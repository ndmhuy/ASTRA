import statistics

from exam_baseline.benchmarks.models import HumanLabel


def summarize(attempts: list[dict], labels: dict[str, HumanLabel]) -> dict:
    """All scheduled attempts remain denominators. Missing human/usage data is unknown."""
    result = {}
    if set(labels) - {a["attempt_id"] for a in attempts}:
        raise ValueError("human annotations reference unknown attempt IDs")
    for key in sorted({(a["system"], a["track"]) for a in attempts}):
        group = [a for a in attempts if (a["system"], a["track"]) == key]
        audited = [(a, labels[a["attempt_id"]]) for a in group if a["attempt_id"] in labels]
        for attempt, label in audited:
            if (
                label.requested_questions != attempt["requested_questions"]
                or label.correct_questions > label.requested_questions
                or label.usable_figures > label.required_figures
                or label.true_positive_defects > min(label.gold_defects, label.predicted_defects)
            ):
                raise ValueError("human annotation denominator/count mismatch")
        denominator = sum(label.requested_questions for _, label in audited)
        # Failed/no-artifact attempts cannot contribute correct questions, even if mislabeled.
        correct = sum(label.correct_questions for a, label in audited if a["artifact_returned"])
        required = sum(label.required_figures for _, label in audited)
        useful = sum(label.usable_figures for a, label in audited if a["artifact_returned"])
        gold = sum(label.gold_defects for _, label in audited)
        tp = sum(label.true_positive_defects for _, label in audited)
        predicted = sum(label.predicted_defects for _, label in audited)
        clean = sum(label.clean_case for _, label in audited)
        latencies = [a["latency_ms"] for a in group]
        calls = sum(a["calls"] for a in group)
        cost_calls = sum(a["known_cost_calls"] for a in group)
        result["/".join(key)] = {
            "scheduled_attempts": len(group),
            "failures": sum(a["status"] == "failed" for a in group),
            "unsupported_attempts": sum(a["status"] == "unsupported" for a in group),
            "matrix_full_pass_rate": sum(a["deterministic_passed"] for a in group) / len(group),
            "machine_accepted_rate": sum(a["accepted"] for a in group) / len(group),
            "human_audited_attempts": len(audited),
            "human_audit_coverage": len(audited) / len(group),
            "correct_question_yield": correct / denominator if denominator else None,
            "useful_figure_rate": useful / required if required else None,
            "reviewer_defect_recall": tp / gold if gold else None,
            "reviewer_issue_precision": tp / predicted if predicted else None,
            "reviewer_clean_false_alarm_rate": (
                sum(label.clean_case and label.false_alarm for _, label in audited) / clean
                if clean
                else None
            ),
            "latency_median_ms": statistics.median(latencies),
            "latency_max_ms": max(latencies),
            "provider_calls": calls,
            "known_input_tokens": sum(a["input_tokens"] for a in group),
            "known_output_tokens": sum(a["output_tokens"] for a in group),
            "usage_unknown_calls": sum(a["usage_unknown_calls"] for a in group),
            "known_cost_subtotal_usd": sum(a["known_cost_usd"] for a in group),
            "cost_coverage": cost_calls / calls if calls else None,
            "total_cost_usd": (
                sum(a["known_cost_usd"] for a in group) if calls and calls == cost_calls else None
            ),
        }
    return result
