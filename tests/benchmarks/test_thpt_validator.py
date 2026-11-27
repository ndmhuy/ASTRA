"""Tests for the THPT Math Validator Seeded Defect Suite."""

import asyncio
import json

import pytest

from exam_baseline.benchmarks.thpt_validator import (
    evaluate_validator_case,
    run_validator_suite,
    score_validator_attempts,
)
from exam_baseline.core.contracts import Completion, CompletionRequest
from exam_baseline.core.models import TokenUsage
from tests.paths import ROOT


def test_validator_suite_replay_perfect_metrics(tmp_path):
    out = tmp_path / "val_replay"
    report = asyncio.run(
        run_validator_suite(
            ROOT / "examples/benchmarks/thpt_validator_suite.json",
            out,
            mode="replay",
            model="gemini-2.5-flash-lite",
        )
    )
    metrics = report["metrics"]
    assert metrics["total_cases"] == 10
    assert metrics["clean_cases"] == 5
    assert metrics["defect_cases"] == 5
    assert metrics["recall"] == 1.0
    assert metrics["precision"] == 1.0
    assert metrics["clean_false_alarm_rate"] == 0.0
    assert metrics["clean_retention"] == 1.0
    assert metrics["caught_by_solver_count"] == 3
    assert metrics["caught_by_leak_check_count"] == 1
    assert metrics["cost_usd"] > 0 and metrics["cost_vnd"] > 0
    assert (out / "validator_metrics.json").is_file()


def test_validator_gold_and_composer_key_never_leak_into_prompts(tmp_path):
    dataset = json.loads(
        (ROOT / "examples/benchmarks/thpt_validator_suite.json").read_text(encoding="utf-8")
    )
    defect_case = next(c for c in dataset["cases"] if c["id"] == "v_defect_01_p1_wrong_key")

    captured: dict[str, list[str]] = {"solver": [], "reviewer": []}

    class SpyProvider:
        name = "spy"

        def __init__(self, role: str, payload: dict):
            self.role = role
            self.payload = payload

        async def complete(self, request: CompletionRequest) -> Completion:
            captured[self.role].append(request.user)
            return Completion(
                text=json.dumps(self.payload, ensure_ascii=False),
                model="gemini-2.5-flash-lite",
                usage=TokenUsage(input_tokens=100, output_tokens=50),
            )

    attempt = asyncio.run(
        evaluate_validator_case(
            defect_case,
            SpyProvider("solver", defect_case["replay"]["solver"]),
            SpyProvider("reviewer", defect_case["replay"]["reviewer"]),
            tmp_path / "resp",
        )
    )
    assert attempt["final_decision"] == "needs_revision"
    assert attempt["caught_by_solver"] is True

    # Solver prompt MUST NOT contain composer solution, answer key, gold, or replay
    solver_prompt = captured["solver"][0]
    solver_payload = json.loads(solver_prompt)
    solver_questions_json = json.dumps(solver_payload["questions"], ensure_ascii=False)
    assert "Sai nhầm" not in solver_prompt
    assert '"answer"' not in solver_questions_json
    assert '"solution"' not in solver_questions_json
    assert '"gold"' not in solver_prompt
    assert "expected_decision" not in solver_prompt
    assert "wrong_p1_key" not in solver_prompt

    # Reviewer prompt MUST NOT contain evaluator gold or replay
    reviewer_prompt = captured["reviewer"][0]
    assert '"gold"' not in reviewer_prompt
    assert "expected_decision" not in reviewer_prompt
    assert '"replay"' not in reviewer_prompt


def test_validator_scoring_keeps_errors_in_denominator():
    cases = [
        {"id": "c1", "category": "clean", "gold": {"has_defect": False}},
        {"id": "c2", "category": "clean", "gold": {"has_defect": False}},
        {"id": "d1", "category": "wrong_p1_key", "gold": {"has_defect": True}},
        {"id": "d2", "category": "scope_drift", "gold": {"has_defect": True}},
    ]
    attempts = [
        {
            "final_decision": "approved",
            "caught_by_solver": False,
            "caught_by_reviewer": False,
            "caught_by_leak_check": False,
            "calls": [],
            "wall_seconds": 0.5,
        },
        {
            "final_decision": "needs_revision",  # False alarm on clean
            "caught_by_solver": False,
            "caught_by_reviewer": True,
            "caught_by_leak_check": False,
            "calls": [],
            "wall_seconds": 0.5,
        },
        {
            "final_decision": "needs_revision",  # True positive
            "caught_by_solver": True,
            "caught_by_reviewer": True,
            "caught_by_leak_check": False,
            "calls": [],
            "wall_seconds": 0.5,
        },
        {
            "final_decision": None,  # Provider error -> counts as missed defect (FN)
            "caught_by_solver": False,
            "caught_by_reviewer": False,
            "caught_by_leak_check": False,
            "calls": [],
            "wall_seconds": 0.5,
        },
    ]
    metrics = score_validator_attempts(cases, attempts)
    assert metrics["errors"] == 1
    assert metrics["recall"] == pytest.approx(0.5)
    assert metrics["precision"] == pytest.approx(0.5)
    assert metrics["clean_false_alarm_rate"] == pytest.approx(0.5)
    assert metrics["clean_retention"] == pytest.approx(0.5)
