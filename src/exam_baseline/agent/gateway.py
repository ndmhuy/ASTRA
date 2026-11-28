"""Google AI Studio structured interpretation through authenticated BYOK only."""

import json
import logging
import re
import sqlite3
from contextlib import asynccontextmanager, closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import httpx
from pydantic import Field, SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from exam_baseline.providers.chat_completions import _retry_after_seconds
from exam_baseline.providers.gateway import Gateway

from .contracts import Decision, Turn
from .prompt import SYSTEM, schema, turn_text
from .provider import ProviderFailure, ProviderRouter, Timing
from .v3 import Interpretation

logger = logging.getLogger(__name__)


class AgentSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="ASTRA_AGENT_", extra="ignore", hide_input_in_errors=True
    )
    enabled: bool = False
    transport: Literal["gateway", "direct", "codex", "offline", "worker"] = "worker"
    semantic_contract: bool = True
    semantic_version: Literal["astra-semantic-v1", "astra-semantic-v3"] = "astra-semantic-v1"
    worker_url: str = "https://astra-ai-proxy.letranhoanglong2227.workers.dev"
    worker_caller_token: SecretStr | None = None
    api_key: SecretStr | None = None
    gateway_account_id: str = ""
    gateway_id: str = ""
    gateway_token: SecretStr | None = None
    gateway_byok_alias: str = "default"
    model: str = ""
    fallback_model: str = ""
    fallback_enabled: bool = False
    daily_attempts: int = Field(default=0, ge=0, le=20_000)
    budget_path: Path = Path("runs/agent-budget.sqlite3")
    primary_seconds: float = Field(default=1.8, ge=0.2, le=30)
    total_seconds: float = Field(default=4.0, ge=0.5, le=30)
    max_output_tokens: int = Field(default=512, ge=128, le=1024)


class DailyBudget:
    """Count attempts, including failed calls and allowed fallback, by UTC day."""

    def __init__(self, path: Path, limit: int):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.limit = limit
        with closing(sqlite3.connect(path)) as db, db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS agent_attempts "
                "(day TEXT PRIMARY KEY, count INTEGER NOT NULL)"
            )

    def reserve(self) -> bool:
        if not self.limit:
            return False
        today = datetime.now(timezone.utc).date().isoformat()
        try:
            with closing(sqlite3.connect(self.path, timeout=0.1)) as db, db:
                consumed = db.execute(
                    "INSERT INTO agent_attempts(day, count) VALUES (?, 1) "
                    "ON CONFLICT(day) DO UPDATE SET count=count+1 WHERE count < ?",
                    (today, self.limit),
                )
                return consumed.rowcount == 1
        except sqlite3.Error:
            logger.warning("agent_budget_storage_unavailable")
            return False


class GeminiGatewayProvider:
    def __init__(
        self,
        client: httpx.AsyncClient,
        gateway: Gateway,
        model: str,
        output_tokens: int,
        *,
        semantic: bool = False,
    ):
        if not re.fullmatch(r"gemini-[A-Za-z0-9][A-Za-z0-9._-]{0,90}", model):
            raise ValueError("invalid configured Gemini model")
        self.client = client
        self.headers = gateway.headers()
        self.model_name = model
        self.headers["cf-aig-max-attempts"] = "1"
        self.url = f"{gateway.base('google-ai-studio')}/v1/models/{model}:generateContent"
        self.output_tokens = output_tokens
        self.semantic = semantic
        self.semantic_version = "astra-semantic-v3" if semantic else "astra-semantic-v1"

    async def interpret(self, turn: Turn, timeout: float) -> Interpretation:
        from .native import gemini_request, parse_native

        native = (
            gemini_request(
                turn,
                self.output_tokens,
                minimal_thinking=self.model_name == "gemini-3.1-flash-lite",
            )
            if self.semantic
            else None
        )
        try:
            response = await self.client.post(
                self.url,
                headers=self.headers,
                json=native
                or {
                    "systemInstruction": {"parts": [{"text": SYSTEM}]},
                    "contents": [{"role": "user", "parts": [{"text": turn_text(turn)}]}],
                    "generationConfig": {
                        "responseMimeType": "application/json",
                        "responseJsonSchema": schema(),
                        "maxOutputTokens": self.output_tokens,
                    },
                },
                timeout=timeout,
                follow_redirects=False,
            )
        except httpx.TimeoutException:
            raise ProviderFailure("timeout") from None
        except httpx.TransportError:
            raise ProviderFailure("transient") from None
        status = response.status_code
        if "cf-aig-authorization" in self.headers:
            logger.info("agent_gateway_http model=%s status=%d", self.model_name, status)
        if status == 429:
            raise ProviderFailure(
                "quota", _retry_after_seconds(response.headers.get("retry-after"))
            )
        if status in {408, 504}:
            raise ProviderFailure("timeout")
        if status >= 500:
            raise ProviderFailure("transient")
        if status != 200:
            code = {401: "auth", 403: "auth", 404: "model", 400: "rejected"}.get(
                status, "configuration"
            )
            logger.warning("agent_upstream_status status=%s category=%s", status, code)
            raise ProviderFailure(code)
        try:
            if self.semantic:
                from .v3 import TurnV3

                return parse_native("gemini", response.json(), v3=isinstance(turn, TurnV3))
            candidates = response.json()["candidates"]
            if len(candidates) != 1 or candidates[0]["finishReason"] != "STOP":
                raise ValueError("incomplete provider output")
            parts = candidates[0]["content"]["parts"]
            text = "".join(part["text"] for part in parts if not part.get("thought"))
            parsed = json.loads(text)
            if not isinstance(parsed, dict) or not {"kind", "intents"} <= parsed.keys():
                raise ValueError("unknown response fields")
            return Decision.model_validate(parsed)
        except (KeyError, TypeError, ValueError, AttributeError):
            raise ProviderFailure("schema") from None


