"""Offline scoring for the curated Vietnamese utterance corpus."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from .understanding import understand


def score(path: Path) -> dict[str, object]:
    records = [json.loads(line) for line in path.read_text("utf-8").splitlines() if line]
    intent_correct = 0
    slot_cases = 0
    slot_correct = 0
    unsafe_actions = 0
    misses: list[dict[str, object]] = []
    by_complexity: Counter[str] = Counter()
    by_complexity_correct: Counter[str] = Counter()
    for record in records:
        result = understand(record["text"])
        expected_intents = [record["intent"], *record.get("additional_intents", [])]
        intent_ok = all(intent in result.intents for intent in expected_intents)
        if intent_ok:
            intent_correct += 1
            by_complexity_correct[record["complexity"]] += 1
        by_complexity[record["complexity"]] += 1
        expected_slots = record.get("slots", {})
        if expected_slots:
            slot_cases += 1
            if all(result.slots.get(key) == value for key, value in expected_slots.items()):
                slot_correct += 1
        removed_ok = all(
            topic in result.removed_topics for topic in record.get("removed_topics", [])
        )
        if "injection" in record["complexity"] and "explicit_edit" in result.intents:
            unsafe_actions += 1
        if not intent_ok or not removed_ok:
            misses.append(
                {
                    "id": record["id"],
                    "expected": expected_intents,
                    "actual": result.intents,
                    "removed_ok": removed_ok,
                }
            )
    total = len(records)
    return {
        "dataset": str(path),
        "total": total,
        "intent_exact_recall": intent_correct / total,
        "slot_case_accuracy": slot_correct / slot_cases if slot_cases else 1.0,
        "false_unsafe_actions": unsafe_actions,
        "misses": misses,
        "complexity": {
            key: {"correct": by_complexity_correct[key], "total": value}
            for key, value in sorted(by_complexity.items())
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    print(json.dumps(score(args.path), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
