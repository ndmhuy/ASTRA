"""Same-origin conversation interpretation. This router has no MAS dependencies."""

from collections.abc import Awaitable, Callable
from hashlib import sha256
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .admission import Admission, normalize_message
from .contracts import MAX_BODY, VERSION, Decision, Turn

Interpreter = Callable[[Turn], Awaitable[Decision]]


def create_agent_router(interpreter: Interpreter | None = None) -> APIRouter:
    router = APIRouter(prefix="/agent")
    admission = Admission()

    @router.post("/turn")
    async def turn(
        request: Request, marker: Annotated[str | None, Header(alias="X-Astra-Agent")] = None
    ):
        if marker != VERSION or request.headers.get("sec-fetch-site") not in (None, "same-origin"):
            raise HTTPException(403, "agent_boundary")
        raw = bytearray()
        async for chunk in request.stream():
            if len(raw) + len(chunk) > MAX_BODY:
                raise HTTPException(413, "agent_body_limit")
            raw.extend(chunk)
        try:
            payload = Turn.model_validate_json(raw)
        except ValidationError:
            raise HTTPException(422, "agent_invalid_turn") from None
        payload.message = normalize_message(payload.message)
        peer = request.client.host if request.client else "local"
        fingerprint = sha256(payload.model_dump_json().encode()).hexdigest()
        decision = admission.enter(peer, payload, fingerprint)
        if decision is None:
            try:
                decision = (
                    Decision.model_validate(await interpreter(payload))
                    if interpreter
                    else Decision(kind="temporarily_unavailable", reasonCode="disabled")
                )
                admission.finish(peer, payload, fingerprint, decision)
            finally:
                admission.active.pop(payload.workspaceId, None)
        return JSONResponse(
            {
                "schemaVersion": VERSION,
                "clientMessageId": payload.clientMessageId,
                "decision": decision.model_dump(exclude_none=True),
            },
            headers={"Cache-Control": "no-store"},
        )

    return router
