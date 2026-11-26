"""Generate Worker resources from the authoritative Python Agent contract."""

import argparse
import json
from hashlib import sha256
from pathlib import Path

from exam_baseline.agent.contracts import INTENTS, Context, Decision, Turn, arg_schema
from exam_baseline.agent.prompt import SYSTEM, available_now, schema, turn_text

ROOT = Path(__file__).resolve().parents[1]


def provider_schema():
    """One common argument object, followed by strict per-intent validation."""
    full = schema()
    arguments = {}
    for definition in INTENTS.values():
        for name, rule in definition["args"].items():
            candidate = arg_schema(rule)
            previous = arguments.get(name)
            if previous is None:
                arguments[name] = candidate
            elif previous.get("enum") and not candidate.get("enum"):
                arguments[name] = candidate
            elif previous.get("enum") and candidate.get("enum"):
                previous["enum"] = sorted(set(previous["enum"]) | set(candidate["enum"]))
    full["properties"]["intents"]["items"] = {
        "type": "object",
        "properties": {
            "id": {"type": "string", "enum": list(INTENTS)},
            "args": {"type": "object", "properties": arguments, "additionalProperties": False},
        },
        "required": ["id", "args"],
        "additionalProperties": False,
    }
    full["required"] = ["kind"]
    for name in ("guidance", "title", "intake"):
        full["properties"][name] = {"anyOf": [full["properties"][name], {"type": "null"}]}
    return full


def export():
    turn = Turn(
        schemaVersion="astra-intent-v1",
        clientMessageId="a" * 36,
        workspaceId="b" * 36,
        message="fixture",
        context=Context(screen="start", setup=False),
    )
    base = json.loads(turn_text(turn))
    for key in ("context", "message", "availableHints"):
        base.pop(key)
    base["intentArguments"] = {name: definition["args"] for name, definition in INTENTS.items()}
    hints = {}
    for setup in (False, True):
        for status in (None, "draft", "error", "generating", "complete"):
            for approved in (False, True):
                for preview in (None, "failed", "unavailable"):
                    context = Context(
                        screen="workspace",
                        setup=setup,
                        status=status,
                        approved=approved,
                        preview=preview,
                    )
                    hints[json.dumps([setup, status, approved, preview], separators=(",", ":"))] = (
                        available_now(context)
                    )
    return (
        json.dumps(
            {
                "system": SYSTEM,
                "base": base,
                "hints": hints,
                "turnSchema": Turn.model_json_schema(),
                "decisionSchema": Decision.model_json_schema(),
                "outputSchema": schema(),
                "providerSchema": provider_schema(),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = ROOT / "workers/astra-ai-proxy/src/generated.json"
    content = export()
    fingerprint = sha256(content.encode()).hexdigest()
    resources = json.loads(content)
    resources["contractHash"] = fingerprint
    outputs = {
        path: json.dumps(resources, ensure_ascii=False, indent=2) + "\n",
        ROOT / "src/exam_baseline/resources/agent/worker-contract.json": json.dumps(
            {"contractHash": fingerprint}
        )
        + "\n",
    }
    for target, text in outputs.items():
        if args.check:
            if target.read_text(encoding="utf-8") != text:
                raise SystemExit("Worker contract is stale. Run scripts/export_worker_contract.py.")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
