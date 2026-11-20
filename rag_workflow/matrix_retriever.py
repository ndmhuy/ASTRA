"""Exam-matrix and per-question Topic-Pack retriever for MAS Orchestrator & Composer."""

from collections import defaultdict
import re
from typing import Any

from .mas_adapter import build_mas_intake_rag_entries, render_reference_material
from .models import (
    CONFIG,
    Gap,
    MatrixQuestionSpec,
    MatrixRetrievalRequest,
    MatrixRetrievalResponse,
    QuestionContext,
)
from .profile_pack import get_topic_pack, load_profile_release
from .query_parser import normalize

GENERIC_MATH_TOKENS = frozenset(
    {
        "toan",
        "bai",
        "cau",
        "phan",
        "muc",
        "do",
        "tim",
        "tinh",
        "cho",
        "biet",
        "xac",
        "dinh",
        "gia",
        "tri",
        "cua",
        "trong",
        "tren",
        "voi",
        "모",
        "mot",
        "hai",
        "ba",
        "bon",
        "cac",
        "va",
        "hoac",
        "khi",
        "theo",
        "tu",
        "den",
        "ung",
        "dung",
        "co",
        "ban",
        "thuc",
        "te",
        "thuc",
        "tien",
        "cong",
        "thuc",
        "quy",
        "tac",
        "dinh",
        "nghia",
        "tinh",
        "chat",
        "dang",
        "so",
        "ham",
        "phuong",
        "trinh",
        "he",
    }
)

OUT_OF_CURRICULUM_PHRASES = (
    "so phuc",
    "can bac hai so phuc",
    "modun so phuc",
    "ma tran nghich dao",
    "dinh thuc ma tran",
    "khong gian vecto n chieu",
    "tri rieng",
    "vecto rieng",
    "tich phan duong",
    "tich phan mat",
    "tich phan boi",
    "phuong trinh vi phan",
    "chuoi fourier",
    "bien doi laplace",
)


