"""Tests for the THPT 4-architecture OFAT benchmark runner."""

import asyncio
import json

import pytest

from exam_baseline.benchmarks.thpt_replay import ReplayThptProvider
from exam_baseline.benchmarks.thpt_suite import (
    ThptSuiteManifest,
    inspect_latex_template,
    run_suite,
)
from exam_baseline.core.contracts import CompletionRequest, ProviderError
from tests.paths import ROOT


def _mini_manifest(tmp_path, runs):
    manifest = {
        "schema_version": "thpt-benchmark-v1",
        "name": "Mini Test Suite",
        "description": "Unit test manifest.",
        "usd_to_vnd_rate": 25_000.0,
        "cost_target_vnd": 2_000.0,
        "cases": [
            {
                "id": "case_01",
                "title": "Đề thử nghiệm 1",
                "prompt": "Tạo đề thi thử Toán THPT chuẩn 2025 đầy đủ 22 câu hỏi.",
                "focus_topics": ["Đạo hàm"],
            }
        ],
        "runs": runs,
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return path


def test_canonical_gemini_manifest_validates():
    manifest = ThptSuiteManifest.model_validate_json(
        (ROOT / "examples/benchmarks/thpt_gemini_suite.json").read_bytes()
    )
    assert len(manifest.cases) == 5
    experiments = {r.experiment for r in manifest.runs}
    assert experiments == {"E1_architecture", "E2_model_reasoning", "E3_hero_comparison"}
    hero = [r for r in manifest.runs if r.experiment == "E3_hero_comparison"]
    assert any(r.model == "gemini-2.5-flash-lite" and r.architecture == "astra_par" for r in hero)
    assert any(r.model == "gemini-3.8-flash" and r.architecture == "naive_chat" for r in hero)


def test_all_four_architectures_replay_and_resume(tmp_path):
    manifest_path = _mini_manifest(
        tmp_path,
        [
            {
                "id": "r_naive",
                "experiment": "E1_architecture",
                "label": "Naive",
                "architecture": "naive_chat",
                "model": "gemini-2.5-flash-lite",
                "reasoning_effort": "low",
            },
            {
                "id": "r_rag",
                "experiment": "E1_architecture",
                "label": "RAG 1-shot",
                "architecture": "single_shot_rag",
                "model": "gemini-2.5-flash-lite",
                "reasoning_effort": "low",
            },
            {
                "id": "r_seq",
                "experiment": "E1_architecture",
                "label": "ASTRA Seq",
                "architecture": "astra_seq",
                "model": "gemini-2.5-flash-lite",
                "reasoning_effort": "low",
            },
            {
                "id": "r_par",
                "experiment": "E1_architecture",
                "label": "ASTRA Par",
                "architecture": "astra_par",
                "model": "gemini-2.5-flash-lite",
                "reasoning_effort": "low",
            },
        ],
    )
    out = tmp_path / "out"
    first = asyncio.run(run_suite(manifest_path, out, mode="replay", compile_mode="skip"))
    assert first["executed_in_this_invocation"] == 4
    assert first["completed_attempts"] == 4
    assert first["failed_attempts"] == 0

    rows = [
        json.loads(line)
        for line in (out / "attempts.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    by_id = {row["run_id"]: row for row in rows}

    # Naive on 2.5-flash-lite replay simulates incomplete/leaked output -> template_pass False
    assert by_id["r_naive"]["template_pass"] is False
    assert by_id["r_naive"]["rag_slots_with_evidence"] == 0
    assert by_id["r_naive"]["reviewer_ran"] is False
    assert by_id["r_naive"]["cost_usd"] > 0 and by_id["r_naive"]["cost_vnd"] > 0

    # Single-shot RAG preserves locked template, has RAG evidence, but no solver/reviewer
    assert by_id["r_rag"]["template_pass"] is True
    assert by_id["r_rag"]["locked_template_preserved"] is True
    assert by_id["r_rag"]["rag_citation_locator_valid"] == 22
    assert by_id["r_rag"]["reviewer_ran"] is False
    assert by_id["r_rag"]["solver_agreed_questions"] is None

    # ASTRA seq & par run Blind Solver + Reviewer and catch the seeded revision on 2.5
    for run_id in ("r_seq", "r_par"):
        assert by_id[run_id]["template_pass"] is True
        assert by_id[run_id]["reviewer_ran"] is True
        assert by_id[run_id]["reviewer_feedback_sent"] is True
        assert by_id[run_id]["revision_count"] == 2
        assert by_id[run_id]["solver_agreed_questions"] == 22
        assert by_id[run_id]["scored_units_total"] == 34

    # Resume skips all 4 completed attempts cleanly
    resumed = asyncio.run(
        run_suite(manifest_path, out, mode="replay", resume=True, compile_mode="skip")
    )
    assert resumed["executed_in_this_invocation"] == 0
    assert resumed["skipped_on_resume"] == 4


def test_failed_attempt_stays_in_denominator_and_tracks_retry_wait(tmp_path):
    class FlakyThenSuccess:
        name = "flaky"

        def __init__(self, inner, fail_times: int):
            self.inner = inner
            self.fail_times = fail_times
            self.seen = 0

        async def complete(self, prompt: CompletionRequest):
            self.seen += 1
            if self.seen <= self.fail_times:
                raise ProviderError(
                    "provider_rate_limited",
                    "HTTP 429: rate limited",
                    http_status=429,
                    retry_after_seconds=0.05,
                )
            return await self.inner.complete(prompt)

    manifest_path = _mini_manifest(
        tmp_path,
        [
            {
                "id": "r_fail",
                "experiment": "E3_hero_comparison",
                "label": "Terminal 429",
                "architecture": "naive_chat",
                "model": "gemini-3.8-flash",
                "reasoning_effort": "high",
            },
            {
                "id": "r_retry_ok",
                "experiment": "E3_hero_comparison",
                "label": "Transient 429 recovered",
                "architecture": "naive_chat",
                "model": "gemini-3.8-flash",
                "reasoning_effort": "high",
            },
        ],
    )

    def factory(spec, _case, req):
        base = ReplayThptProvider(
            role="naive_chat", model=spec.model, request=req, naive_complete=True, naive_leak=False
        )
        # retries=1 in RecordingProvider: fail_times=2 fails terminally; fail_times=1 recovers.
        flaky = FlakyThenSuccess(base, fail_times=2 if spec.id == "r_fail" else 1)
        return {"naive_chat": flaky}

    out = tmp_path / "out_flaky"
    summary = asyncio.run(
        run_suite(manifest_path, out, mode="replay", compile_mode="skip", replay_factory=factory)
    )
    assert summary["total_recorded_attempts"] == 2
    assert summary["completed_attempts"] == 1
    assert summary["failed_attempts"] == 1

    rows = [
        json.loads(line)
        for line in (out / "attempts.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    by_id = {row["run_id"]: row for row in rows}
    assert by_id["r_fail"]["status"] == "failed"
    assert by_id["r_fail"]["template_pass"] is False
    assert by_id["r_retry_ok"]["status"] == "completed"
    assert by_id["r_retry_ok"]["template_pass"] is True
    assert by_id["r_retry_ok"]["rate_limit_wait_seconds"] == pytest.approx(0.05, abs=0.01)

    # --retry-failed re-runs only the failed attempt
    def healthy_factory(spec, _case, req):
        return {
            "naive_chat": ReplayThptProvider(
                role="naive_chat",
                model=spec.model,
                request=req,
                naive_complete=True,
                naive_leak=False,
            )
        }

    retried = asyncio.run(
        run_suite(
            manifest_path,
            out,
            mode="replay",
            resume=True,
            retry_failed=True,
            compile_mode="skip",
            replay_factory=healthy_factory,
        )
    )
    assert retried["executed_in_this_invocation"] == 1
    assert retried["skipped_on_resume"] == 1
    assert retried["completed_attempts"] == 2


def test_inspect_latex_template_detects_answer_leakage():
    leaked = (
        r"\documentclass{article}\begin{document}"
        "PHẦN I\n"
        + "\n".join(f"Câu {i}: Nội dung {i}." for i in range(1, 13))
        + "\nĐáp án: A\nPHẦN II\n"
        + "\n".join(f"Câu {i}: Nội dung {i}." for i in range(1, 5))
        + "\nPHẦN III\n"
        + "\n".join(f"Câu {i}: Nội dung {i}." for i in range(1, 7))
        + r"\end{document}"
    )
    result = inspect_latex_template(leaked, tex_path=None, compile_mode="skip")
    assert result["question_count_detected"] == 22
    assert result["zero_answer_leakage"] is False
    assert result["template_pass"] is False
