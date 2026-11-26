"""Generate Worker resources from the authoritative Python Agent contract."""

import argparse
import json
from pathlib import Path

from exam_baseline.agent.contracts import Context, Decision, Turn
from exam_baseline.agent.prompt import SYSTEM, available_now, schema, turn_text

ROOT = Path(__file__).resolve().parents[1]


def export():
    turn = Turn(
        schemaVersion="astra-intent-v1", clientMessageId="a" * 36,
        workspaceId="b" * 36, message="fixture", context=Context(screen="start", setup=False),
    )
    base = json.loads(turn_text(turn))
    for key in ("context", "message", "availableHints"):
        base.pop(key)
    hints = {}
    for setup in (False, True):
        for status in (None, "draft", "error", "generating", "complete"):
            for approved in (False, True):
                for preview in (None, "failed", "unavailable"):
                    context = Context(screen="workspace", setup=setup, status=status,
                                      approved=approved, preview=preview)
                    hints[json.dumps([setup, status, approved, preview], separators=(",", ":"))] = available_now(context)
    return json.dumps({
        "system": SYSTEM, "base": base, "hints": hints,
        "turnSchema": Turn.model_json_schema(),
        "decisionSchema": Decision.model_json_schema(), "outputSchema": schema(),
    }, ensure_ascii=False, indent=2) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = ROOT / "workers/astra-ai-proxy/src/generated.json"
    content = export()
    if args.check:
        if path.read_text(encoding="utf-8") != content:
            raise SystemExit("Worker contract is stale. Run scripts/export_worker_contract.py.")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
