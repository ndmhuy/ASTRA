"""Isolated THPT Math Validator Seeded Defect Suite.

Evaluates ASTRA's validation stack (Blind Solver + deterministic answer comparison +
answer-leakage check + Reviewer) on clean THPT items and seeded defects.
Evaluator gold and replay fixtures NEVER enter Solver or Reviewer prompts.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
from collections import defaultdict
from pathlib import Path
from time import perf_counter
from typing import Literal

import httpx
from pydantic import Field, model_validator

from exam_baseline.config import Settings
from exam_baseline.core.contracts import Completion, CompletionRequest, LLMProvider, ProviderError
from exam_baseline.core.models import Model, Text, TokenUsage
from exam_baseline.providers.chat_completions import ChatCompletionsProvider
from exam_baseline.thpt.agents import ReviewerAgent, SolverAgent
from exam_baseline.thpt.metrics import DEFAULT_USD_TO_VND, summarize_calls
from exam_baseline.thpt.models import Question
from exam_baseline.thpt.orchestrator import compare_answer
from exam_baseline.thpt.rendering import student_view
from exam_baseline.thpt.runtime import ContractError, RecordingProvider

_LEAKAGE_PATTERN = re.compile(
    r"(?:đáp\s*án|lời\s*giải|hướng\s*dẫn\s*giải)\s*[:.]",
    flags=re.IGNORECASE,
)


class SingleQuestionReview(Model):
    decision: Literal["approved", "needs_revision"]
    checked_ids: list[str] = Field(min_length=1, max_length=1)
    issues: list[Text] = Field(default_factory=list)

    @model_validator(mode="after")
    def consistent(self):
        if (self.decision == "needs_revision") != bool(self.issues):
            raise ValueError("needs_revision requires actionable issues; approved requires none")
        return self


class SingleItemReviewerAgent(ReviewerAgent):
    response = SingleQuestionReview


class ReplayCaseProvider:
    name = "replay_validator"

    def __init__(self, payload: dict, model: str):
        self.payload = payload
        self.model = model

    async def complete(self, _request: CompletionRequest) -> Completion:
        return Completion(
            text=json.dumps(self.payload, ensure_ascii=False),
            model=self.model,
            usage=TokenUsage(input_tokens=600, output_tokens=180),
        )


def has_student_leakage(question: Question, student_latex: str) -> bool:
    student_texts = [
        question.stem,
        *question.choices.values(),
        *(s.text for s in question.statements),
        student_latex,
    ]
    return any(_LEAKAGE_PATTERN.search(text) for text in student_texts)


async def evaluate_validator_case(
    case: dict,
    solver_provider: LLMProvider,
    reviewer_provider: LLMProvider,
    work_dir: Path,
) -> dict:
    """Run Blind Solver + deterministic checks + Reviewer on one THPT case.

    Explicit allowlist: `case['gold']` and `case['replay']` NEVER enter any packet.
    """
    question = Question.model_validate(case["question"])
    calls: list[dict] = []
    started = perf_counter()

    solver = SolverAgent()
    reviewer = SingleItemReviewerAgent()

    solver_entry = None
    review_dump = None
    error = None
    caught_by_solver = False
    caught_by_reviewer = False
    caught_by_leak_check = has_student_leakage(question, case["student_latex"])
    issues: list[str] = []

    if caught_by_leak_check:
        issues.append(
            f"{question.id}: Deterministic check detected answer leakage in student text."
        )

    try:
        solver_recorder = RecordingProvider(
            solver_provider, "solver", 1, calls, work_dir / case["id"], retries=1
        )
        # Strict blind view: NO composer answer, NO composer solution, NO gold.
        solver_packet = {
            "questions": student_view([question]),
            "drawings": {"drawings": []},
        }
        solutions, _ = await solver.run(solver_recorder, solver_packet)
        solver_entry = solutions.entries[0].model_dump()

        check, mismatch = compare_answer(question.model_dump(), solver_entry)
        if solver_entry["status"] != "solved":
            caught_by_solver = True
            issues.append(f"{question.id}: Blind Solver marked question {solver_entry['status']}.")
        elif check == "mismatched" and mismatch is not None:
            caught_by_solver = True
            issues.append(
                f"{question.id}: Composer key ({mismatch['composer']}) "
                f"disagrees with Blind Solver ({mismatch['solver']})."
            )

        reviewer_recorder = RecordingProvider(
            reviewer_provider, "reviewer", 1, calls, work_dir / case["id"], retries=0
        )
        # Strict allowlist: NEVER include case['gold'] or case['replay'].
        review_packet = {
            "matrix": {
                "slots": [case["slot"]],
                "requirements": case.get("requirements", []),
            },
            "questions": [question.model_dump()],
            "drawings": {"drawings": []},
            "solver": solutions.model_dump(),
            "student_latex": case["student_latex"],
            "rag_scope": {question.id: case["rag_scope"]},
        }
        review, _ = await reviewer.run(reviewer_recorder, review_packet)
        review_dump = review.model_dump()
        if review.decision == "needs_revision":
            caught_by_reviewer = True
            issues.extend(review.issues)
    except (ProviderError, ContractError, ValueError) as exc:
        error = str(exc)

    final_decision: str | None
    if error is not None and not issues:
        final_decision = None
    elif issues or caught_by_solver or caught_by_reviewer or caught_by_leak_check:
        final_decision = "needs_revision"
    else:
        final_decision = "approved"

    return {
        "case_id": case["id"],
        "category": case["category"],
        "final_decision": final_decision,
        "caught_by_solver": caught_by_solver,
        "caught_by_reviewer": caught_by_reviewer,
        "caught_by_leak_check": caught_by_leak_check,
        "issues": issues,
        "solver": solver_entry,
        "reviewer": review_dump,
        "calls": calls,
        "wall_seconds": round(perf_counter() - started, 3),
        "error": error,
    }


def score_validator_attempts(
    cases: list[dict],
    attempts: list[dict],
    *,
    usd_to_vnd_rate: float = DEFAULT_USD_TO_VND,
) -> dict:
    tp = fp = fn = tn = errors = 0
    clean_total = defect_total = 0
    by_category: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "flagged": 0})
    all_calls: list[dict] = []

    for case, attempt in zip(cases, attempts, strict=True):
        gold_defect = bool(case["gold"]["has_defect"])
        decision = attempt["final_decision"]
        flagged = decision == "needs_revision"
        cat = by_category[case["category"]]
        cat["total"] += 1
        cat["flagged"] += int(flagged)
        all_calls.extend(attempt.get("calls", []))

        if decision is None:
            errors += 1
        if gold_defect:
            defect_total += 1
            if flagged:
                tp += 1
            else:
                fn += 1
        else:
            clean_total += 1
            if flagged:
                fp += 1
            elif decision == "approved":
                tn += 1

    call_metrics = summarize_calls(all_calls, usd_to_vnd_rate=usd_to_vnd_rate)
    return {
        "total_cases": len(cases),
        "defect_cases": defect_total,
        "clean_cases": clean_total,
        "errors": errors,
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
        "recall": round(tp / (tp + fn), 4) if (tp + fn) else None,
        "precision": round(tp / (tp + fp), 4) if (tp + fp) else None,
        "clean_false_alarm_rate": round(fp / clean_total, 4) if clean_total else None,
        "clean_retention": round(tn / clean_total, 4) if clean_total else None,
        "caught_by_solver_count": sum(1 for a in attempts if a["caught_by_solver"]),
        "caught_by_reviewer_count": sum(1 for a in attempts if a["caught_by_reviewer"]),
        "caught_by_leak_check_count": sum(1 for a in attempts if a["caught_by_leak_check"]),
        "by_category": dict(by_category),
        "cost_usd": call_metrics["standard_price_estimate_usd"],
        "cost_vnd": call_metrics["standard_price_estimate_vnd"],
        "cost_coverage": call_metrics["cost_coverage"],
        "api_compute_seconds": call_metrics["api_seconds_sum"],
        "rate_limit_wait_seconds": call_metrics["retry_wait_seconds"],
        "wall_seconds": round(sum(a["wall_seconds"] for a in attempts), 3),
    }


async def run_validator_suite(
    dataset_path: Path,
    output: Path,
    *,
    mode: Literal["replay", "live"] = "replay",
    model: str | None = None,
    reasoning_effort: Literal["none", "minimal", "low", "medium", "high", "xhigh"] | None = None,
    base_settings: Settings | None = None,
) -> dict:
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    if output.exists():
        raise ValueError("output directory already exists")
    output.mkdir(parents=True)
    work_dir = output / "_responses"

    attempts = []
    if mode == "replay":
        replay_model = model or "gemini-2.5-flash-lite"
        for case in dataset["cases"]:
            solver_p = ReplayCaseProvider(case["replay"]["solver"], replay_model)
            reviewer_p = ReplayCaseProvider(case["replay"]["reviewer"], replay_model)
            attempts.append(await evaluate_validator_case(case, solver_p, reviewer_p, work_dir))
    else:
        settings = base_settings or Settings()
        if settings.provider != "chat_completions":
            raise ValueError("Live validator suite requires EXAM_PROVIDER=chat_completions in .env")
        updates: dict = {}
        if model:
            updates["model"] = model
        if reasoning_effort is not None:
            updates["reasoning_effort"] = reasoning_effort
        settings = settings.model_copy(update=updates).for_agent_generation()
        async with httpx.AsyncClient(follow_redirects=False) as client:
            provider = ChatCompletionsProvider(settings, client)
            for case in dataset["cases"]:
                attempts.append(await evaluate_validator_case(case, provider, provider, work_dir))

    report = {
        "schema_version": dataset.get("schema_version", "thpt-validator-v1"),
        "name": dataset["name"],
        "mode": mode,
        "model": model or ("gemini-2.5-flash-lite" if mode == "replay" else None),
        "reasoning_effort": reasoning_effort,
        "metrics": score_validator_attempts(dataset["cases"], attempts),
        "note": (
            "Replay verifies validator scoring and anti-leakage plumbing ONLY; "
            "not a live model Recall/Precision claim."
            if mode == "replay"
            else "Live Recall/Precision measured on seeded THPT defects; "
            "errors stay in denominator."
        ),
    }
    (output / "validator_attempts.json").write_text(
        json.dumps(attempts, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output / "validator_metrics.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("examples/benchmarks/thpt_validator_suite.json"),
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=("replay", "live"), default="replay")
    parser.add_argument("--model", default=None)
    parser.add_argument(
        "--reasoning-effort",
        choices=("none", "minimal", "low", "medium", "high", "xhigh"),
        default=None,
    )
    args = parser.parse_args()
    result = asyncio.run(
        run_validator_suite(
            args.dataset,
            args.output,
            mode=args.mode,
            model=args.model,
            reasoning_effort=args.reasoning_effort,
        )
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
