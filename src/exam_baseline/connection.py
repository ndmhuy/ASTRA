"""Local shared-key onboarding. Saving configuration never calls an AI provider."""

import asyncio
import hmac
import io
import json
import os
import re
import secrets
import socket
import ssl
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from dotenv import dotenv_values
from dotenv.parser import parse_stream
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError

from exam_baseline.agent.native import SYSTEM, semantic_context
from exam_baseline.agent.provider import ProviderFailure, ProviderRouter, Timing
from exam_baseline.agent.routes import is_loopback
from exam_baseline.agent.semantics import normalize_frame, semantic_schema
from exam_baseline.agent.v3 import SYSTEM as V3_SYSTEM
from exam_baseline.agent.v3 import TurnV3
from exam_baseline.agent.v3 import normalize_frame as normalize_v3
from exam_baseline.agent.v3 import semantic_schema as schema_v3
from exam_baseline.config import Settings
from exam_baseline.core.contracts import CompletionRequest, ProviderError
from exam_baseline.providers.chat_completions import ChatCompletionsProvider

PROFILE = json.loads((Path(__file__).parent / "resources/connection.json").read_text("utf-8"))
DEFAULT_MODEL = PROFILE["defaultModel"]
DEFAULT_URL = PROFILE["defaultBaseUrl"]
KEY_NAME = PROFILE["keyName"]
LEGACY_KEY_NAME = "ASTRA_GEMINI_API_KEY"
MANAGED = ("EXAM_PROVIDER", "EXAM_MODEL", KEY_NAME, "EXAM_BASE_URL")


class ConnectionInput(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    apiKey: SecretStr | None = None
    model: str = Field(min_length=1, max_length=200)
    baseUrl: str = Field(min_length=1, max_length=2048)


def validate_public(model: str, base_url: str) -> tuple[str, str]:
    model, base_url = model.strip(), base_url.strip().rstrip("/")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_./:@-]{0,199}", model):
        raise ValueError("model")
    url = urlsplit(base_url)
    if (
        any(character.isspace() or ord(character) < 32 for character in base_url)
        or (url.port is not None and not 1 <= url.port <= 65535)
        or not url.hostname
        or url.username
        or url.password
        or url.query
        or url.fragment
        or url.scheme not in {"https", "http"}
        or (url.scheme == "http" and not is_loopback(url.hostname))
        or url.hostname in {"gateway.ai.cloudflare.com", "api.cloudflare.com"}
        or url.hostname.endswith(".workers.dev")
    ):
        raise ValueError("baseUrl")
    # The form accepts a base URL; tolerate a pasted full compatible endpoint.
    if base_url.endswith("/chat/completions"):
        base_url = base_url[: -len("/chat/completions")]
    return model, base_url


