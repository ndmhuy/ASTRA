from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_ALLOWED_ENV_KEYS = {
    "AGENT_ALLOWED_ORIGINS",
    "AGENT_HOST",
    "AGENT_LLM_ENABLED",
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


def _as_bool(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class AgentSettings:
    host: str
    port: int
    allowed_origins: tuple[str, ...]
    llm_enabled: bool
    gemini_model: str
    gemini_api_key: str | None
    max_body_bytes: int = 64 * 1024
    max_concurrent_turns: int = 4
    session_ttl_seconds: int = 8 * 60 * 60

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
        return cls(
            host=host,
            port=int(os.getenv("AGENT_PORT", "8010")),
            allowed_origins=origins,
            llm_enabled=_as_bool(os.getenv("AGENT_LLM_ENABLED", "false")),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip(),
            gemini_api_key=os.getenv("GEMINI_API_KEY") or None,
        )
