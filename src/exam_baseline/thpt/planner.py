"""RAG-grounded THPT 22-slot blueprint planner from natural-language user prompts."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from exam_baseline.thpt.models import COUNTS, Level, Part, Request, Slot
from exam_baseline.thpt.rag import DEFAULT_CORPUS_REF, RagHandoffError, default_request
from rag_workflow.matrix_retriever import (
    OUT_OF_CURRICULUM_PHRASES,
    _resolve_candidate_topic_packs,
    _score_curriculum_for_slot,
)
from rag_workflow.models import MatrixQuestionSpec
from rag_workflow.profile_pack import load_profile_release
from rag_workflow.query_parser import normalize

# Map Vietnamese user topic phrasing to canonical umbrella keys in rag_workflow/config.json.
_FAMILY_PATTERNS: list[tuple[str, tuple[str, ...], tuple[str, ...]]] = [
    (
        "dao_ham",
        (
            "ung dung dao ham",
            "khao sat ham so",
            "dao ham",
            "cuc tri",
            "don dieu",
            "dong bien",
            "nghich bien",
            "tiem can",
            "bang bien thien",
            "tiep tuyen",
            "gtln",
            "gtnn",
            "gia tri lon nhat",
            "gia tri nho nhat",
        ),
        (
            "Ứng dụng đạo hàm và khảo sát hàm số",
            "Quy tắc đạo hàm",
            "Ý nghĩa đạo hàm",
            "Hàm số và chuyển động",
            "Tốc độ biến thiên trung bình",
        ),
    ),
    (
        "nguyen_ham",
        ("nguyen ham", "ho nguyen ham"),
        (
            "Nguyên hàm",
            "Nguyên hàm và điều kiện giá trị",
            "Nguyên hàm và tích lũy",
            "Nguyên hàm và chuyển động",
            "Nguyên hàm và tăng trưởng mũ",
            "Đạo hàm và nguyên hàm",
            "Đạo hàm và nguyên hàm ứng dụng",
        ),
    ),
    (
        "tich_phan",
        (
            "tich phan",
            "dien tich hinh phang",
            "the tich khoi tron xoay",
            "ung dung tich phan",
        ),
        (
            "Tích phân xác định",
            "Ứng dụng tích phân: tính diện tích và thể tích",
            "Tích phân và chuyển động",
            "Tích phân và tích lũy",
            "Tích phân và giá trị trung bình",
            "Tích phân và tối ưu",
            "Đạo hàm và tích phân ứng dụng",
            "Nguyên hàm",
            "Nguyên hàm và tích lũy",
        ),
    ),
    (
        "toi_uu",
        ("toi uu", "quy hoach tuyen tinh", "loi nhuan", "chi phi"),
        (
            "Ứng dụng đạo hàm và khảo sát hàm số",
            "Quy hoạch tuyến tính",
            "Tối ưu hình học",
            "Tối ưu khoảng cách",
            "Tích phân và tối ưu",
            "Hệ thức lượng và tối ưu phẳng",
        ),
    ),
    (
        "oxyz",
        (
            "phuong phap toa do trong khong gian",
            "toa do trong khong gian",
            "toa do khong gian",
            "oxyz",
            "phuong trinh mat phang",
            "phuong trinh duong thang",
            "phuong trinh mat cau",
            "mat cau",
            "mat phang",
            "vecto trong khong gian",
            "he truc toa do",
        ),
        (
            "Phương pháp tọa độ trong không gian",
            "Vectơ và hệ trục tọa độ trong không gian",
            "Đường thẳng không gian",
            "Tọa độ vectơ",
            "Tọa độ và đường thẳng",
            "Tọa độ và chuyển động",
            "Tọa độ không gian với cấu hình phẳng",
            "Vị trí tương đối không gian",
        ),
    ),
    (
        "hinh_hoc_khong_gian",
        (
            "hinh hoc khong gian",
            "hinh chop",
            "khoi chop",
            "lang tru",
            "quan he vuong goc",
            "quan he song song",
            "khoang cach trong khong gian",
            "goc trong khong gian",
        ),
        (
            "Hình học không gian: góc, khoảng cách và thể tích",
            "Quan hệ song song không gian",
            "Vị trí tương đối không gian",
        ),
    ),
    (
        "xac_suat",
        (
            "xac suat co dieu kien",
            "xac suat",
            "bayes",
            "so do hinh cay",
            "xac suat toan phan",
            "bien co doc lap",
        ),
        (
            "Xác suất có điều kiện",
            "Xác suất cổ điển và tổ hợp",
            "Quy tắc xác suất",
            "Xác suất cổ điển",
            "Xác suất độc lập",
            "Xác suất cơ bản",
            "Quá trình xác suất hữu hạn",
        ),
    ),
    (
        "to_hop",
        ("to hop", "chinh hop", "hoan vi", "quy tac dem", "nhi thuc newton"),
        (
            "Tổ hợp",
            "Tổ hợp có ràng buộc",
            "Xác suất cổ điển và tổ hợp",
            "Tổ hợp và không gian mẫu",
            "Đếm bằng truy hồi",
        ),
    ),
    (
        "mu_logarit",
        (
            "mu va logarit",
            "logarit",
            "luy thua",
            "ham so mu",
            "phuong trinh mu",
            "bat phuong trinh mu",
        ),
        ("Mũ và lôgarit",),
    ),
    (
        "day_so",
        ("cap so cong", "cap so nhan", "day so"),
        ("Dãy số, cấp số cộng và cấp số nhân", "Tổ hợp và cấp số cộng"),
    ),
    (
        "thong_ke",
        (
            "mau so lieu ghep nhom",
            "thong ke",
            "phuong sai",
            "do lech chuan",
            "tu phan vi",
            "khoang bien thien",
        ),
        ("Số đặc trưng của mẫu số liệu ghép nhóm",),
    ),
    (
        "luong_giac",
        ("phuong trinh luong giac", "ham so luong giac", "ham luong giac", "luong giac"),
        ("Phương trình lượng giác", "Hàm lượng giác", "Công thức lượng giác"),
    ),
    (
        "vecto",
        ("vecto", "tich vo huong"),
        (
            "Vectơ và hệ trục tọa độ trong không gian",
            "Tọa độ vectơ",
            "Tích vô hướng",
            "Tọa độ và tích vô hướng",
            "Vectơ và chuyển động",
        ),
    ),
]

_GENERIC_FULL_EXAM_CUES = (
    "tong hop",
    "de thi thu",
    "de minh hoa",
    "day du",
    "chuan cau truc",
    "chuan 2025",
    "chuan 2026",
    "de thpt",
    "toan thpt",
    "on thi tot nghiep",
    "tot nghiep thpt",
)

_PART_CLAUSE_PATTERNS: dict[Part, tuple[str, ...]] = {
    "P1": ("phan i", "phan 1", "p1", "trac nghiem nhieu lua chon", "trac nghiem 4 phuong an"),
    "P2": ("phan ii", "phan 2", "p2", "dung sai", "dung/sai"),
    "P3": ("phan iii", "phan 3", "p3", "tra loi ngan"),
}

_EXCLUDED_STOP_SIGNALS = (
    "khong co cau ngoai",
    "khong ra ngoai",
    "khong bao gom",
    "tranh cau hoi ngoai",
    "bo qua",
    "khong hoi",
    "tranh ",
)


def _phrase_in(phrase: str, text: str) -> bool:
    return bool(re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text))


def _first_pos(phrases: tuple[str, ...], text: str) -> int | None:
    hits = [
        m.start()
        for phrase in phrases
        if (m := re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text))
    ]
    return min(hits) if hits else None


def _extract_grades(norm_prompt: str) -> set[int] | None:
    grades: set[int] = set()
    pattern = r"\b(?:lop|toan)\s*(10|11|12)(?:\s*[-–và,&\s]+\s*(10|11|12))?"
    for match in re.finditer(pattern, norm_prompt):
        grades.add(int(match.group(1)))
        if match.group(2):
            grades.add(int(match.group(2)))
    if re.search(r"\b11\s*[-–]\s*12\b", norm_prompt):
        grades.update({11, 12})
    if re.search(r"\b10\s*[-–]\s*12\b", norm_prompt):
        grades.update({10, 11, 12})
    return grades or None


def _extract_explicit_chapters(
    norm_prompt: str, grades: set[int] | None
) -> list[tuple[int | None, int]]:
    roman = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7, "viii": 8, "ix": 9}
    found: list[tuple[int | None, int]] = []
    for match in re.finditer(r"\bchuong\s*(\d+|ix|viii|vii|vi|iv|v|iii|ii|i)\b", norm_prompt):
        raw = match.group(1)
        ch = int(raw) if raw.isdigit() else roman[raw]
        g = next(iter(grades)) if grades and len(grades) == 1 else None
        found.append((g, ch))
    return found


def _extract_level_preferences(norm_prompt: str) -> tuple[list[Level], list[Level], Level]:
    """Return (P1 target levels[12], P2 statement levels[4], P3 target level)."""
    easy_cues = ("de hon", "muc de", "co ban", "nhan biet nhieu", "uu tien nhan biet")
    hard_cues = ("nang cao", "muc kho", "phan hoa manh", "uu tien van dung")
    if any(k in norm_prompt for k in easy_cues):
        p1_levels: list[Level] = ["NB"] * 7 + ["TH"] * 5
    elif any(k in norm_prompt for k in hard_cues):
        p1_levels = ["NB"] * 3 + ["TH"] * 7 + ["VD"] * 2
    else:
        p1_levels = ["NB"] * 5 + ["TH"] * 7

    p2_levels: list[Level] = ["NB", "TH", "TH", "VD"]
    if _phrase_in("vdc", norm_prompt) or "van dung cao" in norm_prompt:
        p2_levels = ["NB", "TH", "TH", "VDC"]

    p3_level: Level = "VD"
    p3_basic_cues = ("phan iii co ban", "phan 3 co ban", "tra loi ngan thong hieu")
    if any(k in norm_prompt for k in p3_basic_cues):
        p3_level = "TH"
    return p1_levels, p2_levels, p3_level


def _extract_part_focus_families(norm_prompt: str) -> dict[Part, list[str]]:
    """Map part-specific clauses (e.g. 'phần III ưu tiên tối ưu và tích phân') to family names."""
    focus: dict[Part, list[str]] = {"P1": [], "P2": [], "P3": []}
    clauses = re.split(r"[.;\n]+", norm_prompt)
    for clause in clauses:
        clause = clause.strip()
        if not clause:
            continue
        if not re.match(r"^(?:phan\s*(?:i{1,3}|[123])|p[123])\b", clause):
            continue
        for part, cues in _PART_CLAUSE_PATTERNS.items():
            if any(re.match(r"^" + re.escape(c) + r"\b", clause) for c in cues):
                for fam_name, patterns, _ in _FAMILY_PATTERNS:
                    if _first_pos(patterns, clause) is not None and fam_name not in focus[part]:
                        focus[part].append(fam_name)
    return focus


def _pack_levels_for_part(pack: dict[str, Any], part: Part) -> set[str]:
    levels: set[str] = set()
    for obs in pack["construction_observations"]:
        if obs.get("part") == part and obs.get("level") in {"NB", "TH", "VD"}:
            levels.add(obs["level"])
    for ex in pack["examples"]:
        if ex.get("part") == part:
            if ex.get("level") in {"NB", "TH", "VD"}:
                levels.add(ex["level"])
            for ans in ex.get("answers") or []:
                if isinstance(ans, dict) and ans.get("level") in {"NB", "TH", "VD"}:
                    levels.add(ans["level"])
    return levels


def _pack_supports_part(pack: dict[str, Any], part: Part) -> bool:
    if any(o.get("part") == part for o in pack["construction_observations"]):
        return True
    if any(e.get("part") == part for e in pack["examples"]):
        return True
    return False


def _resolve_level_for_pack(pack: dict[str, Any], part: Part, desired: Level) -> Level | None:
    available = _pack_levels_for_part(pack, part)
    if not available:
        return None
    if part == "P2":
        return "TH" if "TH" in available else next(iter(sorted(available)))
    if desired in available:
        return desired
    if desired == "VDC" and "VD" in available:
        return "VDC"
    fallback_order: dict[str, tuple[Level, ...]] = {
        "NB": ("TH", "VD"),
        "TH": ("NB", "VD"),
        "VD": ("TH", "NB"),
        "VDC": ("VD", "TH", "NB"),
    }
    for cand in fallback_order[desired]:
        if cand in available:
            return cand
    return None


def _pack_objectives(pack: dict[str, Any], part: Part, level: Level) -> list[str]:
    """Derive distinct, concrete Vietnamese objectives from verified RAG observations & patterns."""
    candidates: list[str] = []
    seen: set[str] = set()

    def add(text: str) -> None:
        cleaned = re.sub(r"\s+", " ", text).strip().rstrip(".")
        if len(cleaned) < 12:
            return
        if len(cleaned) > 150:
            cleaned = cleaned[:147].rsplit(" ", 1)[0].rstrip(",;:")
        key = normalize(cleaned)
        if key not in seen:
            seen.add(key)
            candidates.append(cleaned)

    eff_level = "VD" if level == "VDC" else level
    obs_list = [o for o in pack["construction_observations"] if o.get("part") == part]
    obs_list.sort(
        key=lambda o: (
            0 if o.get("level") == eff_level else 1,
            0 if o.get("evidence_class") == "official" else 1,
            str(o.get("ref") or ""),
        )
    )
    for obs in obs_list:
        task = str(obs.get("task") or "").strip()
        topic = str(obs.get("topic") or "").strip()
        if task:
            add(f"{topic}: {task}" if topic and normalize(topic) not in normalize(task) else task)
    for pat in pack["patterns"]:
        if pat.get("part") == part and pat.get("construction"):
            add(str(pat["construction"]))
    for curr in pack["curriculum_units"]:
        outcomes = curr.get("outcomes_vi") or []
        if isinstance(outcomes, list) and outcomes:
            add(f"{curr['title']}: {outcomes[0]}")
        else:
            add(f"Vận dụng kiến thức {curr['title']} ({pack['display_topic']})")
    if not candidates:
        candidates.append(f"Giải bài toán về {pack['display_topic']} mức độ {level}")
    return candidates


def _pick_curriculum_ids(
    pack: dict[str, Any],
    objective: str,
    grades: set[int] | None,
    limit: int = 2,
) -> list[str]:
    units = list(pack.get("curriculum_units") or [])
    if not units:
        return []
    if grades:
        grade_units = [u for u in units if u["grade"] in grades]
        if grade_units:
            units = grade_units
    query_text = f"{pack['display_topic']} {objective}"
    obj_tokens = {w for w in re.findall(r"[a-z0-9]+", normalize(query_text)) if len(w) >= 3}
    ranked = [
        u
        for _, u in sorted(
            enumerate(units),
            key=lambda item: (
                -_score_curriculum_for_slot(item[1], item[0], query_text, obj_tokens),
                item[1]["unit_id"],
            ),
        )
    ]
    return [u["unit_id"] for u in ranked[:limit]]


def _resolve_requested_families(
    norm_prompt: str,
    release: dict[str, Any],
    grades: set[int] | None,
) -> list[tuple[str, list[dict[str, Any]]]]:
    """Resolve ordered topic families from user prompt against verified RAG packs."""
    norm_name_to_id: dict[str, str] = release["norm_name_to_id"]
    by_id: dict[str, dict[str, Any]] = release["topic_packs_by_id"]

    # Strip negation phrases and part-only preference clauses when identifying core exam topics,
    # so "Phần III ưu tiên tối ưu" focuses P3 without injecting unrelated global families.
    core_clauses: list[str] = []
    positive_clauses: list[str] = []
    for clause in re.split(r"[.;\n]+", norm_prompt):
        c = clause.strip()
        if not c:
            continue
        if any(sig in c for sig in _EXCLUDED_STOP_SIGNALS):
            continue
        positive_clauses.append(c)
        is_part_only = bool(re.match(r"^(?:phan\s*(?:i{1,3}|[123])|p[123])\b", c))
        if not is_part_only:
            core_clauses.append(c)

    def _match_text(search_text: str) -> list[tuple[int, str, list[dict[str, Any]]]]:
        found: list[tuple[int, str, list[dict[str, Any]]]] = []
        seen_ids: set[str] = set()
        for fam_name, patterns, pack_names in _FAMILY_PATTERNS:
            pos = _first_pos(patterns, search_text)
            if pos is None:
                continue
            packs = []
            for pname in pack_names:
                tp_id = norm_name_to_id.get(normalize(pname))
                if tp_id and tp_id in by_id:
                    packs.append(by_id[tp_id])
            if packs:
                found.append((pos, fam_name, packs))
                seen_ids.update(p["topic_pack_id"] for p in packs)

        for tp_id, pack in sorted(by_id.items()):
            if tp_id in seen_ids:
                continue
            disp_norm = normalize(pack["display_topic"])
            if len(disp_norm) >= 6 and _phrase_in(disp_norm, search_text):
                pos = search_text.find(disp_norm)
                found.append((pos, f"pack:{tp_id}", [pack]))
                seen_ids.add(tp_id)

        for ch_grade, ch_num in _extract_explicit_chapters(search_text, grades):
            ch_packs = [
                pack
                for pack in by_id.values()
                if any(
                    u.get("chapter") == ch_num and (ch_grade is None or u.get("grade") == ch_grade)
                    for u in pack.get("curriculum_units") or []
                )
            ]
            if ch_packs:
                found.append((0, f"chapter_{ch_grade or 'any'}_c{ch_num}", ch_packs))
        return found

    matched = _match_text(" . ".join(core_clauses)) if core_clauses else []
    if not matched and positive_clauses:
        matched = _match_text(" . ".join(positive_clauses))

    matched.sort(key=lambda item: item[0])

    # Keep specific families cleanly: if user asked for "đạo hàm" + "tích phân" AND
    # "phần III ưu tiên tối ưu", avoid creating a redundant 3rd top-level family for "tối ưu"
    # unless "tối ưu" was a primary topic outside P3-only emphasis.
    families: list[tuple[str, list[dict[str, Any]]]] = [
        (fam_name, packs) for _, fam_name, packs in matched
    ]
    if grades:
        filtered_families: list[tuple[str, list[dict[str, Any]]]] = []
        for fam_name, packs in families:
            strict_curr = [
                p
                for p in packs
                if any(u["grade"] in grades for u in (p.get("curriculum_units") or []))
            ]
            grade_meta = [p for p in packs if not p["grades"] or bool(set(p["grades"]) & grades)]
            filtered_families.append((fam_name, strict_curr or grade_meta or packs))
        families = filtered_families
    return families


def _is_general_exam_prompt(norm_prompt: str) -> bool:
    return any(cue in norm_prompt for cue in _GENERIC_FULL_EXAM_CUES)


def plan_request_from_prompt(
    prompt: str,
    *,
    corpus_ref: str = DEFAULT_CORPUS_REF,
    pack_dir: Path | None = None,
    repo: Path | None = None,
    release: dict[str, Any] | None = None,
) -> Request:
    """Turn a Vietnamese exam prompt into a RAG-verified 22-slot THPT Request."""
    cleaned_prompt = prompt.strip()
    if not cleaned_prompt:
        raise ValueError("Prompt must be nonempty")

    norm_prompt = normalize(cleaned_prompt)
    for forbidden in OUT_OF_CURRICULUM_PHRASES:
        if _phrase_in(forbidden, norm_prompt):
            raise RagHandoffError(
                [
                    {
                        "code": "out_of_curriculum_topic",
                        "message": (
                            "Yêu cầu chứa chủ đề ngoài chương trình Toán THPT GDPT 2018: "
                            f"{forbidden!r}."
                        ),
                    }
                ]
            )

    active_release = release or load_profile_release(
        subject="toan",
        ref=corpus_ref,
        repo=repo or Path.cwd(),
        pack_dir=pack_dir,
    )
    grades = _extract_grades(norm_prompt)
    p1_targets, p2_targets, p3_target = _extract_level_preferences(norm_prompt)
    part_focus = _extract_part_focus_families(norm_prompt)
    families = _resolve_requested_families(norm_prompt, active_release, grades)

    # Full-exam fallback only when the user genuinely requested a general THPT exam.
    if not families:
        if not _is_general_exam_prompt(norm_prompt):
            raise RagHandoffError(
                [
                    {
                        "code": "topic_not_found",
                        "message": (
                            "Không tìm thấy chuyên đề Toán THPT phù hợp trong kho RAG "
                            "cho yêu cầu đã nhập."
                        ),
                    }
                ]
            )
        base = default_request()
        enriched_slots: list[Slot] = []
        p1_idx = 0
        for slot in base.slots:
            matched = _resolve_candidate_topic_packs(
                active_release,
                MatrixQuestionSpec(
                    question_id=slot.id,
                    part=slot.part,
                    topic=slot.topic,
                    learning_objective=slot.objective,
                    level=slot.level,
                ),
            )
            pack = matched[0] if matched else None
            cids = _pick_curriculum_ids(pack, slot.objective, grades) if pack else []
            new_level = slot.level
            if slot.part == "P1":
                desired = p1_targets[p1_idx]
                p1_idx += 1
                if pack:
                    resolved = _resolve_level_for_pack(pack, "P1", desired)
                    if resolved:
                        new_level = resolved
            enriched_slots.append(
                slot.model_copy(
                    update={
                        "level": new_level,
                        "statement_levels": list(p2_targets) if slot.part == "P2" else [],
                        "curriculum_unit_ids": cids,
                    }
                )
            )
        return Request(
            slots=enriched_slots,
            requirements=[
                cleaned_prompt,
                (
                    "Phạm vi bắt buộc: bám sát yêu cầu người dùng, mục tiêu từng slot "
                    "và dẫn chứng RAG cùng question_id."
                ),
            ],
        )

    # Build a 22-slot topic-focused THPT blueprint strictly from verified RAG packs.
    slots: list[Slot] = []
    objective_cursors: dict[tuple[str, str], int] = {}
    selected_topics_summary: list[str] = []

    for part in ("P1", "P2", "P3"):
        count = COUNTS[part]
        part_families: list[tuple[str, list[dict[str, Any]]]] = []
        focused_names = set(part_focus.get(part) or [])
        for fam_name, packs in families:
            usable = [p for p in packs if _pack_supports_part(p, part)]
            if usable:
                part_families.append((fam_name, usable))
        if not part_families:
            requested_names = ", ".join(fam for fam, _ in families)
            raise RagHandoffError(
                [
                    {
                        "code": "part_not_covered",
                        "message": (
                            f"Các chuyên đề đã chọn ({requested_names}) "
                            f"không có đủ dẫn chứng RAG cho phần {part}."
                        ),
                    }
                ]
            )

        # If the user highlighted specific families for this part, prioritize them in rotation.
        ordered_families = part_families
        if focused_names:
            focused = [f for f in part_families if f[0] in focused_names]
            others = [f for f in part_families if f[0] not in focused_names]
            if focused:
                ordered_families = focused + others

        family_pack_cursor: dict[str, int] = {fam: 0 for fam, _ in ordered_families}
        for idx in range(count):
            fam_name, usable_packs = ordered_families[idx % len(ordered_families)]
            desired_level: Level = (
                p1_targets[idx] if part == "P1" else ("TH" if part == "P2" else p3_target)
            )
            # Prefer a pack in this family supporting desired_level, rotating packs for diversity.
            start = family_pack_cursor[fam_name]
            rotated = [
                usable_packs[(start + offset) % len(usable_packs)]
                for offset in range(len(usable_packs))
            ]
            chosen_pack = rotated[0]
            chosen_level = (
                _resolve_level_for_pack(chosen_pack, part, desired_level) or desired_level
            )
            for cand_pack in rotated:
                cand_levels = _pack_levels_for_part(cand_pack, part)
                if part == "P2" and {"NB", "TH", "VD"} <= cand_levels:
                    chosen_pack = cand_pack
                    chosen_level = _resolve_level_for_pack(cand_pack, part, desired_level) or "TH"
                    break
                if part != "P2" and desired_level in cand_levels:
                    chosen_pack = cand_pack
                    chosen_level = desired_level
                    break
            family_pack_cursor[fam_name] = (start + 1) % len(usable_packs)

            obj_pool = _pack_objectives(chosen_pack, part, chosen_level)
            cur_key = (chosen_pack["topic_pack_id"], part)
            obj_idx = objective_cursors.get(cur_key, 0)
            objective = obj_pool[obj_idx % len(obj_pool)]
            objective_cursors[cur_key] = obj_idx + 1

            cids = _pick_curriculum_ids(chosen_pack, objective, grades)
            if chosen_pack["display_topic"] not in selected_topics_summary:
                selected_topics_summary.append(chosen_pack["display_topic"])

            slots.append(
                Slot(
                    id=f"{part}-{idx + 1}",
                    part=part,
                    topic=chosen_pack["display_topic"],
                    objective=objective,
                    level=chosen_level,
                    statement_levels=list(p2_targets) if part == "P2" else [],
                    curriculum_unit_ids=cids,
                )
            )

    topics_line = ", ".join(selected_topics_summary)
    return Request(
        slots=slots,
        requirements=[
            cleaned_prompt,
            (
                f"Phạm vi bắt buộc từ RAG: chỉ soạn câu hỏi trong các chủ đề [{topics_line}] "
                "và đúng curriculum_unit_ids của từng slot; không chèn câu hỏi ngoài chuyên đề. "
                "Mỗi câu phải bám mục tiêu học tập, mức nhận thức và dẫn chứng "
                "UNTRUSTED_RAG_EVIDENCE có cùng question_id."
            ),
        ],
    )
