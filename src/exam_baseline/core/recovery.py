"""Shared bounded transport policy; academic repair remains owned by each Agent."""

import json
import random
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path

POLICY = json.loads(
    (Path(__file__).parents[1] / "resources/agent/recovery-policy.json").read_text("utf-8")
)
OPERATION = ContextVar("astra_provider_operation", default=None)


@dataclass(frozen=True)
class Failure:
    category: str
    retryable: bool = False
    recoverable: bool = False
    uncertain: bool = False


def classify(error) -> Failure:
    code = error.code
    if code in {"provider_quota_exhausted", "spend_limit_exceeded"}:
        return Failure("quota_exhausted")
    if code in {"provider_auth_error", "provider_access_denied"}:
        return Failure("authentication")
    if code in {"provider_not_found", "model_not_configured"}:
        return Failure("unsupported_model")
    if code in {"provider_bad_request", "vision_required"}:
        return Failure("invalid_request")
    if code in {"provider_timeout", "provider_gateway_timeout", "provider_unreachable"}:
        return Failure("uncertain_transport", recoverable=True, uncertain=True)
    if code in {"provider_connect_timeout", "provider_connection_failed"}:
        return Failure("connection", retryable=True, recoverable=True)
    if code in {"provider_rate_limited", "provider_capacity"}:
        return Failure("rate_limit", retryable=error.retryable is not False, recoverable=True)
    if code in {
        "provider_protocol_error",
        "provider_invalid_response",
        "provider_failure_unclassified",
    }:
        return Failure("unclassified_response", recoverable=True)
    if error.http_status in {500, 502, 503}:
        return Failure(
            "temporary_provider", retryable=error.retryable is not False, recoverable=True
        )
    return Failure("permanent_configuration")


def delay(attempt, retry_after, policy, *, jitter=random.random):
    exponential = min(policy["maxDelaySeconds"], policy["baseDelaySeconds"] * 2**attempt)
    # Positive jitter avoids synchronized restarts; Retry-After is never shortened.
    value = exponential * (0.5 + 0.5 * jitter())
    return max(value, retry_after or 0)


def daily_quota(error, depth=0):
    if not isinstance(error, dict) or depth > 8:
        return False
    if isinstance(error.get("code"), str) and error["code"] in {
        "insufficient_quota",
        "billing_hard_limit_reached",
        "provider_quota_exhausted",
    }:
        return True
    for key, value in error.items():
        if key in {
            "quotaId",
            "quota_id",
            "quotaMetric",
            "quota_metric",
            "quotaLimit",
            "quota_limit",
        }:
            folded = "".join(c for c in str(value).lower() if c.isalnum())
            if "perday" in folded or "daily" in folded:
                return True
        if isinstance(value, dict) and daily_quota(value, depth + 1):
            return True
        if isinstance(value, list) and any(daily_quota(item, depth + 1) for item in value):
            return True
    return False