def default_toan_thpt_matrix() -> dict[str, Any]:
    """Return the canonical 22-question Toán THPT sample exam matrix (12 P1, 4 P2, 6 P3)."""
    return {
        "schema_version": CONFIG["schema_version"],
        "matrix_id": "toan-thpt-2026-default-22q",
        "subject": "toan",
        "vdc_policy": "fallback_with_warning",
        "questions": [
            {
                "question_id": "P1_Q01",
                "group_id": "G_P1_NGUYEN_HAM",
                "part": "P1",
                "topic": "Nguyên hàm",
                "learning_objective": "Tìm họ nguyên hàm của hàm số lũy thừa và các hàm số cơ bản bằng quy tắc nguyên hàm",
                "level": "TH",
            },
            {
                "question_id": "P1_Q02",
                "group_id": "G_P1_NGUYEN_HAM",
                "part": "P1",
                "topic": "Nguyên hàm",
                "learning_objective": "Nhận biết định nghĩa và công thức nguyên hàm cơ bản của hàm số lũy thừa, lượng giác",
                "level": "NB",
            },
            {
                "question_id": "P1_Q03",
                "group_id": "G_P1_HAM_SO",
                "part": "P1",
                "topic": "Ứng dụng đạo hàm và khảo sát hàm số",
                "learning_objective": "Xác định khoảng đơn điệu, điểm cực trị hoặc tiệm cận của hàm số từ bảng biến thiên hoặc đồ thị",
                "level": "TH",
            },
            {
                "question_id": "P1_Q04",
                "group_id": "G_P1_TICH_PHAN",
                "part": "P1",
                "topic": "Ứng dụng tích phân: tính diện tích và thể tích",
                "learning_objective": "Nhận biết công thức tính diện tích hình phẳng hoặc thể tích khối tròn xoay bằng tích phân",
                "level": "NB",
            },
            {
                "question_id": "P1_Q05",
                "group_id": "G_P1_TICH_PHAN",
                "part": "P1",
                "topic": "Ứng dụng tích phân: tính diện tích và thể tích",
                "learning_objective": "Tính tích phân xác định hoặc diện tích hình phẳng giới hạn bởi các đồ thị hàm số",
                "level": "TH",
            },
            {
                "question_id": "P1_Q06",
                "group_id": "G_P1_HHKG",
                "part": "P1",
                "topic": "Hình học không gian: góc, khoảng cách và thể tích",
                "learning_objective": "Nhận biết quan hệ vuông góc hoặc công thức thể tích khối chóp, khối lăng trụ",
                "level": "NB",
            },
            {
                "question_id": "P1_Q07",
                "group_id": "G_P1_HHKG",
                "part": "P1",
                "topic": "Hình học không gian: góc, khoảng cách và thể tích",
                "learning_objective": "Tính thể tích khối chóp, lăng trụ hoặc góc, khoảng cách cơ bản trong không gian",
                "level": "TH",
            },
            {
                "question_id": "P1_Q08",
                "group_id": "G_P1_OXYZ",
                "part": "P1",
                "topic": "Vectơ và hệ trục tọa độ trong không gian",
                "learning_objective": "Xác định tọa độ điểm, tọa độ vectơ hoặc tích vô hướng trong hệ trục tọa độ Oxyz",
                "level": "NB",
            },
            {
                "question_id": "P1_Q09",
                "group_id": "G_P1_OXYZ",
                "part": "P1",
                "topic": "Phương pháp tọa độ trong không gian",
                "learning_objective": "Nhận biết vectơ pháp tuyến của mặt phẳng, vectơ chỉ phương của đường thẳng hoặc tâm, bán kính mặt cầu",
                "level": "NB",
            },
            {
                "question_id": "P1_Q10",
                "group_id": "G_P1_MU_LOG",
                "part": "P1",
                "topic": "Mũ và lôgarit",
                "learning_objective": "Giải phương trình, bất phương trình mũ hoặc lôgarit cơ bản và xác định tập nghiệm",
                "level": "TH",
            },
            {
                "question_id": "P1_Q11",
                "group_id": "G_P1_CAP_SO",
                "part": "P1",
                "topic": "Dãy số, cấp số cộng và cấp số nhân",
                "learning_objective": "Tìm số hạng tổng quát, công sai, công bội hoặc tổng n số hạng đầu của cấp số cộng, cấp số nhân",
                "level": "NB",
            },
            {
                "question_id": "P1_Q12",
                "group_id": "G_P1_THONG_KE",
                "part": "P1",
                "topic": "Số đặc trưng của mẫu số liệu ghép nhóm",
                "learning_objective": "Xác định khoảng biến thiên, khoảng tứ phân vị hoặc phương sai, độ lệch chuẩn của mẫu số liệu ghép nhóm",
                "level": "NB",
            },
            {
                "question_id": "P2_Q01",
                "group_id": "G_P2_HAM_SO",
                "part": "P2",
                "topic": "Ứng dụng đạo hàm và khảo sát hàm số",
                "learning_objective": "Xét tính đúng/sai của các mệnh đề về tính đơn điệu, cực trị, tiệm cận và đồ thị hàm số",
                "statement_levels": {"a": "NB", "b": "TH", "c": "TH", "d": "VD"},
            },
            {
                "question_id": "P2_Q02",
                "group_id": "G_P2_NGUYEN_HAM_TICH_PHAN",
                "part": "P2",
                "topic": "Nguyên hàm và tích lũy",
                "learning_objective": "Khôi phục hàm đại lượng từ tốc độ biến thiên và tính tích phân trong bài toán chuyển động/tích lũy",
                "statement_levels": {"a": "NB", "b": "TH", "c": "TH", "d": "VD"},
            },
            {
                "question_id": "P2_Q03",
                "group_id": "G_P2_OXYZ",
                "part": "P2",
                "topic": "Phương pháp tọa độ trong không gian",
                "learning_objective": "Xét phương trình mặt phẳng, đường thẳng, mặt cầu và vị trí tương đối trong không gian Oxyz",
                "statement_levels": {"a": "NB", "b": "TH", "c": "TH", "d": "VD"},
            },
            {
                "question_id": "P2_Q04",
                "group_id": "G_P2_XAC_SUAT",
                "part": "P2",
                "topic": "Xác suất có điều kiện",
                "learning_objective": "Tính xác suất có điều kiện, sử dụng sơ đồ hình cây, công thức xác suất toàn phần và công thức Bayes",
                "statement_levels": {"a": "NB", "b": "TH", "c": "TH", "d": "VD"},
            },
            {
                "question_id": "P3_Q01",
                "group_id": "G_P3_HHKG",
                "part": "P3",
                "topic": "Hình học không gian: góc, khoảng cách và thể tích",
                "learning_objective": "Tính khoảng cách hoặc thể tích trong bài toán hình học không gian gắn với mô hình thực tiễn",
                "level": "VD",
            },
            {
                "question_id": "P3_Q02",
                "group_id": "G_P3_TICH_PHAN",
                "part": "P3",
                "topic": "Ứng dụng tích phân: tính diện tích và thể tích",
                "learning_objective": "Thiết lập hàm biên và dùng tích phân tính diện tích hoặc thể tích vật thể trong thực tế",
                "level": "VD",
            },
            {
                "question_id": "P3_Q03",
                "group_id": "G_P3_OXYZ",
                "part": "P3",
                "topic": "Phương pháp tọa độ trong không gian",
                "learning_objective": "Mô hình hóa bài toán vị trí, quỹ đạo hoặc khoảng cách thực tế trong hệ trục tọa độ Oxyz",
                "level": "VD",
            },
            {
                "question_id": "P3_Q04",
                "group_id": "G_P3_TOI_UU",
                "part": "P3",
                "topic": "Tối ưu",
                "learning_objective": "Giải bài toán tối ưu thực tiễn (tối đa hóa lợi nhuận, tối thiểu hóa chi phí hoặc khoảng cách) bằng đạo hàm",
                "level": "VD",
            },
            {
                "question_id": "P3_Q05",
                "group_id": "G_P3_QUY_HOACH",
                "part": "P3",
                "topic": "Quy hoạch tuyến tính",
                "learning_objective": "Lập hệ bất phương trình bậc nhất hai ẩn và tìm phương án tối ưu trên miền đa giác nghiệm",
                "level": "VD",
            },
            {
                "question_id": "P3_Q06",
                "group_id": "G_P3_XAC_SUAT",
                "part": "P3",
                "topic": "Xác suất cổ điển và tổ hợp",
                "learning_objective": "Đếm cấu hình có ràng buộc và tính xác suất cổ điển hoặc xác suất có điều kiện trong bài toán nhiều bước",
                "level": "VD",
            },
        ],
    }


