"""Record every attempted call, including invalid JSON and provider failures."""

import asyncio
from pathlib import Path
from time import perf_counter

from exam_baseline.core.contracts import ProviderError


class ContractError(ValueError):
    def __init__(self, stage, fields):
        self.stage = stage
        self.fields = fields
        super().__init__(f"{stage} returned invalid JSON/schema after bounded correction")


class RecordingProvider:
    def __init__(
        self, provider, stage: str, revision: int, calls: list, directory: Path, retries: int = 0
    ):
        self.provider = provider
        self.stage = stage
        self.revision = revision
        self.calls = calls
        self.directory = directory
        self.retries = retries

    async def complete(self, request):
        for attempt in range(self.retries + 1):
            try:
                return await self._once(request)
            except ProviderError as exc:
                transient = exc.http_status in {429, 500, 502, 503, 504} or (
                    exc.code in {"provider_timeout", "provider_unreachable"}
                )
                if not transient or attempt == self.retries:
                    raise
                await asyncio.sleep(1)

    async def _once(self, request):
        record = dict(role=self.stage, revision=self.revision, status="started")
        self.calls.append(record)
        start = perf_counter()
        completion = None
        try:
            completion = await self.provider.complete(request)
            record["status"] = "response_received"
            return completion
        except ProviderError as exc:
            completion = exc.completion
            record.update(status="failed", error=exc.code, http_status=exc.http_status)
            raise
        finally:
            record["latency_ms"] = round((perf_counter() - start) * 1000)
            if completion is not None:
                name = f"call_{len(self.calls):02d}_{self.stage}_r{self.revision}.txt"
                self.directory.mkdir(parents=True, exist_ok=True)
                (self.directory / name).write_text(completion.text, encoding="utf-8")
                record.update(
                    model=completion.model,
                    usage=completion.usage.model_dump(),
                    response_file=str(self.directory / name),
                )

    def record_contract(self, status, fields=None, normalized=False):
        self.calls[-1].update(status=status, fields=fields, normalized_json_fence=normalized)
