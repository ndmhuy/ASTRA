import pytest

from exam_baseline.thpt.metrics import summarize_calls


def test_actual_recorded_exam_standard_price():
    metrics = summarize_calls(
        [
            {
                "role": "composer",
                "latency_ms": 36009,
                "model": "gemini-3.1-flash-lite",
                "usage": {"input_tokens": 30499, "output_tokens": 11288},
            }
        ]
    )
    assert metrics["standard_price_estimate_usd"] == pytest.approx(0.02455675)
    assert metrics["billing_tier"] == "unknown"
    assert metrics["estimate_complete"]


def test_missing_usage_or_unpriced_model_is_not_reported_as_complete():
    metrics = summarize_calls(
        [
            {"role": "composer", "latency_ms": 500, "status": "failed"},
            {
                "role": "solver",
                "model": "unknown",
                "usage": {"input_tokens": 10, "output_tokens": 20},
            },
        ]
    )
    assert not metrics["estimate_complete"]
    assert metrics["standard_price_estimate_usd"] == 0
    assert metrics["input_tokens"] == 10