def _distinctive_tokens(text: str) -> set[str]:
    norm = normalize(text)
    return {
        w
        for w in re.findall(r"\w+", norm)
        if len(w) >= 3 and w not in CONFIG["stop_words"] and w not in GENERIC_MATH_TOKENS
    }


def _resolve_candidate_topic_packs(
    release: dict[str, Any], q_spec: MatrixQuestionSpec
) -> list[dict[str, Any]]:
    """Resolve one or more Topic Packs for a question specification."""
    by_id: dict[str, dict[str, Any]] = release["topic_packs_by_id"]
    topic_norm = normalize(q_spec.topic).strip()
    obj_norm = normalize(q_spec.learning_objective or "").strip()

    # Guard against known out-of-curriculum topics removed from GDPT 2018.
    for forbidden in OUT_OF_CURRICULUM_PHRASES:
        if forbidden in topic_norm:
            return []

    candidate_ids: list[str] = []

    # 1. Direct ID or exact topic_key / display_topic match.
    try:
        exact_pack = get_topic_pack(release, q_spec.topic)
        candidate_ids.append(exact_pack["topic_pack_id"])
    except Gap:
        pass

    # 2. Check matrix-mapping table from corpus audit.
    for entry in release.get("topic_mapping_entries") or []:
        if normalize(entry.get("input_topic", "")) == topic_norm:
            for target_field in ("default_topic", "family_topic"):
                t_name = entry.get(target_field)
                if t_name:
                    tp_id = release["norm_name_to_id"].get(normalize(t_name))
                    if tp_id and tp_id not in candidate_ids:
                        candidate_ids.append(tp_id)

    # 3. Check umbrella topic mappings (e.g. "nguyên hàm", "xác suất", "tối ưu", "tích phân").
    umbrella_map: dict[str, list[str]] = CONFIG.get("toan_umbrella_topics", {})
    for umb_key, pack_names in umbrella_map.items():
        if topic_norm == umb_key or re.search(
            r"(?<!\w)" + re.escape(umb_key) + r"(?!\w)", topic_norm
        ):
            for p_name in pack_names:
                tp_id = release["norm_name_to_id"].get(normalize(p_name))
                if tp_id and tp_id not in candidate_ids:
                    candidate_ids.append(tp_id)

    # 4. Keyword & anchor matching across all 71 topic packs (title + raw_topics + observation topics).
    query_anchors = _distinctive_tokens(q_spec.topic)
    obj_anchors = _distinctive_tokens(q_spec.learning_objective or "")

    scored_packs: list[tuple[float, str]] = []
    for tp_id, pack in by_id.items():
        title_norm = normalize(pack["display_topic"])
        key_norm = normalize(pack["topic_key"])
        raw_text_norm = normalize(" ".join(pack.get("raw_topics") or []))
        obs_topics_norm = normalize(
            " ".join(o.get("topic", "") for o in pack["construction_observations"])
        )

        title_anchors = _distinctive_tokens(pack["display_topic"] + " " + pack["topic_key"])
        pack_anchors = title_anchors | _distinctive_tokens(raw_text_norm)

        anchor_overlap = query_anchors & pack_anchors
        if tp_id not in candidate_ids and not anchor_overlap:
            continue

        score = 0.0
        if tp_id in candidate_ids:
            # Preserve priority order from exact/umbrella list while allowing part/level re-ranking.
            score += 25.0 - candidate_ids.index(tp_id) * 1.5
        if topic_norm == title_norm or topic_norm == key_norm:
            score += 30.0
        elif topic_norm in title_norm or title_norm in topic_norm:
            score += 15.0
        elif topic_norm in raw_text_norm or topic_norm in obs_topics_norm:
            score += 10.0

        score += 4.0 * len(query_anchors & title_anchors)
        score += 2.0 * len(query_anchors & pack_anchors)
        score += 1.5 * len(obj_anchors & pack_anchors)
        if obj_norm and any(w in raw_text_norm or w in obs_topics_norm for w in obj_anchors):
            score += 3.0

        # Boost packs that actually contain observations or examples for the requested Part (P1/P2/P3).
        part_obs = [o for o in pack["construction_observations"] if o.get("part") == q_spec.part]
        part_ex = [e for e in pack["examples"] if e.get("part") == q_spec.part]
        if part_obs:
            official_in_part = sum(o["evidence_class"] == "official" for o in part_obs)
            score += 8.0 + min(len(part_obs), 10) * 0.5 + official_in_part * 1.5
        if part_ex:
            score += 3.0

        # Check if all query anchor tokens are accounted for when not in umbrella/exact list.
        if tp_id not in candidate_ids and len(query_anchors) >= 2 and len(anchor_overlap) < 2:
            # Require at least 2 anchor tokens to match when query has >=2 distinctive tokens,
            # unless the single matched token is the entire topic title anchor.
            if anchor_overlap != title_anchors:
                continue

        if score > 0:
            scored_packs.append((score, tp_id))

    if not scored_packs:
        return []

    scored_packs.sort(key=lambda item: (-item[0], item[1]))
    top_score = scored_packs[0][0]
    selected: list[dict[str, Any]] = []
    for sc, tp_id in scored_packs:
        if len(selected) >= 3:
            break
        if len(selected) >= 1 and sc < top_score * 0.45:
            break
        selected.append(by_id[tp_id])
    return selected


