"""Same-origin conversation interpretation. This router has no MAS dependencies."""

from collections.abc import Awaitable, Callable
from hashlib import sha256
from ipaddress import ip_address
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .admission import Admission, normalize_message
from .contracts import MAX_BODY, VERSION, Decision, Turn

Interpreter = Callable[[Turn], Awaitable[Decision]]


def is_loopback(value: str | None) -> bool:
    if value == "localhost":
        return True
    try:
        return ip_address(value or "").is_loopback
    except ValueError:
        return False


def create_agent_router(interpreter: Interpreter | None = None) -> APIRouter:
    router = APIRouter(prefix="/agent")
    admission = Admission()

    @router.post("/turn")
    async def turn(
        request: Request, marker: Annotated[str | None, Header(alias="X-Astra-Agent")] = None
    ):
        if marker != VERSION or request.headers.get("sec-fetch-site") not in (None, "same-origin"):
            raise HTTPException(403, "agent_boundary")
        if any(
            key in request.headers
            for key in ("authorization", "cf-aig-authorization", "x-goog-api-key")
        ):
            raise HTTPException(403, "agent_boundary")
        configured = getattr(request.app.state, "configured_interpreter", None)
        peer = request.client.host if request.client else ""
        if configured and not (is_loopback(peer) and is_loopback(request.url.hostname)):
            raise HTTPException(403, "agent_local_boundary")
        selected = interpreter or configured
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
        fingerprint = sha256(payload.model_dump_json().encode()).hexdigest()
        decision = admission.enter(peer, payload, fingerprint)
        if decision is None:
            try:
                decision = (
                    Decision.model_validate(await selected(payload))
                    if selected
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
