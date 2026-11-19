from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

_ALLOWED_ENV_KEYS = {
    "AGENT_ALLOWED_ORIGINS",
    "AGENT_HOST",
    "AGENT_MODE",
    "AGENT_PORT",
    "GEMINI_API_KEY",
    "GEMINI_MODEL",
}


def _load_local_env(path: Path) -> None:
    """Load only the service's documented keys without logging their values."""
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key in _ALLOWED_ENV_KEYS and key not in os.environ:
            os.environ[key] = value.strip().strip('"').strip("'")


@dataclass(frozen=True)
class AgentSettings:
    host: str
    port: int
    allowed_origins: tuple[str, ...]
    mode: Literal["offline", "gemini"]
    gemini_model: str
    gemini_api_key: str | None
    max_body_bytes: int = 64 * 1024
    max_concurrent_turns: int = 4
    session_ttl_seconds: int = 8 * 60 * 60

    @property
    def llm_enabled(self) -> bool:
        return self.mode == "gemini"

    @classmethod
    def from_environment(cls, env_file: Path | None = None) -> AgentSettings:
        _load_local_env(env_file or Path("agent-service/.env.local"))
        origins = tuple(
            item.strip()
            for item in os.getenv(
                "AGENT_ALLOWED_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173"
            ).split(",")
            if item.strip()
        )
        host = os.getenv("AGENT_HOST", "127.0.0.1").strip()
        if host not in {"127.0.0.1", "localhost"}:
            raise ValueError("Agent service must bind to loopback in local mode")
        mode = os.getenv("AGENT_MODE", "offline").strip().lower()
        if mode not in {"offline", "gemini"}:
            raise ValueError("AGENT_MODE must be either offline or gemini")
        return cls(
            host=host,
            port=int(os.getenv("AGENT_PORT", "8010")),
            allowed_origins=origins,
            mode=mode,
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite").strip(),
            gemini_api_key=os.getenv("GEMINI_API_KEY") or None,
        )
