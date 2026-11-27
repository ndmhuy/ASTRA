"""Provider policy tests use injected clocks and inference fixtures."""

import asyncio

import pytest

from exam_baseline.agent.contracts import VERSION, Decision, Turn
from exam_baseline.agent.provider import ProviderFailure, ProviderRouter, Timing

TURN = Turn(
    schemaVersion=VERSION,
    clientMessageId="a" * 36,
    workspaceId="b" * 36,
    message="Mở phần cấu hình",
    context={"screen": "workspace", "setup": False},
)


class Fake:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    async def interpret(self, _turn, _timeout):
        self.calls += 1
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def test_one_fallback_and_refusal_when_daily_budget_is_exhausted():
    first = Fake(ProviderFailure("transient"))
    second = Fake(Decision(kind="clarify"))
    permits = iter([True, True, False])
    router = ProviderRouter(first, fallback=second, reserve=lambda: next(permits))

    async def scenario():
        assert (await router(TURN)).kind == "clarify"
        assert (await router(TURN)).reasonCode == "budget"

    asyncio.run(scenario())
    assert first.calls == second.calls == 1


@pytest.mark.parametrize("reason", ["configuration", "schema", "quota"])
def test_auth_schema_and_429_cooldown_do_not_trigger_fallback(reason):
    clock = [0.0]
    first = Fake(ProviderFailure(reason, retry_after=45))
    second = Fake(Decision(kind="clarify"))
    router = ProviderRouter(first, fallback=second, reserve=lambda: True, clock=lambda: clock[0])

    async def scenario():
        assert (await router(TURN)).reasonCode == reason
        clock[0] = 10
        assert (await router(TURN)).reasonCode == reason
        assert first.calls == 1
        assert second.calls == 0

    asyncio.run(scenario())


def test_late_primary_result_cannot_supplant_fallback():
    class Late:
        async def interpret(self, _turn, _timeout):
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                await asyncio.sleep(0.02)
                return Decision(kind="unsupported")

    second = Fake(Decision(kind="clarify"))
    router = ProviderRouter(
        Late(),
        fallback=second,
        reserve=lambda: True,
        timing=Timing(primary=0.01, total=0.1, minimum_fallback=0.001),
    )

    async def scenario():
        assert (await router(TURN)).kind == "clarify"
        await asyncio.sleep(0.04)
        assert second.calls == 1

    asyncio.run(scenario())
