"""Deadline and fallback policy for conversational interpretation."""

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from .contracts import Decision, Turn

logger = logging.getLogger(__name__)


class ProviderFailure(Exception):
    def __init__(self, reason: str, retry_after: float | None = None):
        super().__init__(reason)
        self.reason = reason
        self.retry_after = retry_after


class InterpretationProvider(Protocol):
    async def interpret(self, turn: Turn, timeout: float) -> Decision: ...


@dataclass(frozen=True)
class Timing:
    primary: float = 1.8
    total: float = 4.0
    cooldown: float = 20.0
    minimum_fallback: float = 0.2


@dataclass
class Route:
    provider: InterpretationProvider
    until: float = 0.0
    failures: int = 0
    reason: str = "transient"


def discard_result(task: asyncio.Task) -> None:
    if not task.cancelled():
        task.exception()


class ProviderRouter:
    def __init__(
        self,
        primary: InterpretationProvider,
        *,
        reserve: Callable[[], bool],
        fallback: InterpretationProvider | None = None,
        timing: Timing | None = None,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.routes = [Route(primary)] + ([Route(fallback)] if fallback else [])
        self.reserve = reserve
        self.timing = timing or Timing()
        self.clock = clock

    async def __call__(self, turn: Turn) -> Decision:
        started = self.clock()
        reason = "transient"
        attempts = 0
        for index, route in enumerate(self.routes):
            now = self.clock()
            if route.until > now:
                reason = route.reason
                if reason != "transient":
                    break
                continue
            remaining = started + self.timing.total - now
            if remaining <= (self.timing.minimum_fallback if index else 0):
                break
            if not self.reserve():
                reason = "budget"
                break
            attempts += 1
            deadline = min(remaining, self.timing.primary) if index == 0 else remaining
            try:
                result = await self._within(route, turn, deadline)
            except ProviderFailure as exc:
                reason = exc.reason
                self._record_failure(route, exc)
                self._measure(started, attempts, reason)
                if reason != "transient":
                    break
            else:
                route.failures = 0
                route.until = 0
                self._measure(started, attempts, "valid")
                return result
        return Decision(kind="temporarily_unavailable", reasonCode=reason)

    async def _within(self, route: Route, turn: Turn, deadline: float) -> Decision:
        task = asyncio.create_task(route.provider.interpret(turn, deadline))
        try:
            done, _ = await asyncio.wait({task}, timeout=deadline)
            if task in done:
                return task.result()
            raise ProviderFailure("transient")
        finally:
            if not task.done():
                task.add_done_callback(discard_result)
                task.cancel()

    def _record_failure(self, route: Route, error: ProviderFailure) -> None:
        route.reason = error.reason
        route.failures += 1
        if error.reason == "quota":
            route.until = self.clock() + max(1.0, error.retry_after or self.timing.cooldown)
        elif error.reason in {"configuration", "schema"} or route.failures >= 2:
            route.until = self.clock() + self.timing.cooldown

    def _measure(self, started: float, attempts: int, code: str) -> None:
        logger.info(
            "agent_interpret code=%s attempts=%d elapsed_ms=%.1f",
            code,
            attempts,
            (self.clock() - started) * 1000,
        )
