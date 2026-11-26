"""Closed MAS transport boundary. Academic contracts never become Agent semantics.

Arbitrary academic prompts cannot be authenticated by a caller-supplied stage name.
No public MAS route is enabled until the owner approves an authorization policy and
an independent provider/credential. This adapter deliberately performs no I/O.
"""

from base64 import b64encode
from copy import deepcopy
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

from exam_baseline.config import Settings
from exam_baseline.core.contracts import Completion, CompletionRequest, ProviderError


class MasSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ASTRA_MAS_", env_file=".env", extra="ignore", hide_input_in_errors=True
    )
    transport: Literal["disabled", "worker"] = "disabled"
    # Explicitly closed until the public paid-inference authorization problem is solved.
    forwarding_enabled: Literal[False] = False


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


def configured_worker_mas(settings: Settings) -> dict | None:
    profile = MasSettings()
    if profile.transport != "worker":
        return None
    return {
        role: DisabledWorkerMasProvider(settings, role)
        for role in ("composer", "illustrator", "solver", "reviewer")
    }
