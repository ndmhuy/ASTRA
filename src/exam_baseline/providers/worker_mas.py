"""Authenticated MAS transport; retain Backend Chat Completions wire and parser."""

from base64 import b64encode
from copy import deepcopy
from typing import Literal
from urllib.parse import urlsplit

import httpx
from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from exam_baseline.config import Settings
from exam_baseline.core.contracts import Completion, CompletionRequest, ProviderError
from exam_baseline.providers.chat_completions import ChatCompletionsProvider


class MasSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ASTRA_MAS_", env_file=".env", extra="ignore", hide_input_in_errors=True
    )
    transport: Literal["disabled", "worker"] = "disabled"
    forwarding_enabled: bool = False
    worker_url: str = "https://astra-mas-proxy.letranhoanglong2227.workers.dev"
    caller_token: SecretStr | None = None

    @model_validator(mode="after")
    def validate_access(self):
        url = urlsplit(self.worker_url)
        if (
            url.scheme != "https"
            or not url.hostname
            or url.username
            or url.password
            or url.query
            or url.fragment
            or url.path not in ("", "/")
        ):
            raise ValueError("ASTRA_MAS_WORKER_URL must be an HTTPS origin")
        if self.forwarding_enabled and (
            self.transport != "worker"
            or not self.caller_token
            or len(self.caller_token.get_secret_value()) != 64
            or any(char not in "0123456789abcdef" for char in self.caller_token.get_secret_value())
        ):
            raise ValueError(
                "MAS forwarding requires worker transport and a revocable caller token"
            )
        return self


class WorkerMasProvider(ChatCompletionsProvider):
    name = "worker_mas"

    def __init__(
        self, settings: Settings, client: httpx.AsyncClient, profile: MasSettings, stage: str
    ):
        if stage not in {"composer", "illustrator", "solver", "reviewer"}:
            raise ValueError("unknown_backend_stage")
        if not profile.forwarding_enabled or not profile.caller_token:
            raise ValueError("mas_forwarding_disabled")
        # Neither Gemini credentials nor Gateway tokens enter this transport.
        # Existing payload construction, spend accounting and response parsing are reused.
        super().__init__(
            settings.model_copy(update={"use_ai_gateway": False, "api_key": None}), client
        )
        self.url = profile.worker_url.rstrip("/") + "/v1/chat/completions"
        self.headers = {
            "Authorization": "Bearer " + profile.caller_token.get_secret_value(),
            "X-Astra-MAS-Stage": stage,
        }


class DisabledWorkerMasProvider:
    name = "worker_mas_disabled"

    def __init__(self, settings: Settings, stage: str):
        if stage not in {"composer", "illustrator", "solver", "reviewer"}:
            raise ValueError("unknown_backend_stage")
        self.model = settings.model
        self.stage = stage
        self.parameters = {
            "transport": "worker",
            "forwarding": False,
            "max_output_tokens": settings.max_output_tokens,
            "timeout_seconds": settings.timeout_seconds,
        }

    def prepare(self, request: CompletionRequest) -> dict:
        """Lossless synthetic-test/extension seam; never logs or forwards this content."""
        return {
            "schemaVersion": "astra-mas-transport-v1",
            "workload": "MAS_GENERATION",
            "stage": self.stage,
            "model": self.model,
            "request": {
                "system": request.system,
                "user": request.user,
                "output_schema": deepcopy(request.output_schema),
                "images": [
                    {"mime": image.mime, "base64": b64encode(image.data).decode("ascii")}
                    for image in request.images
                ],
            },
            "limits": dict(self.parameters),
        }

    async def complete(self, request: CompletionRequest) -> Completion:
        raise ProviderError(
            "mas_forwarding_disabled",
            "MAS Worker forwarding awaits an independent credential, compatible academic provider "
            "and owner-approved caller authorization/resource policy.",
        )


def configured_worker_mas(
    settings: Settings, client: httpx.AsyncClient | None = None, profile: MasSettings | None = None
) -> dict | None:
    profile = profile or MasSettings()
    if settings.provider != "worker_mas" and profile.transport != "worker":
        return None
    if profile.forwarding_enabled:
        if client is None:
            raise ValueError("MAS Worker transport requires the Backend HTTP client")
        return {
            role: WorkerMasProvider(settings.for_agent_generation(), client, profile, role)
            for role in ("composer", "illustrator", "solver", "reviewer")
        }
    return {
        role: DisabledWorkerMasProvider(settings, role)
        for role in ("composer", "illustrator", "solver", "reviewer")
    }