def _resolve_level_policy(
    q_spec: MatrixQuestionSpec, vdc_policy: str
) -> tuple[dict[str, Any], list[dict[str, str]], list[dict[str, str]]]:
    """Resolve requested cognitive level(s) against the 3-level GDPT 2018 profile scheme (NB/TH/VD)."""
    gaps: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    scheme_name = "GDPT-2018-3-level (NB/TH/VD)"

    if q_spec.part == "P2":
        raw_stmts = q_spec.statement_levels or {
            "a": "NB",
            "b": "TH",
            "c": "TH",
            "d": "VD",
        }
        effective_stmts: dict[str, str] = {}
        has_vdc = False
        for k, lvl in sorted(raw_stmts.items()):
            if lvl == "VDC":
                has_vdc = True
                if vdc_policy == "strict_error":
                    effective_stmts[k] = "VDC"
                else:
                    effective_stmts[k] = "VD"
            else:
                effective_stmts[k] = lvl

        if has_vdc:
            msg = (
                "Profile corpus uses the 3-level GDPT 2018 scheme (NB/TH/VD). "
                "VDC is not natively labeled and high discrimination is never equated to VDC."
            )
            if vdc_policy == "strict_error":
                gaps.append({"code": "level_vdc_not_in_scheme", "message": msg})
            else:
                warnings.append(
                    {
                        "code": "vdc_mapped_to_vd",
                        "message": msg + " Mapped VDC statement(s) to VD with multi-step priority.",
                    }
                )

        return (
            {
                "requested": q_spec.level or "P2_PER_STATEMENT",
                "effective": "P2_PER_STATEMENT",
                "statement_levels_requested": dict(raw_stmts),
                "statement_levels_effective": effective_stmts,
                "scheme": scheme_name,
                "vdc_policy": vdc_policy,
                "mapping_note": (
                    "Each P2 statement (a, b, c, d) carries its own cognitive level; "
                    "sibling TF statements from the same source item stay grouped."
                ),
            },
            gaps,
            warnings,
        )

    req_lvl = q_spec.level or "TH"
    if req_lvl == "VDC":
        msg = (
            "Profile corpus uses the 3-level GDPT 2018 scheme (NB/TH/VD). "
            "VDC is not natively labeled and high discrimination is never equated to VDC."
        )
        if vdc_policy == "strict_error":
            gaps.append({"code": "level_vdc_not_in_scheme", "message": msg})
            return (
                {
                    "requested": "VDC",
                    "effective": None,
                    "scheme": scheme_name,
                    "vdc_policy": vdc_policy,
                    "mapping_note": msg,
                },
                gaps,
                warnings,
            )
        warnings.append(
            {
                "code": "vdc_mapped_to_vd",
                "message": msg + " Fallback resolved to VD (prioritizing multi-step reasoning).",
            }
        )
        return (
            {
                "requested": "VDC",
                "effective": "VD",
                "scheme": scheme_name,
                "vdc_policy": vdc_policy,
                "mapping_note": msg + " Resolved to VD under fallback_with_warning policy.",
            },
            gaps,
            warnings,
        )

    return (
        {
            "requested": req_lvl,
            "effective": req_lvl,
            "scheme": scheme_name,
            "vdc_policy": vdc_policy,
            "mapping_note": None,
        },
        gaps,
        warnings,
    )


