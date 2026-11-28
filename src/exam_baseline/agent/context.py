"""Read-only authoritative workspace facts for Chat. Never starts or changes jobs."""

import re
from datetime import datetime, timezone

from .v3 import BackendFacts, GroundedContext, TurnV3, WorkspaceFacts

ACTIVE = {"queued", "running", "pausing", "resuming", "retrying"}
SENSITIVE = re.compile(
    r"\bBearer\s+\S+|\bsk-[\w-]{12,}|\bAIza[\w-]{15,}|"
    r"(?:api[_ -]?key|token|password)\s*[:=]\s*\S+|\b[\w.+-]+@[\w.-]+\.\w{2,}",
    re.I,
)


def clean(value, maximum):
    if value is None:
        return None
    return " ".join(SENSITIVE.sub("[redacted]", str(value)).split())[:maximum]


def workspace_facts(store, row):
    attempt = row.get("generationId") or row.get("jobId")
    job = store.get(attempt) if attempt else {}
    request = job.get("request") or row.get("jobMeta") or {}
    state = row.get("generationState") or {}
    progress = state.get("progress") or {}
    # GenerationState.view exposes counters at top level, not just raw progress.
    done = state.get("completedItems", progress.get("completedItems", 0)) or 0
    error = row.get("generationError") or row.get("jobError") or {}
    artifact = store.get(row["jobId"]) if row.get("jobStatus") == "completed" else {}
    return WorkspaceFacts(
        title=clean(row.get("title") or "Đề chưa đặt tên", 120),
        lifecycle=row.get("generationStatus") or row.get("jobStatus") or "draft",
        subject=clean(request.get("subject"), 80),
        format=clean(request.get("formatId"), 80),
        count=request.get("itemCount"),
        minutes=request.get("durationMinutes"),
        completed=done,
        estimatedSecondsLeft=state.get("estimatedSecondsLeft") or None,
        stage=clean(
            state.get("statusMessage") or state.get("message") or progress.get("message"), 160
        ),
        requirements=clean(request.get("prompt"), 600),
        errorCode=clean(error.get("code"), 80),
        artifactAvailable=bool(artifact),
        approved=bool(artifact.get("approved")),
        revision=artifact.get("revision"),
    )


def backend_facts(store, workspace_id):
    rows = store.list_workspaces()
    current = next((row for row in rows if row["id"] == workspace_id), None)
    active = [row for row in rows if row.get("generationStatus") in ACTIVE]
    return BackendFacts(
        observedAt=datetime.now(timezone.utc).isoformat(),
        current=workspace_facts(store, current) if current else None,
        active=[workspace_facts(store, row) for row in active[:5]],
        activeCount=len(active),
    )


def ground_turn(turn, store):
    if not isinstance(turn, TurnV3):
        return turn
    facts = backend_facts(store, turn.workspaceId)
    grounded = turn.context.grounded or GroundedContext()
    return turn.model_copy(
        update={
            "context": turn.context.model_copy(
                update={"grounded": grounded.model_copy(update={"backend": facts})}
            )
        }
    )
