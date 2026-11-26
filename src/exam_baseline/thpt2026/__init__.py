"""Contract-driven THPT 2026 profiles, renderers, live generator, and fallback builder."""

from exam_baseline.thpt2026.contract import (
    CONTRACT_FORMAT_IDS,
    build_student_paper,
    catalog_entries,
    expected_question_ids,
    load_contract,
    profile_by_format_id,
    validate_contract_exam,
)
from exam_baseline.thpt2026.fallback import build_fallback_exam_data, run_thpt2026_fallback_job
from exam_baseline.thpt2026.generator import run_thpt2026_live_job
from exam_baseline.thpt2026.rendering import render_contract_exam_tex

__all__ = [
    "CONTRACT_FORMAT_IDS",
    "build_fallback_exam_data",
    "build_student_paper",
    "catalog_entries",
    "expected_question_ids",
    "load_contract",
    "profile_by_format_id",
    "render_contract_exam_tex",
    "run_thpt2026_fallback_job",
    "run_thpt2026_live_job",
    "validate_contract_exam",
]