def _score_observation(
    obs: dict[str, Any],
    obj_tokens: set[str],
    target_level: str | None,
    requested_vdc: bool,
) -> float:
    score = 0.0
    if obs.get("evidence_class") == "official":
        score += 10.0
    else:
        score += 5.0
    if target_level and obs.get("level") == target_level:
        score += 12.0
    elif obs.get("level_status") == "unknown":
        score += 1.0
    if obj_tokens:
        obs_text = normalize(
            " ".join(
                [
                    str(obs.get("topic") or ""),
                    str(obs.get("given") or ""),
                    str(obs.get("task") or ""),
                    *(str(r) for r in (obs.get("reasoning") or [])),
                ]
            )
        )
        obs_words = set(re.findall(r"\w+", obs_text))
        score += 2.5 * len(obj_tokens & obs_words)
    if requested_vdc and obs.get("level") == "VD":
        # Prioritize multi-step / integrated VD.2 reasoning without equating discrimination="high" to VDC.
        steps = obs.get("steps") or 0
        combines_count = len(obs.get("combines") or [])
        score += min(steps, 8) * 0.8 + combines_count * 1.2
    return score


def _example_levels(example: dict[str, Any]) -> set[str]:
    return {
        level
        for level in [
            example.get("level"),
            *(a.get("level") for a in (example.get("answers") or [])),
        ]
        if level
    }


