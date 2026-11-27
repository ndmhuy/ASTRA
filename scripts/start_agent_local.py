"""Run local Agent with the operator's existing Gemini credential and demo MAS."""

import logging
import os
from pathlib import Path

import uvicorn
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
legacy = ROOT.parent.parent / "ASTRA-agent-ui-first" / "agent-service" / ".env.local"
values = dotenv_values(legacy) if legacy.is_file() else {}
key = os.environ.get("ASTRA_AGENT_API_KEY") or values.get("GEMINI_API_KEY")
model = os.environ.get("ASTRA_AGENT_MODEL") or values.get("GEMINI_MODEL")
if not key or not model:
    raise SystemExit("Gemini credential or model missing from the local Agent configuration.")
os.environ.update(
    EXAM_DEMO_MODE="1",
    EXAM_PROVIDER="mock",
    EXAM_MODEL="mock-fixture-v1",
    ASTRA_AGENT_ENABLED="true",
    ASTRA_AGENT_TRANSPORT="direct",
    ASTRA_AGENT_API_KEY=key,
    ASTRA_AGENT_MODEL=model,
)
os.environ.setdefault("ASTRA_AGENT_DAILY_ATTEMPTS", "30")
os.environ.setdefault("ASTRA_AGENT_PRIMARY_SECONDS", "3.5")
os.environ.setdefault("ASTRA_AGENT_TOTAL_SECONDS", "4.5")
logging.getLogger("exam_baseline.agent.provider").setLevel(logging.INFO)
os.chdir(ROOT)
uvicorn.run("exam_baseline.api.app:create_web_app", factory=True, host="127.0.0.1", port=8000)
