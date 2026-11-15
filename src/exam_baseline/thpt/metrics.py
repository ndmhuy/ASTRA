"""Reported-token cost estimates, never a claim about the user's actual billing tier."""

from collections import defaultdict

# Google Developer API Standard, verified 2026-11-07. USD per million tokens.
PRICES = {"gemini-3.1-flash-lite": (0.25, 1.50)}
SOURCE = "https://ai.google.dev/gemini-api/docs/pricing"


def summarize_calls(calls: list[dict]) -> dict:
    input_tokens = output_tokens = 0
    cost = 0.0
    incomplete = False
    stages = defaultdict(lambda: {"calls": 0, "api_seconds": 0.0})
    for call in calls:
        stage = stages[call["role"]]
        stage["calls"] += 1
        stage["api_seconds"] += call.get("latency_ms", 0) / 1000
        usage = call.get("usage", {})
        incoming, outgoing = usage.get("input_tokens"), usage.get("output_tokens")
        input_tokens += incoming or 0
        output_tokens += outgoing or 0
        prices = PRICES.get(call.get("model"))
        if incoming is None or outgoing is None or prices is None:
            incomplete = True
        else:
            cost += (incoming * prices[0] + outgoing * prices[1]) / 1_000_000
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "api_seconds_sum": round(sum(s["api_seconds"] for s in stages.values()), 3),
        "by_stage": {
            name: {**s, "api_seconds": round(s["api_seconds"], 3)} for name, s in stages.items()
        },
        "standard_price_estimate_usd": round(cost, 8),
        "estimate_complete": not incomplete,
        "billing_tier": "unknown",
        "pricing_verified_on": "2026-11-07",
        "pricing_source": SOURCE,
        "note": "Estimate from reported tokens only; retries included when usage is available. "
        "Not an invoice. Free-tier eligible usage has no token charge within quota. "
        "API time sum may exceed elapsed time when calls overlap.",
    }
