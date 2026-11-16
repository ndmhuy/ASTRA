"""Mock job boundary and revision-aware deferred-change ledger."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import NAMESPACE_URL, uuid5

from .models import JobSnapshot, PendingChange, StartReceipt


class MockJobManager:
    def __init__(self):
        self._receipts: dict[str, StartReceipt] = {}
        self._jobs: dict[str, JobSnapshot] = {}

    def start(self, workspace_session_id: str, idempotency_key: str) -> StartReceipt:
        if idempotency_key in self._receipts:
            return self._receipts[idempotency_key]
        existing = self.active_for(workspace_session_id)
        if existing:
            return next(
                receipt for receipt in self._receipts.values() if receipt.job_id == existing.job_id
            )
        job_id = f"mock-job-{uuid5(NAMESPACE_URL, idempotency_key).hex[:12]}"
        receipt = StartReceipt(
            job_id=job_id,
            workspace_session_id=workspace_session_id,
            idempotency_key=idempotency_key,
            accepted_at=datetime.now(UTC),
            source="mock",
        )
        self._receipts[idempotency_key] = receipt
        self._jobs[job_id] = JobSnapshot(
            job_id=job_id,
            workspace_session_id=workspace_session_id,
            status="active",
            stage="mock_composing",
            completed_items=0,
            total_items=None,
            source="mock",
        )
        return receipt

    def active_for(self, workspace_session_id: str) -> JobSnapshot | None:
        return next(
            (
                job
                for job in self._jobs.values()
                if job.workspace_session_id == workspace_session_id and job.status == "active"
            ),
            None,
        )

    def snapshot(self, job_id: str) -> JobSnapshot | None:
        job = self._jobs.get(job_id)
        return job.model_copy(deep=True) if job else None

    def update(self, job_id: str, **changes) -> JobSnapshot:
        job = self._jobs[job_id]
        updated = job.model_copy(update={**changes, "revision": job.revision + 1})
        self._jobs[job_id] = updated
        return updated.model_copy(deep=True)


class PendingChangeLedger:
    def add(
        self,
        entries: list[PendingChange],
        *,
        conversation_id: str,
        workspace_session_id: str,
        job_id: str,
        origin_message_id: str,
        instruction: str,
        kind: str,
        display_question_index: int | None,
        question_id: str | None,
    ) -> PendingChange:
        revision = max((entry.revision for entry in entries), default=0) + 1
        if kind == "structural":
            for entry in entries:
                if entry.kind == "structural" and entry.status == "pending":
                    entry.status = "superseded"
        change = PendingChange(
            change_id=f"change-{revision}",
            conversation_id=conversation_id,
            workspace_session_id=workspace_session_id,
            job_id=job_id,
            question_id=question_id,
            display_question_index=display_question_index,
            instruction=instruction,
            kind=kind,
            status="pending" if kind == "structural" or question_id else "needs_target",
            origin_message_id=origin_message_id,
            revision=revision,
        )
        entries.append(change)
        return change

    def cancel_question(self, entries: list[PendingChange], display_index: int | None) -> int:
        cancelled = 0
        for entry in entries:
            if entry.kind != "question" or entry.status not in {"pending", "needs_target"}:
                continue
            if display_index is None or entry.display_question_index == display_index:
                entry.status = "cancelled"
                cancelled += 1
        return cancelled

    def consolidate(self, entries: list[PendingChange]) -> list[dict[str, object]]:
        return [
            {
                "change_id": entry.change_id,
                "kind": entry.kind,
                "question_id": entry.question_id,
                "instruction": entry.instruction,
                "status": entry.status,
            }
            for entry in entries
            if entry.status in {"pending", "needs_target"}
        ]
