import asyncio
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest
from pydantic import ValidationError

from exam_baseline.config import Settings
from exam_baseline.core.contracts import CompletionRequest, ProviderError
from exam_baseline.core.models import TokenUsage
from exam_baseline.pipeline.bootstrap import stage_settings
from exam_baseline.pipeline.contracts import StageConfig
from exam_baseline.providers.budget import SpendLedger
from exam_baseline.providers.chat_completions import ChatCompletionsProvider
from tests.providers.test_chat_completions import envelope


def settings(tmp_path, **overrides):
    return Settings.for_offline().model_copy(
        update={
            "input_price_per_million": 1,
            "output_price_per_million": 5,
            "spend_limit_usd": 0.003,
            "spend_ledger": tmp_path / "spend.sqlite3",
            "max_output_tokens": 100,
            **overrides,
        }
    )


def test_atomic_reservations_prevent_concurrent_overspend_and_survive_restart(tmp_path):
    config = settings(tmp_path)

    def reserve(_):
        try:
            return SpendLedger(config).reserve({}, 100)
        except ProviderError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(reserve, range(2)))
    assert outcomes.count("spend_limit_exceeded") == 1
    ledger = SpendLedger(config)
    assert ledger.snapshot()["reservedUsd"] > 0
    reservation = next(value for value in outcomes if value != "spend_limit_exceeded")
    ledger.settle(reservation, TokenUsage(input_tokens=100, output_tokens=20))
    assert SpendLedger(config).snapshot()["reportedUsd"] == pytest.approx(0.0002)


@pytest.mark.parametrize(
    "failure", ["success", "unknown_usage", "timeout", "connect_timeout", "401", "503"]
)
def test_adapter_settles_usage_and_keeps_uncertain_costs(tmp_path, failure):
    async def run():
        def handler(request):
            if failure == "connect_timeout":
                raise httpx.ConnectTimeout("not connected", request=request)
            if failure == "timeout":
                raise httpx.ReadTimeout("unknown outcome", request=request)
            if failure in {"401", "503"}:
                return httpx.Response(int(failure))
            return httpx.Response(
                200,
                json=envelope(
                    usage=None
                    if failure == "unknown_usage"
                    else {
                        "prompt_tokens": 100,
                        "completion_tokens": 20,
                    },
                ),
            )

        config = settings(tmp_path)
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = ChatCompletionsProvider(config, client)
            request = CompletionRequest("s", "u", {})
            if failure in {"timeout", "connect_timeout", "401", "503"}:
                with pytest.raises(ProviderError):
                    await provider.complete(request)
            else:
                await provider.complete(request)
        summary = SpendLedger(config).snapshot()
        if failure == "success":
            assert summary["reportedUsd"] == pytest.approx(0.0002)
            assert summary["reservedUsd"] == 0
        elif failure == "connect_timeout":
            assert summary["remainingUsd"] == 0.003
        else:
            assert summary["reservedUsd"] == summary["unknownUsd"] > 0
            with pytest.raises(ProviderError, match="ASTRA"):
                SpendLedger(config).reserve({}, 100)

    asyncio.run(run())


def test_oversized_request_is_blocked_before_http_and_strict_schema_is_forwarded(tmp_path):
    async def run():
        calls = []

        def handler(request):
            import json

            payload = json.loads(request.content)
            assert payload["response_format"]["json_schema"]["strict"] is True
            calls.append(request)
            return httpx.Response(200, json=envelope())

        config = settings(tmp_path, response_format="json_schema", structured_output_strict=True)
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = ChatCompletionsProvider(config, client)
            with pytest.raises(ProviderError) as error:
                await provider.complete(CompletionRequest("s", "x" * 10000, {}))
            assert error.value.code == "spend_limit_exceeded" and not calls
            await provider.complete(CompletionRequest("s", "u", {}))
            assert len(calls) == 1

    asyncio.run(run())


def test_budget_prices_are_required_and_teacher_cannot_override_them(tmp_path):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, provider="mock", spend_limit_usd=5)
    with pytest.raises(ValueError, match="locks"):
        stage_settings(
            settings(tmp_path), StageConfig(input_price_per_million=0, output_price_per_million=0)
        )
