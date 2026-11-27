"""Reported-token cost estimates, never a claim about the user's actual billing tier."""

from collections import defaultdict

DEFAULT_USD_TO_VND = 26_000.0

# Standard API token rates (USD per million input / output tokens).
# gemini-3.8-flash reflects the promotional rate through 2026-12-31 ($1.50/$7.50 from 2027-01-01).
PRICES = {
    "gemini-2.5-flash-lite": (0.10, 0.40),
    "gemini-3.1-flash-lite": (0.25, 1.50),
    "gemini-3.8-flash": (0.75, 3.75),
    "claude-haiku-4-5-20251001": (1.00, 5.00),
}
PRICE_VERIFIED_ON = {
    "gemini-2.5-flash-lite": "2026-11-27",
    "gemini-3.1-flash-lite": "2026-11-07",
    "gemini-3.8-flash": "2026-11-27",
    "claude-haiku-4-5-20251001": "2026-11-18",
}
SOURCE = "https://ai.google.dev/gemini-api/docs/pricing"
CLAUDE_SOURCE = "https://platform.claude.com/docs/en/about-claude/pricing"


def canonical_model_name(model: str | None) -> str | None:
    if not isinstance(model, str) or not model.strip():
        return None
    normalized = model.strip()
    if normalized.startswith("models/"):
        normalized = normalized[len("models/") :]
    return normalized


def resolve_model_price(model: str | None) -> tuple[float, float] | None:
    canonical = canonical_model_name(model)
    if canonical is None:
        return None
    return PRICES.get(canonical)


def usd_to_vnd(usd: float, rate: float = DEFAULT_USD_TO_VND) -> float:
    return round(usd * rate, 2)


def summarize_calls(calls: list[dict], *, usd_to_vnd_rate: float = DEFAULT_USD_TO_VND) -> dict:
    input_tokens = output_tokens = 0
    cost = 0.0
    incomplete = False
    priced_calls = 0
    retry_wait_seconds = 0.0
    stages = defaultdict(lambda: {"calls": 0, "api_seconds": 0.0, "retry_wait_seconds": 0.0})
    seen_models: set[str] = set()
    for call in calls:
        stage = stages[call["role"]]
        stage["calls"] += 1
        stage["api_seconds"] += call.get("latency_ms", 0) / 1000
        wait_s = call.get("retry_wait_ms", 0) / 1000
        stage["retry_wait_seconds"] += wait_s
        retry_wait_seconds += wait_s
        usage = call.get("usage", {})
        incoming, outgoing = usage.get("input_tokens"), usage.get("output_tokens")
        input_tokens += incoming or 0
        output_tokens += outgoing or 0
        canonical = canonical_model_name(call.get("model"))
        prices = PRICES.get(canonical) if canonical else None
        if incoming is None or outgoing is None or prices is None:
            incomplete = True
        else:
            priced_calls += 1
            seen_models.add(canonical)
            cost += (incoming * prices[0] + outgoing * prices[1]) / 1_000_000
    models = sorted(seen_models)
    sources = [
        {
            "model": model,
            "source": CLAUDE_SOURCE if model.startswith("claude-") else SOURCE,
            "verified_on": PRICE_VERIFIED_ON.get(model, "2026-11-27"),
        }
        for model in models
    ]
    total_calls = len(calls)
    cost_coverage = round(priced_calls / total_calls, 4) if total_calls else 0.0
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "api_seconds_sum": round(sum(s["api_seconds"] for s in stages.values()), 3),
        "retry_wait_seconds": round(retry_wait_seconds, 3),
        "by_stage": {
            name: {
                "calls": s["calls"],
                "api_seconds": round(s["api_seconds"], 3),
                "retry_wait_seconds": round(s["retry_wait_seconds"], 3),
            }
            for name, s in stages.items()
        },
        "standard_price_estimate_usd": round(cost, 8),
        "standard_price_estimate_vnd": usd_to_vnd(cost, usd_to_vnd_rate),
        "usd_to_vnd_rate": usd_to_vnd_rate,
        "cost_coverage": cost_coverage,
        "estimate_complete": not incomplete,
        "billing_tier": "unknown",
        "pricing_verified_on": max((s["verified_on"] for s in sources), default="2026-11-27"),
        "pricing_source": sources[0]["source"] if len(sources) == 1 else SOURCE,
        "pricing_sources": sources,
        "note": "Estimate from reported tokens only; retries included when usage is available. "
        "Not an invoice. Free-tier eligible usage has no token charge within quota. "
        "API time sum may exceed elapsed time when calls overlap.",
    }
