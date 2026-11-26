"""Start the local ASTRA workspace with Codex interpretation and demo MAS."""

import logging
import os
from pathlib import Path

import uvicorn

from exam_baseline.agent.codex_cli import resolve_codex

ROOT = Path(__file__).resolve().parents[1]
resolve_codex()
os.environ.update(
    EXAM_DEMO_MODE="1",
    EXAM_PROVIDER="mock",
    EXAM_MODEL="mock-fixture-v1",
    ASTRA_AGENT_ENABLED="true",
    ASTRA_AGENT_TRANSPORT="codex",
    ASTRA_AGENT_FALLBACK_ENABLED="false",
    ASTRA_AGENT_PRIMARY_SECONDS="30",
    ASTRA_AGENT_TOTAL_SECONDS="30",
)
os.environ.setdefault("ASTRA_AGENT_DAILY_ATTEMPTS", "30")
logging.getLogger("exam_baseline.agent.provider").setLevel(logging.INFO)
os.chdir(ROOT)
uvicorn.run("exam_baseline.api.app:create_web_app", factory=True, host="127.0.0.1", port=8000)
