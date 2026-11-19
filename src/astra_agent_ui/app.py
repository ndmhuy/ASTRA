from __future__ import annotations

import asyncio
import secrets
import time
from collections import deque
from collections.abc import Awaitable, Callable

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import AgentSettings
from .gemini_provider import GeminiInterpretationProvider, GeminiProviderError
from .interpreter import AgentInterpreter
from .models import AgentTurnRequest, AgentTurnResponse


class SessionTokens:
    def __init__(self, ttl_seconds: int):
        self.ttl_seconds = ttl_seconds
        self._tokens: dict[str, float] = {}

    def issue(self) -> str:
        now = time.monotonic()
        self._tokens = {token: expiry for token, expiry in self._tokens.items() if expiry > now}
        token = secrets.token_urlsafe(32)
        self._tokens[token] = now + self.ttl_seconds
        return token

    def valid(self, token: str | None) -> bool:
        if not token:
            return False
        expiry = self._tokens.get(token)
        return expiry is not None and expiry > time.monotonic()


def create_app(
    settings: AgentSettings | None = None,
    interpreter: AgentInterpreter | None = None,
) -> FastAPI:
    active_settings = settings or AgentSettings.from_environment()
    active_interpreter = interpreter or AgentInterpreter(
        provider=GeminiInterpretationProvider(active_settings), mode=active_settings.mode
    )
    tokens = SessionTokens(active_settings.session_ttl_seconds)
    turn_slots = asyncio.Semaphore(active_settings.max_concurrent_turns)
    rate_windows: dict[str, deque[float]] = {}
    app = FastAPI(title="ASTRA UI Agent", version="0.1.0", docs_url=None, redoc_url=None)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(active_settings.allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-ASTRA-Agent-Session"],
    )

    @app.exception_handler(GeminiProviderError)
    async def gemini_error(_request: Request, error: GeminiProviderError) -> JSONResponse:
        status_code = {
            "quota": status.HTTP_429_TOO_MANY_REQUESTS,
            "timeout": status.HTTP_504_GATEWAY_TIMEOUT,
            "auth_error": status.HTTP_502_BAD_GATEWAY,
            "model_unavailable": status.HTTP_502_BAD_GATEWAY,
            "provider_error": status.HTTP_502_BAD_GATEWAY,
            "network_error": status.HTTP_502_BAD_GATEWAY,
            "request_rejected": status.HTTP_502_BAD_GATEWAY,
            "sdk_error": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "upstream_server_error": status.HTTP_502_BAD_GATEWAY,
        }.get(error.code, status.HTTP_503_SERVICE_UNAVAILABLE)
        messages = {
            "disabled": "Gemini AI mode is not enabled.",
            "missing_key": "Gemini AI mode requires a local GEMINI_API_KEY.",
            "sdk_missing": "Gemini AI mode requires the optional google-genai package.",
            "provider_not_configured": "Gemini provider is not configured for AI mode.",
            "auth_error": "Gemini rejected the configured API key or project access.",
            "model_unavailable": "The configured Gemini model is unavailable to this project.",
            "quota": "Gemini quota or rate limit was exceeded.",
            "timeout": "Gemini interpretation timed out.",
            "empty_response": "Gemini returned no structured interpretation.",
            "provider_error": "Gemini interpretation failed.",
            "network_error": "Gemini network transport failed.",
            "request_rejected": "Gemini rejected the structured interpretation request.",
            "sdk_error": "The local Gemini SDK failed before a valid response was returned.",
            "upstream_server_error": (
                "Gemini returned an upstream server error. "
                "Retry once later; no UI action was executed."
            ),
        }
        return JSONResponse(
            status_code=status_code,
            content={
                "error": {
                    "code": f"gemini_{error.code}",
                    "message": messages.get(error.code, "Gemini interpretation failed."),
                }
            },
        )

    @app.middleware("http")
    async def protect_local_boundary(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        origin = request.headers.get("origin")
        if origin and origin not in active_settings.allowed_origins:
            return Response(status_code=status.HTTP_403_FORBIDDEN)
        length = request.headers.get("content-length")
        if length and (not length.isdigit()):
            return Response(status_code=400)
        if length and int(length) > active_settings.max_body_bytes:
            return Response(status_code=status.HTTP_413_CONTENT_TOO_LARGE)
        if request.method == "POST":
            if len(await request.body()) > active_settings.max_body_bytes:
                return Response(status_code=status.HTTP_413_CONTENT_TOO_LARGE)
            now = time.monotonic()
            for key in list(rate_windows):
                if not rate_windows[key] or rate_windows[key][-1] <= now - 60:
                    del rate_windows[key]
            # Session bootstrap is limited per local client; interpretation per
            # opaque token. Neither is user/tenant authorization.
            candidate = request.headers.get("x-astra-agent-session")
            identity = (candidate if tokens.valid(candidate) else None) or (
                request.client.host if request.client else "local"
            )
            bucket = rate_windows.setdefault(identity, deque())
            while bucket and bucket[0] <= now - 60:
                bucket.popleft()
            if len(bucket) >= 30:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "agent_rate_limited",
                            "message": "Too many Agent requests. Wait a minute before retrying.",
                        }
                    },
                    headers={"Retry-After": "60"},
                )
            bucket.append(now)
        return await call_next(request)

    def require_session(
        x_astra_agent_session: str | None = Header(default=None),
    ) -> None:
        if not tokens.valid(x_astra_agent_session):
            raise HTTPException(status_code=401, detail="invalid or expired agent session")

    @app.get("/agent/health")
    async def health() -> dict[str, object]:
        return {
            "status": "ok",
            "mode": active_settings.mode,
            "llmEnabled": active_settings.llm_enabled,
            "geminiKeyConfigured": bool(active_settings.gemini_api_key),
            "model": active_settings.gemini_model,
            "businessBackendAccess": False,
        }

    @app.post("/agent/session")
    async def create_session(request: Request) -> dict[str, object]:
        if request.headers.get("origin") not in active_settings.allowed_origins:
            raise HTTPException(status_code=403, detail="origin is not allowed")
        return {"token": tokens.issue(), "expiresIn": active_settings.session_ttl_seconds}

    @app.post(
        "/agent/interpret",
        response_model=AgentTurnResponse,
        dependencies=[Depends(require_session)],
    )
    async def interpret(request: AgentTurnRequest) -> AgentTurnResponse:
        if turn_slots.locked():
            raise HTTPException(status_code=429, detail="Agent is busy; retry later")
        async with turn_slots:
            return await active_interpreter.interpret(request)

    return app


app = create_app()


def main() -> None:
    import uvicorn

    settings = AgentSettings.from_environment()
    uvicorn.run("astra_agent_ui.app:app", host=settings.host, port=settings.port, reload=False)