def _retrieve_single_question(
    release: dict[str, Any],
    q_spec: MatrixQuestionSpec,
    req: MatrixRetrievalRequest,
) -> QuestionContext:
    lvl_info, gaps, warnings = _resolve_level_policy(q_spec, req.vdc_policy)
    requested_meta = {
        "question_id": q_spec.question_id,
        "group_id": q_spec.group_id,
        "part": q_spec.part,
        "qtype": CONFIG["parts"][q_spec.part],
        "topic": q_spec.topic,
        "learning_objective": q_spec.learning_objective,
        "level": q_spec.level,
        "statement_levels": q_spec.statement_levels,
        "needs": list(q_spec.needs),
    }

    matched_packs = _resolve_candidate_topic_packs(release, q_spec)
    if not matched_packs:
        gaps.append(
            {
                "code": "topic_not_found",
                "message": f"No topic pack in {req.subject!r} profile matches topic {q_spec.topic!r}.",
            }
        )
        ctx = QuestionContext(
            question_id=q_spec.question_id,
            group_id=q_spec.group_id,
            status="gap",
            requested=requested_meta,
            resolved_level=lvl_info,
            gaps=gaps,
            warnings=warnings,
        )
        ctx.reference_material_text = render_reference_material(ctx.to_dict())
        return ctx

    # Check if strict VDC policy blocked retrieval.
    if any(g["code"] == "level_vdc_not_in_scheme" for g in gaps):
        ctx = QuestionContext(
            question_id=q_spec.question_id,
            group_id=q_spec.group_id,
            status="gap",
            requested=requested_meta,
            resolved_level=lvl_info,
            matched_topic_packs=[
                {
                    "topic_pack_id": p["topic_pack_id"],
                    "topic_key": p["topic_key"],
                    "display_topic": p["display_topic"],
                    "grades": p["grades"],
                    **p["provenance"],
                }
                for p in matched_packs
            ],
            gaps=gaps,
            warnings=warnings,
        )
        ctx.reference_material_text = render_reference_material(ctx.to_dict())
        return ctx

    obj_tokens = _distinctive_tokens(f"{q_spec.topic} {q_spec.learning_objective or ''}")

    # Gather all observations, patterns, examples, mistakes, and curriculum across matched packs.
    all_part_obs: list[dict[str, Any]] = []
    all_part_patterns: list[dict[str, Any]] = []
    all_part_examples: list[dict[str, Any]] = []
    all_mistakes: list[dict[str, Any]] = []
    all_curriculum: list[dict[str, Any]] = []
    seen_curr_ids: set[str] = set()

    for pack in matched_packs:
        all_part_obs.extend(
            o for o in pack["construction_observations"] if o.get("part") == q_spec.part
        )
        all_part_patterns.extend(p for p in pack["patterns"] if p.get("part") == q_spec.part)
        all_part_examples.extend(e for e in pack["examples"] if e.get("part") == q_spec.part)
        all_mistakes.extend(
            m for m in pack["common_mistakes"] if m.get("part") in (None, q_spec.part)
        )
        for c in pack["curriculum_units"]:
            if c["unit_id"] not in seen_curr_ids:
                seen_curr_ids.add(c["unit_id"])
                all_curriculum.append(c)

    if not all_part_obs and not all_part_patterns and not all_part_examples:
        available_parts = sorted(
            {p_part for pack in matched_packs for p_part in pack["parts_present"]}
        )
        gaps.append(
            {
                "code": "part_not_covered",
                "message": (
                    f"Matched topic pack(s) {[p['display_topic'] for p in matched_packs]} "
                    f"have no observations, patterns, or examples for part {q_spec.part} "
                    f"(available parts: {available_parts})."
                ),
            }
        )
        ctx = QuestionContext(
            question_id=q_spec.question_id,
            group_id=q_spec.group_id,
            status="gap",
            requested=requested_meta,
            resolved_level=lvl_info,
            matched_topic_packs=[
                {
                    "topic_pack_id": p["topic_pack_id"],
                    "topic_key": p["topic_key"],
                    "display_topic": p["display_topic"],
                    "grades": p["grades"],
                    **p["provenance"],
                }
                for p in matched_packs
            ],
            curriculum_knowledge=all_curriculum[: req.max_curriculum_units]
            if "knowledge" in q_spec.needs
            else [],
            gaps=gaps,
            warnings=warnings,
        )
        ctx.reference_material_text = render_reference_material(ctx.to_dict())
        return ctx

    selected_obs: list[dict[str, Any]] = []
    selected_examples: list[dict[str, Any]] = []
    p2_coverage: dict[str, Any] | None = None

    if q_spec.part == "P2":
        # P2 True/False: keep sibling statements (a, b, c, d) from the same (paper_id, P2, idx) together.
        eff_stmts: dict[str, str] = lvl_info["statement_levels_effective"]
        req_stmts: dict[str, str] = lvl_info["statement_levels_requested"]
        needed_levels = set(eff_stmts.values())

        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for obs in all_part_obs:
            if obs.get("level_status") == "unknown" and not req.include_unknown_level:
                continue
            groups[obs["group_key"]].append(obs)

        scored_groups: list[tuple[float, str, list[dict[str, Any]]]] = []
        for g_key, g_obs in groups.items():
            g_obs_sorted = sorted(g_obs, key=lambda o: str(o.get("sub") or ""))
            g_levels = {o.get("level") for o in g_obs_sorted if o.get("level")}
            covered_count = len(needed_levels & g_levels)
            g_score = (
                covered_count * 10.0
                + max(_score_observation(o, obj_tokens, None, False) for o in g_obs_sorted)
                + len(g_obs_sorted) * 1.5
            )
            scored_groups.append((g_score, g_key, g_obs_sorted))

        scored_groups.sort(key=lambda item: (-item[0], item[1]))
        for _, _, g_obs_sorted in scored_groups:
            if len(selected_obs) >= req.max_observations:
                break
            selected_obs.extend(g_obs_sorted)

        # Prefer examples that supply levels missing from the selected sibling groups.
        uncovered = needed_levels - {obs.get("level") for obs in selected_obs}
        candidates = all_part_examples.copy()
        for _ in range(min(len(candidates), req.max_examples)):
            example = min(
                candidates,
                key=lambda e: (
                    -len(_example_levels(e) & uncovered),
                    -len(_example_levels(e) & needed_levels),
                    -bool(e.get("official_anchor_available")),
                    e["example_id"],
                ),
            )
            selected_examples.append(example)
            candidates.remove(example)
            uncovered.difference_update(_example_levels(example))

        # Build per-statement (a, b, c, d) coverage diagnostic.
        p2_coverage = {}
        missing_stmt_keys = []
        for sub_key in ("a", "b", "c", "d"):
            if sub_key not in eff_stmts:
                continue
            eff_l = eff_stmts[sub_key]
            req_l = req_stmts[sub_key]
            matching_refs = [o["ref"] for o in selected_obs if o.get("level") == eff_l]
            matching_ex_ids = [
                e["example_id"] for e in selected_examples if eff_l in _example_levels(e)
            ]
            is_cov = bool(matching_refs or matching_ex_ids)
            if not is_cov:
                missing_stmt_keys.append(f"{sub_key}:{req_l}")
            p2_coverage[sub_key] = {
                "requested_level": req_l,
                "effective_level": eff_l,
                "covered": is_cov,
                "matching_observation_refs": matching_refs[:5],
                "matching_example_ids": matching_ex_ids[:3],
            }
        if missing_stmt_keys:
            warnings.append(
                {
                    "code": "p2_sublevel_incomplete",
                    "message": (
                        "Selected P2 evidence lacks an observation or example for level(s): "
                        f"{', '.join(missing_stmt_keys)}."
                    ),
                }
            )
    else:
        # P1 (MCQ) or P3 (Short Answer): filter by effective cognitive level.
        eff_level = lvl_info["effective"]
        requested_vdc = lvl_info["requested"] == "VDC"
        eligible_obs = [
            o
            for o in all_part_obs
            if o.get("level") == eff_level
            or (req.include_unknown_level and o.get("level_status") == "unknown")
        ]
        exact_ex = [e for e in all_part_examples if e.get("level") == eff_level]

        if not eligible_obs and not exact_ex:
            avail_lvls = sorted(
                {o.get("level") for o in all_part_obs if o.get("level")}
                | {e.get("level") for e in all_part_examples if e.get("level")}
            )
            gaps.append(
                {
                    "code": "level_not_covered",
                    "message": (
                        f"Matched topic pack(s) {[p['display_topic'] for p in matched_packs]} "
                        f"have part {q_spec.part}, but no observations or examples at level {eff_level!r} "
                        f"(available levels in {q_spec.part}: {avail_lvls})."
                    ),
                }
            )
            # Still include adjacent-level patterns/curriculum for diagnostic context, but mark status="gap".
            selected_examples = all_part_examples[: req.max_examples]
        else:
            scored_obs = sorted(
                eligible_obs,
                key=lambda o: (
                    -_score_observation(o, obj_tokens, eff_level, requested_vdc),
                    str(o.get("ref") or ""),
                ),
            )
            selected_obs = scored_obs[: req.max_observations]
            other_ex = [e for e in all_part_examples if e.get("level") != eff_level]
            selected_examples = (exact_ex + other_ex)[: req.max_examples]

    if not selected_examples and "examples" in q_spec.needs:
        warnings.append(
            {
                "code": "missing_ready_examples",
                "message": f"No ready synthetic example found for {q_spec.part} in matched topic pack(s).",
            }
        )

    if any(o.get("level_status") == "unknown" for o in selected_obs):
        warnings.append(
            {
                "code": "unknown_level_observations_included",
                "message": "Includes observation(s) with level=null (unknown cognitive level); do not treat as verified NB/TH/VD.",
            }
        )

    # Deduplicate mistakes while prioritizing mistakes from the requested part.
    dedup_mistakes: list[dict[str, Any]] = []
    seen_m: set[tuple[str, str]] = set()
    for m in all_mistakes:
        k = (str(m.get("mistake_kind")), str(m.get("detail")))
        if k not in seen_m:
            seen_m.add(k)
            dedup_mistakes.append(m)

    matched_pack_headers = [
        {
            "topic_pack_id": p["topic_pack_id"],
            "topic_key": p["topic_key"],
            "display_topic": p["display_topic"],
            "grades": p["grades"],
            **p["provenance"],
        }
        for p in matched_packs
    ]

    provenance_summary = {
        "source_id": matched_packs[0]["provenance"]["source_id"],
        "source_locator": matched_packs[0]["provenance"]["source_locator"],
        "source_version": release["release_info"]["corpus_snapshot"],
        "corpus_snapshot": release["release_info"]["corpus_snapshot"],
        "release_fingerprint": release["release_fingerprint"],
        "bundle_sha256": release["release_info"]["bundle_sha256"],
        "topic_pack_ids": [p["topic_pack_id"] for p in matched_packs],
        "topic_pack_locators": [p["provenance"]["source_locator"] for p in matched_packs],
        "curriculum_unit_ids": [c["unit_id"] for c in all_curriculum[: req.max_curriculum_units]],
        "evidence_counts": {
            "official_observations": sum(
                o.get("evidence_class") == "official" for o in selected_obs
            ),
            "provincial_observations": sum(
                o.get("evidence_class") == "provincial_third_party" for o in selected_obs
            ),
            "synthetic_examples": len(selected_examples),
            "curriculum_units": min(len(all_curriculum), req.max_curriculum_units),
        },
        "approval_status": "agent-reviewed, not teacher-confirmed",
        "teacher_approved": False,
        "evidence_policy": (
            "Official and provincial source observations are abstracted patterns (never verbatim exam items). "
            "Synthetic examples are model-checked reference items (origin=synthetic_not_corpus_evidence) and not frequency evidence."
        ),
    }

    status = "gap" if gaps else ("ready_with_warnings" if warnings else "ready")
    ctx = QuestionContext(
        question_id=q_spec.question_id,
        group_id=q_spec.group_id,
        status=status,
        requested=requested_meta,
        resolved_level=lvl_info,
        matched_topic_packs=matched_pack_headers,
        curriculum_knowledge=all_curriculum[: req.max_curriculum_units]
        if "knowledge" in q_spec.needs
        else [],
        construction_patterns=all_part_patterns if "patterns" in q_spec.needs else [],
        construction_observations=selected_obs if "patterns" in q_spec.needs else [],
        p2_statement_coverage=p2_coverage,
        examples=selected_examples if "examples" in q_spec.needs else [],
        common_mistakes=dedup_mistakes[:12] if "common_mistakes" in q_spec.needs else [],
        provenance_summary=provenance_summary,
        gaps=gaps,
        warnings=warnings,
    )
    ctx.reference_material_text = render_reference_material(ctx.to_dict())
    return ctx


