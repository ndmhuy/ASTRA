"""Record every attempted call, including invalid JSON and provider failures."""

import asyncio
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from exam_baseline.core.contracts import ProviderError
from exam_baseline.core.recovery import OPERATION, POLICY, classify, delay


class ContractError(ValueError):
    def __init__(self, stage, fields):
        self.stage = stage
        self.fields = fields
        super().__init__(f"{stage} returned invalid JSON/schema after bounded correction")


class RecordingProvider:
    def __init__(
        self,
        provider,
        stage: str,
        revision: int,
        calls: list,
        directory: Path,
        retries: int = 0,
        *,
        on_attempt=None,
        operation_id=None,
    ):
        self.provider = provider
        self.stage = stage
        self.revision = revision
        self.calls = calls
        self.directory = directory
        self.retries = retries
        self.record = None
        self.on_attempt = on_attempt or (lambda: None)
        self.operation_id = operation_id

    async def complete(self, request):
        started = perf_counter()
        policy = POLICY["mas"]
        for attempt in range(min(self.retries + 1, policy["maxAttempts"])):
            try:
                return await self._once(request)
            except ProviderError as exc:
                failure = classify(exc)
                if (
                    not failure.retryable
                    or attempt == self.retries
                    or attempt + 1 == policy["maxAttempts"]
                ):
                    raise
                wait = delay(attempt, exc.retry_after_seconds, policy)
                if perf_counter() - started + wait >= policy["deadlineSeconds"]:
                    raise
                retry_wait = getattr(self.provider, "retry_wait", None)
                if retry_wait:
                    await retry_wait(wait, attempt + 2, exc)
                else:
                    await asyncio.sleep(wait)

    async def _once(self, request):
        record = dict(role=self.stage, revision=self.revision, status="started")
        self.calls.append(record)
        if self.operation_id:
            record["operation_id"] = self.operation_id
        self.record = record
        call_number = len(self.calls)
        start = perf_counter()
        completion = None
        attempt_id = str(uuid4())
        record["attempt_id"] = attempt_id
        self.on_attempt()
        context = OPERATION.set((self.operation_id, attempt_id))
        try:
            completion = await self.provider.complete(request)
            record["status"] = "response_received"
            return completion
        except asyncio.CancelledError:
            record["status"] = "cancelled"
            raise
        except ProviderError as exc:
            completion = exc.completion
            record.update(status="failed", error=exc.code, http_status=exc.http_status)
            failure = classify(exc)
            record.update(failure_category=failure.category, outcome_uncertain=failure.uncertain)
            if exc.retry_after_seconds is not None:
                record["retry_after_seconds"] = exc.retry_after_seconds
            raise
        finally:
            OPERATION.reset(context)
            record["latency_ms"] = round((perf_counter() - start) * 1000)
            if completion is not None:
                name = f"call_{call_number:02d}_{self.stage}_r{self.revision}.txt"
                self.directory.mkdir(parents=True, exist_ok=True)
                (self.directory / name).write_text(completion.text, encoding="utf-8")
                record.update(
                    model=completion.model,
                    usage=completion.usage.model_dump(),
                    response_file=str(self.directory / name),
                )
            self.on_attempt()

    def record_contract(self, status, fields=None, normalized=False):
        self.record.update(status=status, fields=fields, normalized_json_fence=normalized)