class DirectGeminiProvider(GeminiGatewayProvider):
    """Direct Gemini transport for a local operator-controlled development session."""

    def __init__(self, client, key: SecretStr, model: str, output_tokens: int, *, semantic=False):
        if not re.fullmatch(r"gemini-[A-Za-z0-9][A-Za-z0-9._-]{0,90}", model):
            raise ValueError("invalid configured Gemini model")
        if not key.get_secret_value().strip():
            raise ValueError("missing Gemini key")
        self.client = client
        self.model_name = model
        self.semantic = semantic
        self.headers = {"x-goog-api-key": key.get_secret_value()}
        self.url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        )
        self.output_tokens = output_tokens


async def configuration_failure(_turn: Turn) -> Decision:
    return Decision(kind="temporarily_unavailable", reasonCode="configuration")


@asynccontextmanager
async def configured_interpreter(settings: AgentSettings | None = None):
    try:
        settings = settings or AgentSettings()
    except ValidationError:
        logger.warning("agent_gateway_settings_invalid")
        yield configuration_failure
        return
    if not settings.enabled or settings.transport == "offline":
        yield None
        return
    async with httpx.AsyncClient(follow_redirects=False, trust_env=False) as client:
        try:
            if settings.transport == "worker":
                from exam_baseline.worker_profile import resolve_profile

                from .worker import WorkerInterpretationProvider

                caller = settings.worker_caller_token
                caller_profile = resolve_profile(".env.agent-worker")
                if caller is None and caller_profile.is_file():
                    caller = AgentSettings(_env_file=caller_profile).worker_caller_token
                logger.info("agent_worker_access configured=%s", caller is not None)
                yield ProviderRouter(
                    WorkerInterpretationProvider(
                        client,
                        settings.worker_url,
                        semantic=settings.semantic_contract,
                        semantic_version=settings.semantic_version,
                        caller_token=caller.get_secret_value() if caller else None,
                    ),
                    reserve=lambda: True,
                    timing=Timing(primary=33, total=33),
                )
                return
            if settings.transport == "codex":
                from .codex_cli import CodexCliInterpretationProvider

                primary = CodexCliInterpretationProvider()
                budget = DailyBudget(settings.budget_path, settings.daily_attempts)
                yield ProviderRouter(
                    primary,
                    reserve=budget.reserve,
                    timing=Timing(primary=settings.primary_seconds, total=settings.total_seconds),
                )
                return
            if settings.transport == "direct":
                if not settings.api_key:
                    raise ValueError("missing Gemini key")

                def make_provider(model):
                    return DirectGeminiProvider(
                        client,
                        settings.api_key,
                        model,
                        settings.max_output_tokens,
                        semantic=settings.semantic_contract,
                    )
            else:
                required = ("gateway_account_id", "gateway_id", "gateway_token", "model")
                missing = [name for name in required if not getattr(settings, name)]
                if missing:
                    logger.warning("agent_gateway_missing fields=%s", ",".join(missing))
                    raise ValueError("incomplete gateway configuration")
                gateway = Gateway(
                    settings.gateway_account_id,
                    settings.gateway_id,
                    settings.gateway_token,
                    settings.gateway_byok_alias,
                )

                def make_provider(model):
                    return GeminiGatewayProvider(
                        client,
                        gateway,
                        model,
                        settings.max_output_tokens,
                        semantic=settings.semantic_contract,
                    )

            primary = make_provider(settings.model)
            fallback = None
            if settings.fallback_enabled:
                if settings.fallback_model == settings.model:
                    raise ValueError("configure a separate fallback model")
                fallback = make_provider(settings.fallback_model)
            budget = DailyBudget(settings.budget_path, settings.daily_attempts)
            timing = Timing(primary=settings.primary_seconds, total=settings.total_seconds)
        except (ValueError, OSError, sqlite3.Error):
            logger.warning("agent_gateway_configuration_unavailable")
            yield configuration_failure
            return
        yield ProviderRouter(primary, fallback=fallback, timing=timing, reserve=budget.reserve)