def parse_matrix_request(payload: dict[str, Any]) -> MatrixRetrievalRequest:
    """Validate and parse a JSON dictionary into a MatrixRetrievalRequest."""
    if not isinstance(payload, dict):
        raise Gap("invalid_request", "Matrix request payload must be a JSON object.")
    raw_questions = payload.get("questions")
    if not isinstance(raw_questions, list) or not raw_questions:
        raise Gap(
            "invalid_request", "questions must be a nonempty list of question specifications."
        )

    parsed_questions: list[MatrixQuestionSpec] = []
    for idx, q in enumerate(raw_questions, 1):
        if not isinstance(q, dict):
            raise Gap("invalid_request", f"Question entry #{idx} must be a JSON object.")
        needs_raw = q.get("needs")
        spec_kwargs: dict[str, Any] = {
            "question_id": q.get("question_id") or q.get("id") or f"Q{idx:02d}",
            "part": q.get("part"),
            "topic": q.get("topic"),
            "learning_objective": q.get("learning_objective") or q.get("objective"),
            "level": q.get("level"),
            "statement_levels": q.get("statement_levels"),
            "group_id": q.get("group_id"),
        }
        if needs_raw is not None:
            if not isinstance(needs_raw, list):
                raise Gap("invalid_request", f"needs must be a list for question #{idx}.")
            spec_kwargs["needs"] = tuple(needs_raw)
        parsed_questions.append(MatrixQuestionSpec(**spec_kwargs))

    req_kwargs: dict[str, Any] = {
        "questions": tuple(parsed_questions),
        "subject": payload.get("subject", "toan"),
        "matrix_id": payload.get("matrix_id", "toan-thpt-matrix"),
        "vdc_policy": payload.get("vdc_policy", CONFIG["default_vdc_policy"]),
        "include_unknown_level": payload.get("include_unknown_level", False),
        "max_observations": payload.get(
            "max_observations", CONFIG["default_max_observations_per_question"]
        ),
        "max_examples": payload.get("max_examples", CONFIG["default_max_examples_per_question"]),
        "max_curriculum_units": payload.get(
            "max_curriculum_units", CONFIG["default_max_curriculum_units_per_question"]
        ),
        "mode": payload.get("mode", CONFIG["default_mode"]),
        "schema_version": payload.get("schema_version", CONFIG["schema_version"]),
    }
    return MatrixRetrievalRequest(**req_kwargs)