class SharedConnection:
    def __init__(self, path: Path, *, transport=None):
        self.path = Path(path).absolute()
        self.transport = transport
        self.client = None
        self.lock = asyncio.Lock()
        self.requests = 0
        self.active_calls = 0
        self.token = secrets.token_urlsafe(32)
        self.last_failure = None
        self.verified = False
        self.configuration_error = None
        self.app = None
        try:
            self.values = self._read()
        except (OSError, ValueError):
            self.values = {}
            self.configuration_error = (
                "Chưa đọc được file .env. Hãy kiểm tra quyền ghi thư mục ứng dụng."
            )
        self.settings = self._load()
        self.providers = {
            role: SharedProvider(self, role)
            for role in ("composer", "illustrator", "solver", "reviewer")
        }
        self.baseline = SharedProvider(self, "baseline")
        self.chat_provider = SharedInterpreter(self)
        self.interpreter = self._router()

    def _read(self):
        if self.path.is_symlink():
            raise ValueError("The local .env must be a regular file")
        if not self.path.exists():
            return {}
        return dict(dotenv_values(self.path, encoding="utf-8-sig", interpolate=False))

    def _load(self):
        try:
            model, url = validate_public(
                self.values.get("EXAM_MODEL") or DEFAULT_MODEL,
                self.values.get("EXAM_BASE_URL") or DEFAULT_URL,
            )
            key = self.values.get(KEY_NAME) or self.values.get(LEGACY_KEY_NAME) or ""
            return self.make_settings(model, url, key)
        except (ValueError, ValidationError):
            self.configuration_error = "Cấu hình .env chưa hợp lệ. Hãy nhập lại kết nối AI."
            defaults = {name: field.get_default() for name, field in Settings.model_fields.items()}
            return Settings(
                _env_file=None,
                **{
                    **defaults,
                    "provider": "unconfigured",
                    "model": DEFAULT_MODEL,
                    "base_url": DEFAULT_URL,
                },
            )

    def make_settings(self, model, url, key):
        if key and (
            len(key) > PROFILE["maxKeyCharacters"] or any(ord(c) < 33 or ord(c) > 126 for c in key)
        ):
            raise ValueError("apiKey")
        # Preserve academic settings, overriding only credential/transport selection.
        # An existing Claude-compatible tool wire is reused; no academic schema changes.
        tool = self.values.get("EXAM_SCHEMA_AS_TOOL")
        tool = (tool.lower() == "true") if tool is not None else "claude" in model.lower()
        return Settings(
            _env_file=self.path if self.path.exists() else None,
            provider="chat_completions" if key else "unconfigured",
            model=model,
            base_url=url,
            api_key=SecretStr(key) if key else None,
            use_ai_gateway=False,
            demo_mode=False,
            schema_as_tool=tool,
            response_format="json_schema",
            structured_output_strict=False,
            token_limit_field="max_tokens",
        )

    @property
    def configured(self):
        return self.settings.provider == "chat_completions" and bool(self.settings.api_key)

    def _router(self):
        # No internal request allowance and no fallback to Cloudflare or a second model.
        return ProviderRouter(
            self.chat_provider,
            reserve=lambda: True,
            timing=Timing(
                primary=PROFILE["chatTimeoutSeconds"], total=PROFILE["chatTimeoutSeconds"]
            ),
        )

    def busy(self):
        jobs = getattr(getattr(self.app, "state", None), "ui_jobs", None)
        tasks = [*jobs.tasks.values(), *jobs.question_tasks.values()] if jobs else []
        return bool(self.requests or self.active_calls or any(not task.done() for task in tasks))

    def public(self):
        return {
            "schemaVersion": "astra-local-connection-v1",
            "managed": True,
            "configured": self.configured,
            "hasApiKey": self.configured,
            "model": self.settings.model,
            "baseUrl": self.settings.base_url,
            "setupToken": self.token,
            "file": ".env",
            "shared": True,
            "verified": self.verified,
            "busy": self.busy(),
            "lastFailure": self.last_failure,
            "configurationError": self.configuration_error,
        }

    def _write(self, settings):
        # Preserve unrelated variables/comments; replace all four fields atomically.
        if self.path.is_symlink():
            raise ValueError("env_path")
        text = self.path.read_text("utf-8-sig") if self.path.exists() else ""
        values = {
            "EXAM_PROVIDER": "chat_completions",
            "EXAM_MODEL": settings.model,
            KEY_NAME: settings.api_key.get_secret_value(),
            "EXAM_BASE_URL": settings.base_url,
        }
        remaining = dict(values)
        lines = []
        for binding in parse_stream(io.StringIO(text)):
            if binding.key == LEGACY_KEY_NAME:
                # Migrate the misleading old name on save, without two stale keys.
                continue
            if binding.key in values:
                if binding.key in remaining:
                    lines.append(binding.key + "=" + json.dumps(remaining.pop(binding.key)) + "\n")
            else:
                lines.append(binding.original.string)
        if lines and not lines[-1].endswith("\n"):
            lines.append("\n")
        lines.extend(name + "=" + json.dumps(value) + "\n" for name, value in remaining.items())
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, name = tempfile.mkstemp(prefix=".astra-env-", dir=self.path.parent)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as output:
                output.write("".join(lines))
                output.flush()
                os.fsync(output.fileno())
            os.chmod(name, 0o600)
            os.replace(name, self.path)
        finally:
            if os.path.exists(name):
                os.unlink(name)

    async def save(self, data):
        async with self.lock:
            if self.busy():
                raise HTTPException(409, "connection_busy")
            model, url = validate_public(data.model, data.baseUrl)
            key = data.apiKey.get_secret_value().strip() if data.apiKey else ""
            if not key:
                key = self.settings.api_key.get_secret_value() if self.configured else ""
            if not key:
                raise ValueError("apiKey")
            settings = self.make_settings(model, url, key)
            self._write(settings)
            self.settings = settings
            self.values = self._read()
            self.configuration_error = None
            self.last_failure = None
            self.verified = False
            self.interpreter = self._router()  # Clear an old credential's circuit/cooldown.
            if self.app:
                self.app.state.settings = settings
                self.app.state.ui_jobs.settings = settings
                self.app.state.configured_interpreter = self.interpreter
                from exam_baseline.baseline.bootstrap import build_service

                self.app.state.service = build_service(settings, self.baseline)
            return self.public()

    @asynccontextmanager
    async def lifespan(self, app):
        self.app = app
        async with httpx.AsyncClient(
            transport=self.transport, trust_env=False, follow_redirects=False
        ) as client:
            self.client = client
            yield
        self.client = None

    def record_failure(self, error, role):
        status = error.http_status
        message = {
            "provider_connection_failed": (
                "Không kết nối được tới máy chủ API. "
                "Mở Kết nối AI để kiểm tra API Base URL và kết nối Internet."
            ),
            "provider_connect_timeout": (
                "Hết thời gian kết nối tới máy chủ API. Kiểm tra URL và kết nối Internet."
            ),
        }.get(error.code, "Dịch vụ AI chưa trả lời hợp lệ. Dữ liệu đã lưu vẫn được giữ.")
        cause = error
        for _ in range(8):
            if isinstance(cause, socket.gaierror):
                message = (
                    "Không phân giải được tên miền API. "
                    "Mở Kết nối AI để kiểm tra API Base URL hoặc DNS của mạng."
                )
                break
            if isinstance(cause, ssl.SSLError):
                message = (
                    "Không xác minh được kết nối HTTPS tới máy chủ API. "
                    "Kiểm tra địa chỉ, chứng chỉ và cấu hình mạng."
                )
                break
            cause = cause.__cause__ or cause.__context__
            if cause is None:
                break
        descriptions = {
            400: "Dịch vụ từ chối định dạng yêu cầu.",
            401: "API key bị dịch vụ từ chối.",
            403: "API key chưa có quyền dùng model này.",
            404: "Không tìm thấy model hoặc đường dẫn API.",
            429: "Dịch vụ đang giới hạn lượt gọi hoặc quota.",
        }
        field = None
        try:
            raw = error.__cause__.response.json().get("error", {})
            candidate = raw.get("param") if isinstance(raw, dict) else None
            if candidate in {
                "model",
                "response_format",
                "tools",
                "tool_choice",
                "max_tokens",
                "max_completion_tokens",
                "temperature",
                "seed",
                "messages",
            }:
                field = candidate
        except (AttributeError, TypeError, ValueError):
            pass
        self.last_failure = {
            "code": error.code,
            "status": status,
            "role": role,
            "field": field,
            "message": descriptions.get(status, message),
        }


