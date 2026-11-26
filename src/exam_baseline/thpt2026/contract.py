"""Contract-driven THPT 2026 profiles (Literature, English, History, Geography, Chem, Biology)."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from hashlib import sha256
from importlib.resources import files

_SECTION_DEFAULT_TITLES = {
    "mcq": "PHẦN I. Trắc nghiệm nhiều lựa chọn",
    "true_false": "PHẦN II. Trắc nghiệm đúng/sai",
    "short_answer": "PHẦN III. Trả lời ngắn",
    "written": "Tự luận",
}

_SECTION_INSTRUCTIONS_VI = {
    "mcq": "Chọn một phương án đúng A, B, C hoặc D.",
    "true_false": "Trong mỗi ý a), b), c), d) ở mỗi câu, chọn đúng hoặc sai.",
    "short_answer": "Tính toán hoặc xác định đáp án ngắn theo yêu cầu từng câu.",
    "written": "Viết bài trả lời tự luận theo hướng dẫn và thang điểm quy định.",
}


@lru_cache(maxsize=1)
def load_contract() -> dict:
    """Load the bundled ASTRA_THPT_2026_Contract.json once per process."""
    text = (
        files("exam_baseline.resources")
        .joinpath("contracts/ASTRA_THPT_2026_Contract.json")
        .read_text(encoding="utf-8")
    )
    return json.loads(text)


CONTRACT_FORMAT_IDS: tuple[str, ...] = tuple(load_contract()["properties"]["formatId"]["enum"])


def profile_by_format_id(format_id: str) -> dict | None:
    """Return the enriched profile dict from x-profiles for a 2026 contract formatId."""
    profiles = load_contract().get("x-profiles", {})
    for subject_key, profile in profiles.items():
        if profile.get("formatId") == format_id:
            return {**profile, "subjectKey": subject_key}
    return None


def catalog_entries() -> list[dict]:
    """Build GET /api/exam-formats entries from x-profiles in ASTRA_THPT_2026_Contract.json."""
    profiles = load_contract().get("x-profiles", {})
    entries = []
    for profile in profiles.values():
        lang = profile.get("language", "vi")
        sections = []
        for sec in profile["sections"]:
            sec_type = sec["type"]
            instructions = _SECTION_INSTRUCTIONS_VI[sec_type]
            if lang == "en" and sec_type == "mcq":
                instructions = "Choose one correct option A, B, C, or D."
            entry: dict = {
                "id": sec["id"],
                "title": sec.get("title") or _SECTION_DEFAULT_TITLES.get(sec_type, sec["id"]),
                "type": sec_type,
                "count": sec["count"],
                "instructions": instructions,
            }
            if sec.get("pointsPerQuestion") is not None:
                entry["pointsPerQuestion"] = sec["pointsPerQuestion"]
            elif sec.get("pointsPerItem") is not None:
                entry["pointsPerQuestion"] = sec["pointsPerItem"]
            if sec.get("pointsByItem") is not None:
                entry["pointsByItem"] = sec["pointsByItem"]
            if sec.get("pointsByCorrectStatements") is not None:
                entry["scoreByCorrectStatements"] = sec["pointsByCorrectStatements"]
            if sec.get("sectionPoints") is not None:
                entry["sectionPoints"] = sec["sectionPoints"]
            sections.append(entry)

        entries.append(
            {
                "schemaVersion": "exam-format-v1",
                "id": profile["formatId"],
                "version": str(profile.get("formatVersion", "1")),
                "displayName": f"{profile['displayName']} THPT 2026",
                "examType": "THPT_STANDARD",
                "engine": "thpt_contract_2026_v1",
                "subjects": [profile["displayName"]],
                "grades": [12],
                "durationMinutes": profile["durationMinutes"],
                "totalQuestions": profile["totalQuestions"],
                "totalScore": 10,
                "sections": sections,
                "lockedFields": [
                    "subject",
                    "grade",
                    "durationMinutes",
                    "itemCount",
                    "sections",
                    "template",
                ],
                "editableFields": ["prompt"],
                "exportFormats": ["tex", "json", "pdf"],
                "preview": {
                    "format": "pdf",
                    "requires": "local_latex_compiler",
                    "revisionBound": True,
                },
                "available": True,
                "requires": ["chat_completions_provider"],
            }
        )
    return entries


def expected_question_ids(profile: dict) -> list[str]:
    """Return canonical question IDs ordered section by section."""
    return [f"{sec['id']}-{i}" for sec in profile["sections"] for i in range(1, sec["count"] + 1)]


def question_type_map(profile: dict) -> dict[str, tuple[dict, int]]:
    """Map canonical question ID -> (section_dict, 0-based index within section)."""
    mapping: dict[str, tuple[dict, int]] = {}
    for sec in profile["sections"]:
        for idx in range(sec["count"]):
            qid = f"{sec['id']}-{idx + 1}"
            mapping[qid] = (sec, idx)
    return mapping


def _safe_contract_id(raw: str, prefix: str = "id") -> str:
    normalized = re.sub(r"[^a-z0-9_-]", "-", raw.lower()).strip("-")
    if not normalized or not normalized[0].isalpha():
        normalized = f"{prefix}_{normalized}" if normalized else prefix
    return normalized[:64]


def validate_contract_exam(
    profile: dict,
    questions: list[dict],
    passages: list[dict] | None = None,
) -> list[str]:
    """Validate structure, counts, item fields, and passage bindings against a contract profile."""
    errors: list[str] = []
    passages_list = list(passages or [])
    passage_ids = [p.get("id") for p in passages_list]
    if len(passage_ids) != len(set(passage_ids)):
        errors.append("duplicate_passage_ids")
    passage_map = {str(p.get("id")): p for p in passages_list if p.get("id")}

    expected_ids = expected_question_ids(profile)
    actual_ids = [str(q.get("id", "")) for q in questions]
    if actual_ids != expected_ids:
        errors.append(
            f"question_ids_mismatch: expected {len(expected_ids)} items starting with "
            f"{expected_ids[:2]}, got {len(actual_ids)}"
        )
        return errors

    spec_map = question_type_map(profile)
    for question in questions:
        qid = question["id"]
        sec, idx_in_sec = spec_map[qid]
        q_type = question.get("type", sec["type"])
        if q_type != sec["type"]:
            errors.append(f"{qid}: expected type {sec['type']}, got {q_type}")
            continue

        passage_id = question.get("passage_id")
        if passage_id and passage_id not in passage_map:
            errors.append(f"{qid}: missing passage_id '{passage_id}'")

        stem = str(question.get("stem") or "").strip()
        if q_type == "mcq":
            if not stem and not passage_id:
                errors.append(f"{qid}: empty stem requires shared passage_id")
            choices = question.get("choices") or {}
            if set(choices) != {"A", "B", "C", "D"}:
                errors.append(f"{qid}: choices must contain A, B, C, D")
            else:
                values = [str(choices[k]).strip() for k in "ABCD"]
                if any(not val for val in values) or len(set(values)) != 4:
                    errors.append(f"{qid}: choices must be 4 non-empty distinct options")
            if question.get("answer") not in {"A", "B", "C", "D"}:
                errors.append(f"{qid}: invalid mcq answer")
        elif q_type == "true_false":
            if not stem:
                errors.append(f"{qid}: missing true_false stem")
            statements = question.get("statements") or []
            if len(statements) != 4:
                errors.append(f"{qid}: true_false requires exactly 4 statements")
            else:
                for pos, stmt in enumerate(statements):
                    if not str(stmt.get("text") or "").strip():
                        errors.append(f"{qid}.{pos}: empty statement text")
                    if not isinstance(stmt.get("answer"), bool):
                        errors.append(f"{qid}.{pos}: statement answer must be bool")
                    if (
                        not str(stmt.get("solution") or "").strip()
                        and not str(question.get("solution") or "").strip()
                    ):
                        errors.append(f"{qid}.{pos}: missing statement solution")
        elif q_type == "short_answer":
            if not stem:
                errors.append(f"{qid}: missing short_answer stem")
            ans = str(question.get("answer") or "").strip()
            if not ans:
                errors.append(f"{qid}: empty short_answer")
        elif q_type == "written":
            if not stem:
                errors.append(f"{qid}: missing written stem")
            tasks = sec.get("tasks") or []
            expected_task = tasks[idx_in_sec] if idx_in_sec < len(tasks) else None
            if expected_task and question.get("task", expected_task) != expected_task:
                errors.append(f"{qid}: expected task {expected_task}, got {question.get('task')}")
            if not str(question.get("solution") or "").strip():
                errors.append(f"{qid}: missing written rubric/solution")
    return errors


def _rich_text(value: str) -> list[dict]:
    return [{"type": "text", "text": value or " "}]


def _stem_blocks(text: str) -> list[dict]:
    cleaned = (text or "").strip()
    if not cleaned:
        return []
    return [
        {"type": "paragraph", "runs": _rich_text(part.strip())}
        for part in cleaned.split("\n\n")
        if part.strip()
    ]


def build_student_paper(
    job_id: str,
    revision: int,
    profile: dict,
    questions: list[dict],
    passages: list[dict] | None = None,
    *,
    front_matter: list[str] | None = None,
) -> dict:
    """Build an schema-aligned studentPaper payload without any keys or solutions."""
    passage_lookup = {
        str(p.get("id")): _safe_contract_id(str(p.get("id")), "g") for p in (passages or [])
    }
    q_by_id = {q["id"]: q for q in questions}
    sections_payload = []

    for sec in profile["sections"]:
        sec_type = sec["type"]
        items_payload = []
        for idx in range(sec["count"]):
            raw_qid = f"{sec['id']}-{idx + 1}"
            q = q_by_id[raw_qid]
            pid = q.get("passage_id")
            base = {
                "id": _safe_contract_id(raw_qid, "q"),
                "number": idx + 1,
                "stem": _stem_blocks(q.get("stem", "")),
                "passageIds": [passage_lookup[pid]] if pid and pid in passage_lookup else [],
                "sourceIds": ["src_astra_contract"],
                "verificationStatus": "PENDING",
                "type": sec_type,
            }
            if sec_type == "mcq":
                choices = q.get("choices", {})
                base["choices"] = {k: _rich_text(str(choices.get(k, ""))) for k in "ABCD"}
            elif sec_type == "true_false":
                stmts = q.get("statements", [])
                base["statements"] = {
                    letter: _rich_text(str(stmts[i].get("text", "")) if i < len(stmts) else "")
                    for i, letter in enumerate("abcd")
                }
            elif sec_type == "short_answer":
                ans = str(q.get("answer") or "")
                base["responseKind"] = (
                    "digit_sequence" if re.fullmatch(r"[0-9]{1,4}", ans) else "numeric"
                )
            elif sec_type == "written":
                tasks = sec.get("tasks") or []
                base["task"] = q.get("task") or (
                    tasks[idx] if idx < len(tasks) else "reading_response"
                )
                targets = sec.get("wordCountTargets") or []
                wc = q.get("word_count_target") or (targets[idx] if idx < len(targets) else None)
                if wc:
                    base["wordCountTarget"] = int(wc)
            items_payload.append(base)
        section_obj: dict = {"id": sec["id"], "items": items_payload}
        if sec.get("title"):
            section_obj["title"] = sec["title"]
        sections_payload.append(section_obj)

    passages_payload = []
    for p in passages or []:
        raw_pid = str(p["id"])
        q_range = p.get("questionRange") or [1, 1]
        blocks = []
        if str(p.get("heading") or "").strip():
            blocks.append(
                {
                    "type": "paragraph",
                    "runs": [{"type": "text", "text": p["heading"].strip(), "style": "bold"}],
                }
            )
        blocks.extend(_stem_blocks(p.get("text", "")))
        if p.get("table"):
            tbl = p["table"]
            cols = tbl.get("columns", [])
            rows = [
                [{"runs": _rich_text(str(cell))} for cell in row]
                for row in ([cols, *tbl.get("rows", [])] if cols else tbl.get("rows", []))
            ]
            if cols and rows:
                blocks.append(
                    {
                        "type": "table",
                        "columnCount": len(cols),
                        "headerRowCount": 1,
                        "rows": rows,
                    }
                )
        passages_payload.append(
            {
                "id": passage_lookup[raw_pid],
                "sectionId": p.get("section", "P1"),
                "questionRange": [int(q_range[0]), int(q_range[1])],
                "kind": p.get("kind") or "reading",
                "instructions": _rich_text(
                    p.get("instruction") or "Đọc ngữ liệu và trả lời câu hỏi."
                ),
                "blocks": blocks or [{"type": "paragraph", "runs": _rich_text(" ")}],
            }
        )

    paper_without_hash = {
        "schemaVersion": "astra-thpt-paper-v1",
        "examId": _safe_contract_id(f"exam_{job_id}", "exam"),
        "revision": int(revision),
        "examType": "THPT_STANDARD",
        "formatId": profile["formatId"],
        "formatVersion": str(profile.get("formatVersion", "1")),
        "subject": profile["subjectKey"],
        "grade": 12,
        "title": f"Đề luyện tập tốt nghiệp THPT 2026 · Môn {profile['displayName']}",
        "durationMinutes": profile["durationMinutes"],
        "totalScore": 10,
        "sections": sections_payload,
        "passages": passages_payload,
        "assets": [],
        "sources": [
            {
                "id": "src_astra_contract",
                "title": f"Chuẩn cấu trúc THPT 2026 · Môn {profile['displayName']}",
                "locator": f"formatId={profile['formatId']}",
            }
        ],
    }
    if front_matter:
        paper_without_hash["frontMatter"] = [
            {"type": "paragraph", "runs": _rich_text(line)} for line in front_matter if line.strip()
        ]

    canonical = json.dumps(
        paper_without_hash, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    paper_without_hash["contentHash"] = sha256(canonical.encode("utf-8")).hexdigest()
    return paper_without_hash
