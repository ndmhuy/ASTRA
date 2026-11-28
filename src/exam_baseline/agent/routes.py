"""Same-origin conversation interpretation and allowlisted web research. No MAS deps."""

from collections.abc import Awaitable, Callable
from hashlib import sha256
from ipaddress import ip_address
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .admission import Admission, normalize_message
from .contracts import MAX_BODY, VERSION, Decision, Turn
from .research import ResearchRequest, ResearchResponse, search_adjacent_topic
from .semantics import SemanticFrame, SemanticTurn, legacy_decision
from .v3 import FrameV3, TurnV3, upgrade_legacy

Interpreter = Callable[[Turn], Awaitable[Decision | SemanticFrame]]
Researcher = Callable[[ResearchRequest], Awaitable[ResearchResponse]]


def is_loopback(value: str | None) -> bool:
    if value == "localhost":
        return True
    try:
        return ip_address(value or "").is_loopback
    except ValueError:
        return False


async def _read_bounded_body(request: Request, marker: str | None) -> bytearray:
    if marker != VERSION or request.headers.get("sec-fetch-site") not in (None, "same-origin"):
        raise HTTPException(403, "agent_boundary")
    if any(
        key in request.headers
        for key in ("authorization", "cf-aig-authorization", "x-goog-api-key")
    ):
        raise HTTPException(403, "agent_boundary")
    raw = bytearray()
    async for chunk in request.stream():
        if len(raw) + len(chunk) > MAX_BODY:
            raise HTTPException(413, "agent_body_limit")
        raw.extend(chunk)
    return raw


def create_agent_router(
    interpreter: Interpreter | None = None,
    researcher: Researcher | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/agent")
    admission = Admission()

    @router.post("/turn")
    async def turn(
        request: Request, marker: Annotated[str | None, Header(alias="X-Astra-Agent")] = None
    ):
        raw = await _read_bounded_body(request, marker)
        configured = getattr(request.app.state, "configured_interpreter", None)
        peer = request.client.host if request.client else ""
        if configured and not (is_loopback(peer) and is_loopback(request.url.hostname)):
            raise HTTPException(403, "agent_local_boundary")
        selected = interpreter or configured
        try:
            contract = (
                TurnV3
                if request.headers.get("X-Astra-Semantic") == "astra-semantic-v3"
                else (
                    SemanticTurn
                    if request.headers.get("X-Astra-Semantic") == "astra-semantic-v1"
                    else Turn
                )
            )
            payload = contract.model_validate_json(raw)
        except ValidationError:
            raise HTTPException(422, "agent_invalid_turn") from None
        payload.message = normalize_message(payload.message)
        fingerprint = sha256(payload.model_dump_json(exclude_none=True).encode()).hexdigest()
        decision = admission.enter(peer, payload, fingerprint)
        if decision is None:
            try:
                decision = (
                    await selected(payload)
                    if selected
                    else Decision(kind="temporarily_unavailable", reasonCode="disabled")
                )
                if not isinstance(decision, (SemanticFrame, FrameV3)):
                    decision = Decision.model_validate(decision)
                admission.finish(peer, payload, fingerprint, decision)
            finally:
                admission.leave(peer, payload)
        if request.headers.get("X-Astra-Semantic") == "astra-semantic-v3" and isinstance(
            decision, (SemanticFrame, FrameV3)
        ):
            source = decision.schemaVersion
            frame = upgrade_legacy(decision) if isinstance(decision, SemanticFrame) else decision
            result = {
                "schemaVersion": frame.schemaVersion,
                "sourceContract": source,
                "clientMessageId": payload.clientMessageId,
                "frame": frame.model_dump(exclude_none=True),
            }
        elif (
            isinstance(decision, SemanticFrame)
            and request.headers.get("X-Astra-Semantic") == decision.schemaVersion
        ):
            result = {
                "schemaVersion": decision.schemaVersion,
                "clientMessageId": payload.clientMessageId,
                "frame": decision.model_dump(exclude_none=True),
            }
        else:
            if isinstance(decision, SemanticFrame):
                decision = legacy_decision(decision)
            result = {
                "schemaVersion": VERSION,
                "clientMessageId": payload.clientMessageId,
                "decision": decision.model_dump(exclude_none=True),
            }
        return JSONResponse(
            result,
            headers={"Cache-Control": "no-store"},
        )

    @router.get("/capabilities")
    async def capabilities(request: Request):
        configured = getattr(request.app.state, "configured_interpreter", None)
        provider = getattr(getattr(configured, "routes", [None])[0], "provider", None)
        version = getattr(provider, "semantic_version", "astra-semantic-v1")
        return JSONResponse(
            {
                "clientContract": "astra-semantic-v3",
                "providerContract": version,
                "compatibility": "native"
                if version == "astra-semantic-v3"
                else "explicit-legacy-bridge",
                "workerDeploymentRequired": version != "astra-semantic-v3",
            },
            headers={"Cache-Control": "no-store"},
        )

    @router.post("/research")
    async def research(
        request: Request, marker: Annotated[str | None, Header(alias="X-Astra-Agent")] = None
    ):
        raw = await _read_bounded_body(request, marker)
        try:
            payload = ResearchRequest.model_validate_json(raw)
        except ValidationError:
            raise HTTPException(422, "agent_invalid_research") from None
        settings = getattr(request.app.state, "settings", None)
        allow_network = not bool(getattr(settings, "demo_mode", False))
        selected = researcher or getattr(request.app.state, "agent_researcher", None)
        result = (
            await selected(payload)
            if selected
            else await search_adjacent_topic(payload, allow_network=allow_network)
        )
        return JSONResponse(
            ResearchResponse.model_validate(result).model_dump(mode="json"),
            headers={"Cache-Control": "no-store"},
        )

    return router
