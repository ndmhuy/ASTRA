"""Live multi-agent composer + blind solver runner for the 6 THPT 2026 contract formats."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from exam_baseline.core.contracts import CompletionRequest
from exam_baseline.pipeline.runtime import normalize_json
from exam_baseline.thpt.runtime import ContractError
from exam_baseline.thpt2026.contract import validate_contract_exam
from exam_baseline.thpt2026.rendering import render_contract_exam_tex

_COMPOSER_SCHEMA = {
    "type": "object",
    "properties": {
        "front_matter": {"type": "array", "items": {"type": "string"}},
        "passages": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "section": {"type": "string"},
                    "kind": {"type": "string"},
                    "questionRange": {"type": "array", "items": {"type": "integer"}},
                    "instruction": {"type": "string"},
                    "heading": {"type": "string"},
                    "text": {"type": "string"},
                    "source": {"type": "string"},
                },
                "required": ["id", "section", "questionRange", "text"],
            },
        },
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "type": {"type": "string"},
                    "passage_id": {"type": ["string", "null"]},
                    "stem": {"type": "string"},
                    "choices": {"type": "object"},
                    "statements": {"type": "array"},
                    "answer": {"type": ["string", "null"]},
                    "task": {"type": ["string", "null"]},
                    "word_count_target": {"type": ["integer", "null"]},
                    "points": {"type": ["number", "null"]},
                    "solution": {"type": "string"},
                },
                "required": ["id", "type", "stem", "solution"],
            },
        },
    },
    "required": ["questions"],
}

_SOLVER_SCHEMA = {
    "type": "object",
    "properties": {
        "entries": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question_id": {"type": "string"},
                    "status": {"type": "string", "enum": ["solved", "ambiguous", "unsolvable"]},
                    "answer": {"type": "string"},
                    "reasoning": {"type": "string"},
                },
                "required": ["question_id", "status", "answer"],
            },
        }
    },
    "required": ["entries"],
}


def _contract_error(stage: str, message: str) -> ContractError:
    return ContractError(stage, [{"location": [stage], "type": "contract", "message": message}])


def _parse_json_object(raw_text: str, stage: str) -> dict:
    try:
        normalized, _ = normalize_json(raw_text)
        parsed = json.loads(normalized)
    except (ValueError, json.JSONDecodeError) as exc:
        raise _contract_error(stage, f"Invalid JSON from {stage}: {exc}") from exc
    if not isinstance(parsed, dict):
        raise _contract_error(stage, f"Expected JSON object from {stage}")
    return parsed


def _blind_student_items(questions: list[dict]) -> list[dict]:
    """Strip all keys and private solutions before passing questions to the Blind Solver."""
    items: list[dict] = []
    for q in questions:
        q_type = q.get("type")
        if q_type not in {"mcq", "true_false", "short_answer"}:
            continue
        view: dict = {
            "id": q["id"],
            "type": q_type,
            "stem": q.get("stem", ""),
        }
        if q.get("passage_id"):
            view["passage_id"] = q["passage_id"]
        if q_type == "mcq":
            view["choices"] = dict(q.get("choices") or {})
        elif q_type == "true_false":
            view["statements"] = [{"text": s.get("text", "")} for s in q.get("statements") or []]
        items.append(view)
    return items


async def run_thpt2026_live_job(
    profile: dict,
    providers: dict,
    output: Path,
    on_progress: Callable[[str, str | None, int], None] | None = None,
    *,
    prompt: str = "",
    font_profile: str = "unicode_times",
) -> dict:
    """Compose contract-compliant questions per section via LLM providers and verify via Solver."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    composer = providers["composer"]
    solver = providers["solver"]

    all_questions: list[dict] = []
    all_passages: list[dict] = []
    seen_passage_ids: set[str] = set()
    front_matter: list[str] = []

    ref_groups = profile.get("reference", {}).get("observedGroups")

    for sec in profile["sections"]:
        sec_id = sec["id"]
        if on_progress:
            on_progress("composer", sec_id, 1)
        expected_ids = [f"{sec_id}-{i}" for i in range(1, sec["count"] + 1)]
        sec_payload = {
            "formatId": profile["formatId"],
            "subject": profile["displayName"],
            "language": profile.get("language", "vi"),
            "section": sec,
            "expectedQuestionIds": expected_ids,
            "observedGroups": ref_groups if ref_groups and sec_id == "P1" else None,
            "teacherPrompt": prompt,
        }
        system_prompt = (
            "Return valid JSON matching output_schema without Markdown fences. "
            "Follow Vietnamese MoET 2026 Graduation Exam structure strictly. "
            "Produce all requested question IDs in exact order, keeping stems/options free "
            "from leaked answers, and provide accurate private answers and detailed solutions. "
            "For short_answer items, answers must be at most 4 characters using comma decimals."
        )
        completion = await composer.complete(
            CompletionRequest(
                system=system_prompt,
                user=json.dumps(sec_payload, ensure_ascii=False),
                output_schema=_COMPOSER_SCHEMA,
            )
        )
        parsed = _parse_json_object(completion.text, "composer")
        sec_questions = parsed.get("questions")
        if not isinstance(sec_questions, list):
            raise _contract_error("composer", f"{sec_id}: missing questions list")
        for idx, q in enumerate(sec_questions):
            if not isinstance(q, dict):
                raise _contract_error("composer", f"{sec_id}: question item must be object")
            q.setdefault("type", sec["type"])
            if sec["type"] == "written":
                tasks = sec.get("tasks") or []
                targets = sec.get("wordCountTargets") or []
                pts = sec.get("pointsByItem") or []
                if idx < len(tasks) and not q.get("task"):
                    q["task"] = tasks[idx]
                if idx < len(targets) and q.get("word_count_target") is None:
                    q["word_count_target"] = targets[idx]
                if idx < len(pts) and q.get("points") is None:
                    q["points"] = pts[idx]
            all_questions.append(q)

        for passage in parsed.get("passages") or []:
            if (
                isinstance(passage, dict)
                and passage.get("id")
                and passage["id"] not in seen_passage_ids
            ):
                all_passages.append(passage)
                seen_passage_ids.add(passage["id"])
        for note in parsed.get("front_matter") or []:
            if isinstance(note, str) and note.strip() and note not in front_matter:
                front_matter.append(note.strip())

    errors = validate_contract_exam(profile, all_questions, all_passages)
    if errors:
        raise _contract_error("composer", "; ".join(errors))

    objective_items = _blind_student_items(all_questions)
    solver_entries: list[dict] = []
    if objective_items:
        if on_progress:
            on_progress("solver", None, 1)
        referenced_pids = {q.get("passage_id") for q in objective_items if q.get("passage_id")}
        solver_passages = [
            {
                "id": p["id"],
                "heading": p.get("heading", ""),
                "text": p.get("text", ""),
                "table": p.get("table"),
            }
            for p in all_passages
            if p.get("id") in referenced_pids
        ]
        solver_payload = {
            "subject": profile["displayName"],
            "passages": solver_passages,
            "questions": objective_items,
        }
        solver_completion = await solver.complete(
            CompletionRequest(
                system=(
                    "Independently solve every question from first principles and return valid "
                    "JSON matching output_schema without Markdown fences."
                ),
                user=json.dumps(solver_payload, ensure_ascii=False),
                output_schema=_SOLVER_SCHEMA,
            )
        )
        solved_data = _parse_json_object(solver_completion.text, "solver")
        raw_entries = solved_data.get("entries")
        if not isinstance(raw_entries, list):
            raise _contract_error("solver", "Solver response missing entries list")
        solver_entries = [e for e in raw_entries if isinstance(e, dict) and e.get("question_id")]

    if on_progress:
        on_progress("reviewer", None, 1)

    tex_bytes = render_contract_exam_tex(
        profile,
        all_questions,
        all_passages,
        front_matter=front_matter,
        font_profile=font_profile,
    )
    (output / "de_thi.tex").write_bytes(tex_bytes)
    (output / "dap_an_va_loi_giai.json").write_text(
        json.dumps(
            {
                "composer": all_questions,
                "passages": all_passages,
                "front_matter": front_matter,
                "independent_solver": {"entries": solver_entries},
            },
            ensure_ascii=False,
            indent=2,
        ),
        "utf-8",
    )
    revision_dir = output / "_internal" / "revision_1"
    revision_dir.mkdir(parents=True, exist_ok=True)
    (revision_dir / "illustrations.json").write_text('{"drawings": []}', "utf-8")
    return {"execution_status": "completed", "revision": 1}
