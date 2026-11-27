"""Explicit keyless distributed profile; startup makes no inference request."""

import argparse
import os
from pathlib import Path

import uvicorn

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    os.environ.update(
        ASTRA_AGENT_ENABLED="true",
        ASTRA_AGENT_TRANSPORT="worker",
        ASTRA_AGENT_SEMANTIC_CONTRACT="true",
        ASTRA_AGENT_FALLBACK_ENABLED="false",
        EXAM_DEMO_MODE="true",
        EXAM_PROVIDER="mock",
        EXAM_MODEL="mock-fixture-v1",
        ASTRA_MAS_TRANSPORT="disabled",
    )
    os.chdir(ROOT)
    uvicorn.run(
        "exam_baseline.api.app:create_web_app", factory=True, host="127.0.0.1", port=args.port
    )


if __name__ == "__main__":
    main()
