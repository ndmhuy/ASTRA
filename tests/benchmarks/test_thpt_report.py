"""End-to-end tests for blind CSV export, human grading import, report, and SVG charts."""

import asyncio
import csv
import json
import xml.etree.ElementTree as ET

from exam_baseline.benchmarks.thpt_report import build_report, export_grading_sheet
from exam_baseline.benchmarks.thpt_suite import run_suite
from exam_baseline.benchmarks.thpt_validator import run_validator_suite
from tests.paths import ROOT


def _hero_manifest(tmp_path):
    manifest = {
        "schema_version": "thpt-benchmark-v1",
        "name": "Hero Report E2E Test",
        "description": "Tests blind CSV export, ungraded handling, human grading, and SVGs.",
        "usd_to_vnd_rate": 26_000.0,
        "cost_target_vnd": 2_000.0,
        "cases": [
            {
                "id": "case_01",
                "title": "Đề tổng hợp",
                "prompt": "Tạo đề thi thử Toán THPT chuẩn 2025 đầy đủ 22 câu.",
                "focus_topics": ["Đạo hàm"],
            }
        ],
        "runs": [
            {
                "id": "hero_weak_astra",
                "experiment": "E3_hero_comparison",
                "label": "HERO: 2.5-flash-lite (low) + ASTRA Song song",
                "architecture": "astra_par",
                "model": "gemini-2.5-flash-lite",
                "reasoning_effort": "low",
            },
            {
                "id": "hero_strong_naive",
                "experiment": "E3_hero_comparison",
                "label": "BASELINE: 3.8-flash (high) + Ngu chat",
                "architecture": "naive_chat",
                "model": "gemini-3.8-flash",
                "reasoning_effort": "high",
            },
        ],
    }
    path = tmp_path / "hero_manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return path


def test_blind_csv_export_ungraded_and_graded_report_with_svgs(tmp_path):
    suite_dir = tmp_path / "suite_run"
    asyncio.run(run_suite(_hero_manifest(tmp_path), suite_dir, mode="replay", compile_mode="skip"))

    val_dir = tmp_path / "val_run"
    asyncio.run(
        run_validator_suite(
            ROOT / "examples/benchmarks/thpt_validator_suite.json",
            val_dir,
            mode="replay",
            model="gemini-2.5-flash-lite",
        )
    )

    # 1. Export blind CSV
    exported = export_grading_sheet(suite_dir, seed=7)
    assert exported["exams_exported"] == 2
    assert exported["unit_rows_exported"] == 68  # 2 exams x 34 units

    csv_path = suite_dir / "grading_sheet.csv"
    key_path = suite_dir / "blind_key.json"
    csv_text = csv_path.read_text(encoding="utf-8-sig")
    # Model & architecture names must NOT leak into blind CSV
    assert "gemini-2.5-flash-lite" not in csv_text
    assert "gemini-3.8-flash" not in csv_text
    assert "astra_par" not in csv_text

    # 2. Report BEFORE human grading MUST display 'Chưa chấm' (never fabricate scores)
    ungraded_md = suite_dir / "REPORT_UNGRADED.md"
    build_report(suite_dir, output_md=ungraded_md)
    ungraded_text = ungraded_md.read_text(encoding="utf-8")
    assert "Chưa chấm" in ungraded_text
    assert "0/68" in ungraded_text
    assert "REPLAY OFFLINE" in ungraded_text

    # 3. Simulate human grading in CSV (ASTRA gets 33/34 math, Naive gets 24/34 math)
    blind_key = json.loads(key_path.read_text(encoding="utf-8"))
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    counters: dict[str, int] = {}
    for row in rows:
        bid = row["blind_id"]
        counters[bid] = counters.get(bid, 0) + 1
        idx = counters[bid]
        is_astra = blind_key[bid]["architecture"] == "astra_par"
        row["math_ok"] = "1" if (idx <= 33 if is_astra else idx <= 24) else "0"
        row["citation_ok"] = "1" if is_astra else "0"
        row["scope_ok"] = "1" if (idx <= 34 if is_astra else idx <= 28) else "0"
        row["defect_caught_by_validator"] = "1" if is_astra else "0"

    filled_csv = suite_dir / "grading_sheet_filled.csv"
    with filled_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # 4. Build final report with human grades + validator metrics
    summary = build_report(
        suite_dir,
        grading_csv=filled_csv,
        blind_key_path=key_path,
        validator_metrics_path=val_dir / "validator_metrics.json",
    )
    assert summary["human_units_graded"] == 68
    assert summary["human_units_expected"] == 68

    md_text = (suite_dir / "BENCHMARK_REPORT.md").read_text(encoding="utf-8")
    # Strict 7-metric column priority ordering
    header_line = next(line for line in md_text.splitlines() if "1. Đúng Template" in line)
    positions = [
        header_line.index(col)
        for col in (
            "1. Đúng Template",
            "2. Tính toán",
            "3. Trích dẫn",
            "4. Validator",
            "5. Compliance",
            "6. Chi phí",
            "7. Thời gian",
        )
    ]
    assert positions == sorted(positions)
    assert "33/34 (97.1%)" in md_text
    assert "24/34 (70.6%)" in md_text
    assert "Recall (bắt trúng lỗi)" in md_text
    assert "Case Study 1" in md_text

    # 5. All 3 SVG charts exist and parse as valid XML
    for svg_name in (
        "hero_quality_bars.svg",
        "pareto_cost_vs_quality.svg",
        "latency_cost_breakdown.svg",
    ):
        svg_path = suite_dir / "charts" / svg_name
        assert svg_path.is_file()
        root = ET.fromstring(svg_path.read_text(encoding="utf-8"))
        assert root.tag.endswith("svg")
