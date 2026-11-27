import pytest

from exam_baseline.thpt.metrics import summarize_calls, usd_to_vnd


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
    assert metrics["standard_price_estimate_vnd"] == pytest.approx(usd_to_vnd(0.02455675))
    assert metrics["cost_coverage"] == 1.0
    assert metrics["billing_tier"] == "unknown"
    assert metrics["estimate_complete"]


def test_gemini_25_and_38_pricing_and_retry_wait_separation():
    metrics = summarize_calls(
        [
            {
                "role": "composer",
                "latency_ms": 1200,
                "retry_wait_ms": 4500,
                "model": "models/gemini-2.5-flash-lite",
                "usage": {"input_tokens": 100_000, "output_tokens": 25_000},
            },
            {
                "role": "solver",
                "latency_ms": 2300,
                "model": "gemini-3.8-flash",
                "usage": {"input_tokens": 20_000, "output_tokens": 4_000},
            },
        ],
        usd_to_vnd_rate=25_000,
    )
    # 2.5: (0.1*0.10 + 0.025*0.40) = 0.02; 3.8: (0.02*0.75 + 0.004*3.75) = 0.03
    assert metrics["standard_price_estimate_usd"] == pytest.approx(0.05)
    assert metrics["standard_price_estimate_vnd"] == pytest.approx(1250.0)
    assert metrics["api_seconds_sum"] == pytest.approx(3.5)
    assert metrics["retry_wait_seconds"] == pytest.approx(4.5)
    assert metrics["cost_coverage"] == 1.0
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
    assert metrics["cost_coverage"] == 0.0
    assert metrics["standard_price_estimate_usd"] == 0
    assert metrics["input_tokens"] == 10


def test_haiku_report_uses_its_actual_price_source():
    metrics = summarize_calls(
        [
            {
                "role": "composer",
                "model": "claude-haiku-4-5-20251001",
                "usage": {"input_tokens": 1104, "output_tokens": 164},
            }
        ]
    )
    assert metrics["standard_price_estimate_usd"] == pytest.approx(0.001924)
    assert metrics["estimate_complete"]
    assert "claude.com" in metrics["pricing_source"]