class SharedProvider:
    def __init__(self, owner, role):
        self.owner, self.role = owner, role

    @property
    def name(self):
        return "chat_completions" if self.owner.configured else "unconfigured"

    @property
    def model(self):
        return self.owner.settings.model

    @property
    def parameters(self):
        return {
            "transport": "shared_local_api",
            "max_tokens": self.owner.settings.max_output_tokens,
            "schema_as_tool": self.owner.settings.schema_as_tool,
        }

    async def complete(self, request, *, chat=False, timeout=None):
        if not self.owner.configured:
            raise ProviderError("provider_not_configured", "Enter the shared API key in ASTRA.")
        settings = self.owner.settings
        if chat:
            settings = settings.model_copy(
                update={
                    "max_output_tokens": PROFILE["chatOutputTokens"],
                    "timeout_seconds": timeout or PROFILE["chatTimeoutSeconds"],
                    "spend_limit_usd": None,
                }
            )
        self.owner.active_calls += 1
        try:
            result = await ChatCompletionsProvider(
                settings.for_agent_generation(), self.owner.client
            ).complete(request)
            self.owner.verified = True
            self.owner.last_failure = None
            return result
        except ProviderError as error:
            self.owner.record_failure(error, self.role)
            raise
        finally:
            self.owner.active_calls -= 1


