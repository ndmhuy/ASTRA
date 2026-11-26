"""Server-side Cloudflare AI Gateway BYOK request binding."""

import re
from dataclasses import dataclass
from typing import Literal

from pydantic import SecretStr


@dataclass(frozen=True)
class Gateway:
    account: str
    identifier: str
    token: SecretStr
    alias: str = "default"

    def __post_init__(self):
        if not re.fullmatch(r"[0-9a-fA-F]{32}", self.account):
            raise ValueError("invalid AI Gateway account")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", self.identifier):
            raise ValueError("invalid AI Gateway identifier")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", self.alias):
            raise ValueError("invalid AI Gateway BYOK alias")
        if not re.fullmatch(r"[A-Za-z0-9._~-]{1,300}", self.token.get_secret_value()):
            raise ValueError("invalid AI Gateway Run token")

    def base(self, provider: Literal["openai", "google-ai-studio"]) -> str:
        if provider not in {"openai", "google-ai-studio"}:
            raise ValueError("unsupported gateway provider")
        return f"https://gateway.ai.cloudflare.com/v1/{self.account}/{self.identifier}/{provider}"

    def headers(self) -> dict[str, str]:
        return {
            "cf-aig-authorization": f"Bearer {self.token.get_secret_value()}",
            "cf-aig-byok-alias": self.alias,
            "cf-aig-no-wholesale": "true",
            "cf-aig-skip-cache": "true",
            "cf-aig-collect-log-payload": "false",
            "cf-aig-collect-log": "false",
        }