def retrieve_exam_context(
    payload: dict[str, Any],
    ref: str = "origin/staging/rag",
    repo: Any = None,
    pack_dir: Any = None,
    release: dict[str, Any] | None = None,
) -> MatrixRetrievalResponse:
    """Stable entry point for MAS Orchestrator to retrieve topic-pack contexts for an exam matrix."""
    response = MatrixRetrievalResponse()
    try:
        req = parse_matrix_request(payload)
        response.matrix_id = req.matrix_id
        response.subject = req.subject
        active_release = release or load_profile_release(
            subject=req.subject, ref=ref, repo=repo, pack_dir=pack_dir
        )
        response.release_info = active_release["release_info"]

        contexts_dicts: list[dict[str, Any]] = []
        ready_count = 0
        warning_count = 0
        gap_count = 0

        for q_spec in req.questions:
            q_ctx = _retrieve_single_question(active_release, q_spec, req)
            q_dict = q_ctx.to_dict()
            contexts_dicts.append(q_dict)
            if q_ctx.status == "gap":
                gap_count += 1
                for g in q_ctx.gaps:
                    response.gaps.append(
                        {
                            "question_id": q_spec.question_id,
                            "code": g["code"],
                            "message": g["message"],
                        }
                    )
            elif q_ctx.status == "ready_with_warnings":
                ready_count += 1
                warning_count += 1
            else:
                ready_count += 1

        response.question_contexts = contexts_dicts
        response.mas_intake_rag = build_mas_intake_rag_entries(
            contexts_dicts, active_release["release_info"]
        )
        response.summary = {
            "total_questions": len(req.questions),
            "ready_questions": ready_count,
            "questions_with_warnings": warning_count,
            "gap_questions": gap_count,
            "parts_breakdown": {
                part_id: sum(q.part == part_id for q in req.questions)
                for part_id in ("P1", "P2", "P3")
            },
        }
        if gap_count == 0:
            response.status = "success"
        elif ready_count > 0:
            response.status = "partial_gap"
        else:
            response.status = "gap"
    except Gap as exc:
        response.gaps.append({"code": exc.code, "message": str(exc)})
    return response