class SharedInterpreter:
    semantic_version = "astra-semantic-v3"

    def __init__(self, owner):
        self.provider = SharedProvider(owner, "chat")

    async def interpret(self, turn, timeout):
        v3 = isinstance(turn, TurnV3)
        try:
            completion = await self.provider.complete(
                CompletionRequest(
                    V3_SYSTEM if v3 else SYSTEM,
                    json.dumps(semantic_context(turn), ensure_ascii=False, separators=(",", ":")),
                    schema_v3(compact=True) if v3 else semantic_schema(compact=True),
                ),
                chat=True,
                timeout=timeout,
            )
            return (normalize_v3 if v3 else normalize_frame)(json.loads(completion.text))
        except ProviderError as error:
            reason = {400: "rejected", 401: "auth", 403: "auth", 404: "model", 429: "quota"}.get(
                error.http_status,
                "configuration"
                if error.code == "provider_not_configured"
                else "timeout"
                if "timeout" in error.code
                else "transient",
            )
            raise ProviderFailure(reason) from None
        except (ValueError, TypeError):
            raise ProviderFailure("schema") from None


def requires_ai(method, path):
    return method == "POST" and (
        path == "/agent/turn"
        or path.endswith("/exams/generate")
        or (
            path.startswith("/api/exams/")
            and path.rsplit("/", 1)[-1] in {"resume", "retry", "verify", "regenerate"}
        )
    )


def install_connection(app, manager):
    router = APIRouter(prefix="/api/connection")

    def boundary(request):
        peer = request.client.host if request.client else ""
        if not is_loopback(peer) or not is_loopback(request.url.hostname):
            raise HTTPException(403, "local_configuration_only")
        if request.headers.get("sec-fetch-site") not in (None, "same-origin"):
            raise HTTPException(403, "local_configuration_only")
        origin = request.headers.get("origin")
        if origin and origin.rstrip("/") != str(request.base_url).rstrip("/"):
            raise HTTPException(403, "local_configuration_only")

    @router.get("")
    async def status(request: Request):
        boundary(request)
        return JSONResponse(manager.public(), headers={"Cache-Control": "no-store"})

    @router.post("")
    async def save(request: Request):
        boundary(request)
        if not hmac.compare_digest(request.headers.get("X-Astra-Setup", ""), manager.token):
            raise HTTPException(403, "configuration_token_required")
        raw = bytearray()
        async for chunk in request.stream():
            raw.extend(chunk)
            if len(raw) > PROFILE["maxBodyBytes"]:
                raise HTTPException(413, "configuration_body_limit")
        try:
            data = ConnectionInput.model_validate_json(raw)
            return JSONResponse(await manager.save(data), headers={"Cache-Control": "no-store"})
        except (ValueError, ValidationError):
            return JSONResponse(
                {
                    "error": {
                        "code": "invalid_connection",
                        "message": (
                            "Kiểm tra API key, model và URL. "
                            "Chỉ dùng HTTPS hoặc máy chủ local; không đặt key trong URL."
                        ),
                    }
                },
                status_code=422,
            )
        except OSError:
            return JSONResponse(
                {
                    "error": {
                        "code": "configuration_write_failed",
                        "message": "Chưa ghi được file .env. Cấu hình đang dùng vẫn được giữ.",
                    }
                },
                status_code=503,
            )

    app.include_router(router)

    @app.middleware("http")
    async def admit(request, call_next):
        if not requires_ai(request.method, request.url.path):
            return await call_next(request)
        async with manager.lock:
            if not manager.configured:
                return JSONResponse(
                    {
                        "error": {
                            "code": "provider_not_configured",
                            "message": "Mở Kết nối AI để nhập API key dùng chung.",
                        }
                    },
                    status_code=503,
                )
            manager.requests += 1
        try:
            return await call_next(request)
        finally:
            manager.requests -= 1
