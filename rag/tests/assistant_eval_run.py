"""Run the curriculum questions through the source and score them. Used by the test and by the review package."""
import json
from pathlib import Path

from exam_generator.assistant.sources.curriculum import CurriculumSource

QUESTIONS = Path(__file__).with_name("curriculum.json")


def judge(expect: dict, got) -> tuple[bool, str]:
    ids = [p.id for p in got.passages]
    if "gap" in expect:
        ok = got.gap == expect["gap"] and (not expect.get("meta_has") or expect["meta_has"] in got.meta)
        return ok, f"gap={got.gap} ids={ids[:3]}"
    if got.gap:
        return False, f"gap={got.gap}"
    if "top1" in expect:
        return bool(ids) and ids[0] == expect["top1"], f"ids={ids[:3]}"
    if "top3_any" in expect:
        return any(i in ids[:3] for i in expect["top3_any"]), f"ids={ids[:3]}"
    if "ids_all" in expect:
        return all(i in ids for i in expect["ids_all"]), f"ids={ids}"
    return False, "no expectation"


def run(limit: int = 3) -> list[dict]:
    source = CurriculumSource()
    rows = []
    for q in json.loads(QUESTIONS.read_text(encoding="utf-8")):
        got = source.search({"text": q["question"]}, limit=limit)
        ok, detail = judge(q["expect"], got)
        rows.append({**q, "ok": ok, "detail": detail})
    return rows
