"""Generate synchronized V3 native/Worker resources, leaving V1 hashes untouched."""

import argparse
import json
from hashlib import sha256
from pathlib import Path

from exam_baseline.agent.native import gemini_request
from exam_baseline.agent.v3 import REGISTRY, SYSTEM, TurnV3, semantic_schema

ROOT = Path(__file__).resolve().parents[1]


def export():
    result = {
        "catalog": REGISTRY,
        "system": SYSTEM,
        "turnSchema": TurnV3.model_json_schema(),
        "canonicalSchema": semantic_schema(),
        "providerSchema": semantic_schema(compact=True),
    }
    result["contractHash"] = sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    resources = export()
    for path, value in {
        ROOT / "workers/astra-ai-proxy/src/semantic-v3.generated.json": resources,
        ROOT / "src/exam_baseline/resources/agent/semantic-v3-contract.json": {
            "schemaVersion": REGISTRY["schemaVersion"],
            "contractHash": resources["contractHash"],
        },
        ROOT / "eval/agent-v3/native-wire.fixture.json": {
            "provenance": "Generated native builder fixture, no provider call.",
            "request": gemini_request(
                TurnV3(
                    schemaVersion="astra-intent-v1",
                    workspaceId="b" * 36,
                    clientMessageId="a" * 36,
                    message="Natural fixture",
                    context={"screen": "start", "setup": False},
                ),
                512,
            ),
        },
    }.items():
        content = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
        if args.check:
            if not path.is_file() or path.read_text("utf-8") != content:
                raise SystemExit("Stale V3 contract: run scripts/export_agent_v3.py")
        else:
            path.write_text(content, encoding="utf-8")
