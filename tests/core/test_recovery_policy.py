"""Classification and retry ownership with fake HTTP and providers only."""

import asyncio
from uuid import uuid4

import httpx
import pytest

from exam_baseline.agent.contracts import Decision
from exam_baseline.agent.provider import ProviderFailure, ProviderRouter, Timing
from exam_baseline.config import Settings
from exam_baseline.core.contracts import Completion, CompletionRequest, ProviderError
from exam_baseline.core.recovery import POLICY, classify, delay
from exam_baseline.providers.chat_completions import ChatCompletionsProvider
from exam_baseline.thpt.runtime import RecordingProvider


@pytest.mark.parametrize(
    ("status", "error", "headers", "category", "retry"),
    [
        (401, {}, {}, "authentication", False),
        (404, {}, {}, "unsupported_model", False),
        (400, {}, {}, "invalid_request", False),
        (503, {}, {}, "temporary_provider", True),
        (429, {"code": "rate_limit_exceeded"}, {"Retry-After": "2"}, "rate_limit", True),
        (429, {"code": "insufficient_quota"}, {}, "quota_exhausted", False),
        (
            429,
            {"details": [{"violations": [{"quotaId": "RequestsPerDayPerModel"}]}]},
            {},
            "quota_exhausted",
            False,
        ),
        (429, {}, {}, "rate_limit", False),
        (
            502,
            {"type": "astra_mas_error", "code": "upstream_failed"},
            {},
            "unclassified_response",
            False,
        ),
    ],
)
def test_http_adapter_preserves_failure_categories_without_own_retries(
    status, error, headers, category, retry
):
    observed = []

    def handler(request):
        observed.append(request)
        return httpx.Response(status, json={"error": error}, headers=headers)

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = ChatCompletionsProvider(Settings.for_offline(), client)
            with pytest.raises(ProviderError) as caught:
                await provider.complete(CompletionRequest("fixture", "fixture", {}))
            result = classify(caught.value)
            assert (result.category, result.retryable) == (category, retry)

    asyncio.run(run())
    assert len(observed) == 1


def test_retry_records_two_attempts_one_operation_and_respects_backoff(tmp_path, monkeypatch):
    waits = []

    async def sleep(value):
        waits.append(value)

    class Fake:
        calls = 0

        async def complete(self, request):
            self.calls += 1
            if self.calls == 1:
                raise ProviderError(
                    "provider_unavailable", "fixture", http_status=503, retry_after_seconds=2
                )
            return Completion("{}", "fixture")

    monkeypatch.setattr("exam_baseline.thpt.runtime.asyncio.sleep", sleep)
    records = []
    fake = Fake()
    asyncio.run(
        RecordingProvider(
            fake, "composer", 1, records, tmp_path, retries=10, operation_id="a" * 64
        ).complete(CompletionRequest("", "", {}))
    )
    assert fake.calls == 2 and waits == [2]
    assert len({record["attempt_id"] for record in records}) == 2
    assert {record["operation_id"] for record in records} == {"a" * 64}
    assert delay(2, 5, POLICY["mas"], jitter=lambda: 0) >= 5


def test_operation_deadline_bounds_inflight_work_without_automatic_replay(tmp_path, monkeypatch):
    monkeypatch.setitem(POLICY["mas"], "deadlineSeconds", 0.02)

    class Slow:
        calls = 0

        async def complete(self, request):
            self.calls += 1
            await asyncio.sleep(10)

    provider, records = Slow(), []
    with pytest.raises(ProviderError) as caught:
        asyncio.run(
            RecordingProvider(provider, "composer", 1, records, tmp_path, retries=1).complete(
                CompletionRequest("", "", {})
            )
        )
    assert classify(caught.value).uncertain and not classify(caught.value).retryable
    assert provider.calls == len(records) == 1
    assert records[0]["outcome_uncertain"] is True


@pytest.mark.parametrize("safe", [False, True])
def test_chat_retries_only_when_no_admitted_inference_can_have_occurred(safe, monkeypatch):
    class Fake:
        calls = 0

        async def interpret(self, turn, timeout):
            self.calls += 1
            if self.calls == 1:
                raise ProviderFailure("transient", safe_retry=safe)
            return Decision(kind="answer")

    monkeypatch.setitem(POLICY["chat"], "baseDelaySeconds", 0)
    primary, attempts = Fake(), []
    router = ProviderRouter(
        primary,
        reserve=lambda: attempts.append(str(uuid4())) or True,
        timing=Timing(primary=1, total=2),
    )
    result = asyncio.run(router(None))
    assert primary.calls == len(attempts) == (2 if safe else 1)
    assert result.kind == ("answer" if safe else "temporarily_unavailable")
