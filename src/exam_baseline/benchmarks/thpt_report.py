"""Blind CSV grading export and Human-Readable THPT Benchmark Report generator.

Two workflows:
1. `export-grading-sheet`: assigns blind IDs hiding model/architecture, writes
   private `blind_key.json`, and exports Excel-friendly `grading_sheet.csv` (34 units/exam).
2. `build-report`: combines `attempts.jsonl`, optional human-filled `grading_sheet.csv`,
   and optional `validator_metrics.json` into `BENCHMARK_REPORT.md` + 3 SVG charts.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path
from statistics import median

from exam_baseline.benchmarks.thpt_charts import (
    render_hero_quality_bars_svg,
    render_latency_cost_breakdown_svg,
    render_pareto_cost_quality_svg,
)

GRADING_COLUMNS = (
    "blind_id",
    "case_id",
    "question_id",
    "unit_id",
    "part",
    "stem_preview",
    "writer_key",
    "solver_key",
    "math_ok",
    "citation_ok",
    "scope_ok",
    "defect_caught_by_validator",
    "note",
)


def _load_latest_attempts(suite_dir: Path) -> list[dict]:
    jsonl_path = suite_dir / "attempts.jsonl"
    if not jsonl_path.is_file():
        raise ValueError(f"Missing attempts.jsonl in {suite_dir}")
    latest: dict[str, dict] = {}
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        latest[rec["attempt_key"]] = rec
    return list(latest.values())


def _canonical_unit_specs() -> list[tuple[str, str, str]]:
    """Return the exact 34 scored unit IDs in a standard THPT Math paper."""
    units: list[tuple[str, str, str]] = []
    for i in range(1, 13):
        units.append((f"P1-{i}", f"P1-{i}", "P1"))
    for i in range(1, 5):
        for stmt in "abcd":
            units.append((f"P2-{i}", f"P2-{i}{stmt}", "P2"))
    for i in range(1, 7):
        units.append((f"P3-{i}", f"P3-{i}", "P3"))
    return units


def _extract_exam_units(suite_dir: Path, attempt: dict, blind_id: str) -> list[dict]:
    attempt_dir = suite_dir / attempt["output_dir"]
    answers_path = attempt_dir / "dap_an_va_loi_giai.json"
    if answers_path.is_file():
        data = json.loads(answers_path.read_text(encoding="utf-8"))
        solver_map = {}
        if data.get("independent_solver"):
            for entry in data["independent_solver"].get("entries", []):
                solver_map[entry["question_id"]] = entry.get("answer", "")
        rows = []
        for q in data.get("composer", []):
            qid = q["id"]
            part = qid.split("-")[0]
            preview = " ".join(q.get("stem", "").split())[:120]
            solver_ans = solver_map.get(qid, "")
            if part == "P2":
                for label, stmt in zip("abcd", q.get("statements", []), strict=False):
                    rows.append(
                        {
                            "blind_id": blind_id,
                            "case_id": attempt["case_id"],
                            "question_id": qid,
                            "unit_id": f"{qid}{label}",
                            "part": part,
                            "stem_preview": f"{preview} | {label}) {stmt['text'][:80]}",
                            "writer_key": "Đúng" if stmt["answer"] else "Sai",
                            "solver_key": solver_ans,
                            "math_ok": "",
                            "citation_ok": "",
                            "scope_ok": "",
                            "defect_caught_by_validator": "",
                            "note": "",
                        }
                    )
            else:
                rows.append(
                    {
                        "blind_id": blind_id,
                        "case_id": attempt["case_id"],
                        "question_id": qid,
                        "unit_id": qid,
                        "part": part,
                        "stem_preview": preview,
                        "writer_key": q.get("answer") or "",
                        "solver_key": solver_ans,
                        "math_ok": "",
                        "citation_ok": "",
                        "scope_ok": "",
                        "defect_caught_by_validator": "",
                        "note": "",
                    }
                )
        return rows

    # Unstructured baseline (e.g., naive_chat): emit the same 34 canonical unit slots
    # pointing the human grader to the saved raw response / LaTeX file.
    ref_file = (
        f"{attempt['output_dir']}/de_thi.tex"
        if (attempt_dir / "de_thi.tex").is_file()
        else f"{attempt['output_dir']}/raw_response.txt"
    )
    return [
        {
            "blind_id": blind_id,
            "case_id": attempt["case_id"],
            "question_id": qid,
            "unit_id": uid,
            "part": part,
            "stem_preview": f"[Chấm từ file {ref_file}]",
            "writer_key": "",
            "solver_key": "",
            "math_ok": "",
            "citation_ok": "",
            "scope_ok": "",
            "defect_caught_by_validator": "",
            "note": "",
        }
        for qid, uid, part in _canonical_unit_specs()
    ]


def export_grading_sheet(
    suite_dir: Path,
    *,
    out_csv: Path | None = None,
    blind_key_path: Path | None = None,
    seed: int = 42,
) -> dict:
    """Export blind Excel-friendly CSV (34 units per exam) + separate blind_key.json."""
    attempts = _load_latest_attempts(suite_dir)
    order = list(attempts)
    rng = random.Random(seed)
    rng.shuffle(order)

    out_csv = out_csv or (suite_dir / "grading_sheet.csv")
    blind_key_path = blind_key_path or (suite_dir / "blind_key.json")

    blind_key: dict[str, dict] = {}
    csv_rows: list[dict] = []
    for idx, attempt in enumerate(order, start=1):
        blind_id = f"BLIND-{idx:03d}"
        blind_key[blind_id] = {
            "attempt_key": attempt["attempt_key"],
            "run_id": attempt["run_id"],
            "experiment": attempt["experiment"],
            "label": attempt["label"],
            "architecture": attempt["architecture"],
            "model": attempt["model"],
            "reasoning_effort": attempt["reasoning_effort"],
            "case_id": attempt["case_id"],
            "repeat": attempt["repeat"],
            "status": attempt["status"],
            "output_dir": attempt["output_dir"],
        }
        csv_rows.extend(_extract_exam_units(suite_dir, attempt, blind_id))

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=GRADING_COLUMNS)
        writer.writeheader()
        writer.writerows(csv_rows)

    blind_key_path.write_text(
        json.dumps(blind_key, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return {
        "grading_csv": str(out_csv),
        "blind_key": str(blind_key_path),
        "exams_exported": len(order),
        "unit_rows_exported": len(csv_rows),
    }


def _parse_binary(value: str | None) -> int | None:
    if value is None:
        return None
    cleaned = value.strip().casefold()
    if cleaned in {"1", "true", "yes", "đúng", "dung", "pass", "ok"}:
        return 1
    if cleaned in {"0", "false", "no", "sai", "fail"}:
        return 0
    return None


def _load_human_grades(
    grading_csv: Path | None, blind_key_path: Path | None
) -> dict[str, list[dict]]:
    """Map attempt_key -> list of graded unit rows from a human-filled CSV."""
    if not grading_csv or not grading_csv.is_file():
        return {}
    if not blind_key_path or not blind_key_path.is_file():
        raise ValueError("blind_key.json is required alongside grading_sheet.csv")
    blind_key = json.loads(blind_key_path.read_text(encoding="utf-8"))
    by_attempt: dict[str, list[dict]] = defaultdict(list)
    with grading_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            meta = blind_key.get(row["blind_id"])
            if not meta:
                continue
            by_attempt[meta["attempt_key"]].append(
                {
                    "math_ok": _parse_binary(row.get("math_ok")),
                    "citation_ok": _parse_binary(row.get("citation_ok")),
                    "scope_ok": _parse_binary(row.get("scope_ok")),
                    "defect_caught": _parse_binary(row.get("defect_caught_by_validator")),
                    "note": (row.get("note") or "").strip(),
                }
            )
    return dict(by_attempt)


def _fmt_ratio(passed: int, total: int) -> str:
    if total <= 0:
        return "Chưa chấm"
    pct = (passed / total) * 100.0
    badge = "✅" if pct >= 90.0 else ("⚠️" if pct >= 70.0 else "❌")
    return f"{badge} {passed}/{total} ({pct:.1f}%)"


def _aggregate_runs(
    attempts: list[dict],
    human_by_attempt: dict[str, list[dict]],
    validator_metrics: dict | None,
) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    order: list[str] = []
    for att in attempts:
        rid = att["run_id"]
        if rid not in grouped:
            order.append(rid)
        grouped[rid].append(att)

    validator_recall = (
        validator_metrics.get("metrics", {}).get("recall") if validator_metrics else None
    )

    rows = []
    for rid in order:
        items = grouped[rid]
        sample = items[0]
        total = len(items)
        tpl_pass = sum(1 for a in items if a.get("template_pass"))
        tpl_rate = tpl_pass / total if total else 0.0

        # Human-graded unit counts across all attempts of this run
        math_ok = math_n = cit_ok = cit_n = scope_ok = scope_n = val_ok = val_n = 0
        for att in items:
            for u in human_by_attempt.get(att["attempt_key"], []):
                if u["math_ok"] is not None:
                    math_n += 1
                    math_ok += u["math_ok"]
                if u["citation_ok"] is not None:
                    cit_n += 1
                    cit_ok += u["citation_ok"]
                if u["scope_ok"] is not None:
                    scope_n += 1
                    scope_ok += u["scope_ok"]
                if u["defect_caught"] is not None:
                    val_n += 1
                    val_ok += u["defect_caught"]

        math_rate = (math_ok / math_n) if math_n else None
        citation_rate = (cit_ok / cit_n) if cit_n else None
        compliance_rate = (scope_ok / scope_n) if scope_n else None

        if val_n:
            validator_rate = val_ok / val_n
            validator_str = _fmt_ratio(val_ok, val_n)
        elif sample["architecture"] in {"astra_seq", "astra_par"} and validator_recall is not None:
            validator_rate = validator_recall
            vm = validator_metrics["metrics"]
            validator_str = (
                f"Suite Recall {vm['true_positives']}/{vm['defect_cases']} "
                f"({validator_recall * 100:.1f}%)"
            )
        elif sample["architecture"] in {"astra_seq", "astra_par"}:
            rev_sent = sum(1 for a in items if a.get("reviewer_feedback_sent"))
            validator_rate = None
            validator_str = f"Đã chạy ({rev_sent}/{total} đề kích hoạt sửa)"
        else:
            validator_rate = 0.0
            validator_str = "❌ Không có Validator (0%)"

        rag_valid = sum(a.get("rag_citation_locator_valid", 0) for a in items)
        rag_total = total * 22
        auto_rag_rate = rag_valid / rag_total if rag_total else 0.0

        costs_vnd = [a.get("cost_vnd", 0.0) for a in items]
        costs_usd = [a.get("cost_usd", 0.0) for a in items]
        mean_cost_vnd = sum(costs_vnd) / total if total else 0.0
        mean_cost_usd = sum(costs_usd) / total if total else 0.0
        cov_mean = sum(a.get("cost_coverage", 0.0) for a in items) / total if total else 0.0

        walls = [a.get("wall_seconds", 0.0) for a in items]
        computes = [a.get("api_compute_seconds", 0.0) for a in items]
        waits = [a.get("rate_limit_wait_seconds", 0.0) for a in items]

        # Composite quality for Pareto chart: average of available quality rates (never fake N/A)
        avail_quality = [
            r for r in (tpl_rate, math_rate, citation_rate, compliance_rate) if r is not None
        ]
        composite = sum(avail_quality) / len(avail_quality) if avail_quality else tpl_rate

        rows.append(
            {
                "run_id": rid,
                "experiment": sample["experiment"],
                "label": sample["label"],
                "architecture": sample["architecture"],
                "model": sample["model"],
                "reasoning_effort": sample.get("reasoning_effort"),
                "attempts": total,
                "completed": sum(1 for a in items if a.get("status") == "completed"),
                # Priority 1..5
                "template_pass": tpl_pass,
                "template_rate": tpl_rate,
                "template_str": _fmt_ratio(tpl_pass, total),
                "math_ok": math_ok,
                "math_n": math_n,
                "math_rate": math_rate,
                "math_str": _fmt_ratio(math_ok, math_n) if math_n else "Chưa chấm",
                "citation_ok": cit_ok,
                "citation_n": cit_n,
                "citation_rate": citation_rate,
                "citation_str": (
                    _fmt_ratio(cit_ok, cit_n)
                    if cit_n
                    else f"Chưa chấm (locator: {rag_valid}/{rag_total})"
                ),
                "auto_rag_rate": auto_rag_rate,
                "validator_rate": validator_rate,
                "validator_str": validator_str,
                "compliance_ok": scope_ok,
                "compliance_n": scope_n,
                "compliance_rate": compliance_rate,
                "compliance_str": _fmt_ratio(scope_ok, scope_n) if scope_n else "Chưa chấm",
                "composite_quality_rate": composite,
                # Priority 6: Cost
                "mean_cost_usd": round(mean_cost_usd, 6),
                "mean_cost_vnd": round(mean_cost_vnd, 1),
                "cost_coverage": round(cov_mean, 3),
                # Priority 7: Latency
                "median_wall_seconds": round(median(walls), 2) if walls else 0.0,
                "max_wall_seconds": round(max(walls), 2) if walls else 0.0,
                "median_compute_seconds": round(median(computes), 2) if computes else 0.0,
                "median_wait_seconds": round(median(waits), 2) if waits else 0.0,
            }
        )
    return rows


def _extract_case_studies(suite_dir: Path, attempts: list[dict]) -> list[str]:
    """Pull up to 2 real observed snippets from saved run artifacts (never fabricated)."""
    snippets: list[str] = []
    # 1. Real ASTRA Validator catch (revision_1 review.json with issues)
    for att in attempts:
        if att.get("reviewer_feedback_sent"):
            rev_path = suite_dir / att["output_dir"] / "_internal" / "revision_1" / "review.json"
            if rev_path.is_file():
                review = json.loads(rev_path.read_text(encoding="utf-8"))
                issues = review.get("issues", [])
                if issues:
                    snippets.append(
                        f"- **Case Study 1 — ASTRA tự bắt lỗi trước khi xuất đề** "
                        f"(`{att['label']}`, đề `{att['case_id']}`):\n"
                        f"  - Vòng 1 phát hiện: `{issues[0]}`\n"
                        f"  - Hệ thống tự sửa sang Vòng 2 (`revision_count = "
                        f"{att['revision_count']}`, Solver khớp "
                        f"`{att['solver_agreed_questions']}/22`)."
                    )
                    break
    # 2. Real Naive failure (template fail / leakage)
    for att in attempts:
        if att["architecture"] == "naive_chat" and not att.get("template_pass"):
            reasons = []
            if att.get("question_count_detected", 0) != 22:
                reasons.append(f"chỉ sinh {att.get('question_count_detected', 0)}/22 câu")
            if not att.get("zero_answer_leakage"):
                reasons.append("lộ đáp án ngay trong thân đề học sinh")
            if str(att.get("pdf_compile_status", "")).startswith("failed"):
                reasons.append(f"lỗi biên dịch PDF ({att['pdf_compile_status']})")
            reason_txt = ", ".join(reasons) or (att.get("error_code") or "không đạt cấu trúc")
            snippets.append(
                f"- **Case Study 2 — Lỗi thực tế của Naive Chat** "
                f"(`{att['label']}`, đề `{att['case_id']}`):\n"
                f"  - Kết quả kiểm tra tự động: `template_pass = False` ({reason_txt}).\n"
                "  - Không có RAG (`rag_slots = 0/22`) và không có Blind Solver/Reviewer."
            )
            break
    return snippets


def _scorecard_table(rows: list[dict], cost_target_vnd: float) -> list[str]:
    lines = [
        "| Cấu hình | 1. Đúng Template | 2. Tính toán (x/34) | 3. Trích dẫn | "
        "4. Validator | 5. Compliance | 6. Chi phí (VNĐ/đề) | 7. Thời gian (med / max) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]
    for r in rows:
        cost_badge = "✅" if r["mean_cost_vnd"] <= cost_target_vnd else "⚠️"
        cost_txt = (
            f"{cost_badge} {r['mean_cost_vnd']:,.0f} đ "
            f"(USD {r['mean_cost_usd']:.4f}, cov {r['cost_coverage'] * 100:.0f}%)"
        )
        time_txt = (
            f"{r['median_wall_seconds']:.1f}s / {r['max_wall_seconds']:.1f}s "
            f"(comp {r['median_compute_seconds']:.1f}s, wait {r['median_wait_seconds']:.1f}s)"
        )
        lines.append(
            f"| **{r['label']}** | {r['template_str']} | {r['math_str']} | {r['citation_str']} | "
            f"{r['validator_str']} | {r['compliance_str']} | {cost_txt} | {time_txt} |"
        )
    return lines


def build_report(
    suite_dir: Path,
    *,
    grading_csv: Path | None = None,
    blind_key_path: Path | None = None,
    validator_metrics_path: Path | None = None,
    output_md: Path | None = None,
) -> dict:
    """Aggregate benchmark outputs and generate BENCHMARK_REPORT.md + 3 SVG charts."""
    attempts = _load_latest_attempts(suite_dir)
    manifest_path = suite_dir / "manifest_snapshot.json"
    manifest = (
        json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
    )
    suite_name = manifest.get("name", "ASTRA THPT Math Benchmark")
    cost_target_vnd = float(manifest.get("cost_target_vnd", 2_000.0))
    mode = attempts[0].get("mode", "unknown") if attempts else "unknown"

    human_by_attempt = _load_human_grades(grading_csv, blind_key_path)
    validator_metrics = (
        json.loads(validator_metrics_path.read_text(encoding="utf-8"))
        if validator_metrics_path and validator_metrics_path.is_file()
        else None
    )

    rows = _aggregate_runs(attempts, human_by_attempt, validator_metrics)
    total_units_expected = len(attempts) * 34
    total_units_graded = sum(
        sum(1 for u in units if u["math_ok"] is not None) for units in human_by_attempt.values()
    )

    charts_dir = suite_dir / "charts"
    hero_rows = [r for r in rows if r["experiment"] == "E3_hero_comparison"] or rows[:4]
    chart_quality = render_hero_quality_bars_svg(
        hero_rows, charts_dir / "hero_quality_bars.svg", mode=mode
    )
    chart_pareto = render_pareto_cost_quality_svg(
        rows, charts_dir / "pareto_cost_vs_quality.svg", cost_target_vnd=cost_target_vnd, mode=mode
    )
    chart_latency = render_latency_cost_breakdown_svg(
        rows, charts_dir / "latency_cost_breakdown.svg", mode=mode
    )

    graded_pct = (
        (total_units_graded / total_units_expected * 100.0) if total_units_expected else 0.0
    )
    md_lines = [
        f"# {suite_name}",
        "",
        f"> **Chế độ chạy:** `{mode.upper()}` | **Tổng số lần chạy (mẫu số):** `{len(attempts)}` "
        f"| **Độ phủ chấm tay mù:** `{total_units_graded}/{total_units_expected}` đơn vị "
        f"({graded_pct:.1f}%)",
        "",
    ]
    if mode == "replay":
        md_lines += [
            "> [!WARNING]",
            "> Đây là kết quả chạy **REPLAY OFFLINE** chỉ dùng để kiểm tra đường ống, bộ chấm điểm "
            "và biểu đồ. Không dùng số liệu replay làm kết luận chất lượng model thực tế.",
            "",
        ]

    # Executive Verdict (Hero Comparison)
    md_lines += ["## 1. Kết luận nhanh (Executive Verdict — Hero Test)", ""]
    hero_astra = next(
        (r for r in hero_rows if r["architecture"] in {"astra_par", "astra_seq"}), None
    )
    hero_naive = next((r for r in hero_rows if r["architecture"] == "naive_chat"), None)
    if hero_astra and hero_naive:
        md_lines += [
            f"- **Ứng viên ASTRA (Model yếu + Kiến trúc ASTRA):** `{hero_astra['label']}` — "
            f"Template {hero_astra['template_str']}, Toán {hero_astra['math_str']}, "
            f"Chi phí `{hero_astra['mean_cost_vnd']:,.0f} VNĐ/đề`.",
            f"- **Đối chứng Naive (Model mạnh + Phương pháp ngây thơ):** `{hero_naive['label']}` — "
            f"Template {hero_naive['template_str']}, Toán {hero_naive['math_str']}, "
            f"Chi phí `{hero_naive['mean_cost_vnd']:,.0f} VNĐ/đề`.",
            "",
        ]
    else:
        md_lines += [
            "- Chưa đủ cả hai nhánh đối đầu Hero (`E3_hero_comparison`) trong tập chạy.",
            "",
        ]

    # Master 7-Metric Scorecard
    md_lines += [
        "## 2. Bảng điểm tổng hợp theo đúng 7 tiêu chí ưu tiên",
        "",
        *_scorecard_table(rows, cost_target_vnd),
        "",
    ]

    # Per-experiment OFAT breakdown
    exp_titles = {
        "E1_architecture": (
            "Thí nghiệm E1 — Cô lập Kiến trúc (Ngu chat → Ngu work → Tuần tự → Song song)"
        ),
        "E2_model_reasoning": "Thí nghiệm E2 — Cô lập Model (2.5 → 3.1 → 3.8) & Reasoning Effort",
        "E3_hero_comparison": "Thí nghiệm E3 — Đối đầu Chứng minh Tính Ưu việt (Hero Comparison)",
    }
    md_lines += ["## 3. Kết quả từng thí nghiệm cô lập biến (OFAT)", ""]
    for exp_key, exp_title in exp_titles.items():
        subset = [r for r in rows if r["experiment"] == exp_key]
        if not subset:
            continue
        md_lines += [f"### {exp_title}", "", *_scorecard_table(subset, cost_target_vnd), ""]

    # Validator Seeded Defect Suite section
    if validator_metrics:
        vm = validator_metrics["metrics"]
        val_mode = validator_metrics.get("mode")
        val_model = validator_metrics.get("model")
        md_lines += [
            "## 4. Kiểm định bộ Validator trên tập lỗi cài sẵn (Seeded Defect Suite)",
            "",
            f"- **Mode:** `{val_mode}` | **Model:** `{val_model}`",
            f"- **Recall (bắt trúng lỗi):** `{vm['true_positives']}/{vm['defect_cases']}` "
            f"({(vm['recall'] or 0.0) * 100:.1f}%)",
            f"- **Precision (độ chính xác khi báo lỗi):** `{(vm['precision'] or 0.0) * 100:.1f}%`",
            f"- **False Alarm trên đề sạch:** `{(vm['clean_false_alarm_rate'] or 0.0) * 100:.1f}%` "
            f"(Giữ nguyên đề sạch: `{(vm['clean_retention'] or 0.0) * 100:.1f}%`)",
            f"- **Phân bổ nguồn bắt lỗi:** Blind Solver = `{vm['caught_by_solver_count']}`, "
            f"Reviewer = `{vm['caught_by_reviewer_count']}`, "
            f"Leakage Check = `{vm['caught_by_leak_check_count']}`",
            "",
        ]

    # Visual Charts
    md_lines += [
        "## 5. Biểu đồ trực quan (SVG)",
        "",
        "### 5.1. So sánh 5 thước đo chất lượng ưu tiên",
        "![So sánh chất lượng](charts/hero_quality_bars.svg)",
        "",
        "### 5.2. Pareto Chi phí (VNĐ/đề) vs Chất lượng tổng hợp",
        "![Pareto chi phí và chất lượng](charts/pareto_cost_vs_quality.svg)",
        "",
        "### 5.3. Phân tách thời gian sinh đề & Chi phí",
        "![Phân tách độ trễ và chi phí](charts/latency_cost_breakdown.svg)",
        "",
    ]

    # Real Case Studies
    snippets = _extract_case_studies(suite_dir, attempts)
    md_lines += ["## 6. Minh chứng thực tế (Case Studies từ artifact chạy thật)", ""]
    if snippets:
        md_lines.extend(snippets)
    else:
        md_lines.append(
            "- Chưa ghi nhận ca lỗi hoặc ca kích hoạt vòng sửa trong tập chạy hiện tại."
        )
    md_lines.append("")

    report_path = output_md or (suite_dir / "BENCHMARK_REPORT.md")
    report_path.write_text("\n".join(md_lines), encoding="utf-8")

    summary_json = suite_dir / "report_summary.json"
    summary_payload = {
        "suite_name": suite_name,
        "mode": mode,
        "report_md": str(report_path),
        "charts": [str(chart_quality), str(chart_pareto), str(chart_latency)],
        "human_units_graded": total_units_graded,
        "human_units_expected": total_units_expected,
        "runs": rows,
    }
    summary_json.write_text(
        json.dumps(summary_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary_payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    exp = sub.add_parser("export-grading-sheet", help="Export blind Excel CSV + private blind key.")
    exp.add_argument("--suite-dir", type=Path, required=True)
    exp.add_argument("--out-csv", type=Path, default=None)
    exp.add_argument("--blind-key", type=Path, default=None)
    exp.add_argument("--seed", type=int, default=42)

    rep = sub.add_parser("build-report", help="Generate BENCHMARK_REPORT.md and 3 SVG charts.")
    rep.add_argument("--suite-dir", type=Path, required=True)
    rep.add_argument("--grading-csv", type=Path, default=None)
    rep.add_argument("--blind-key", type=Path, default=None)
    rep.add_argument("--validator-metrics", type=Path, default=None)
    rep.add_argument("--output-md", type=Path, default=None)

    args = parser.parse_args()
    if args.command == "export-grading-sheet":
        result = export_grading_sheet(
            args.suite_dir, out_csv=args.out_csv, blind_key_path=args.blind_key, seed=args.seed
        )
    else:
        result = build_report(
            args.suite_dir,
            grading_csv=args.grading_csv,
            blind_key_path=args.blind_key,
            validator_metrics_path=args.validator_metrics,
            output_md=args.output_md,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
