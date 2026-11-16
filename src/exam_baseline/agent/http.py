"""Standalone offline Agent HTTP app; no generation service or environment keys loaded."""

from fastapi import FastAPI, HTTPException

from .capabilities import CapabilityRegistry
from .models import TurnRequest, TurnResponse
from .orchestrator import ConversationOrchestrator
from .service import AgentService, ExecutionFeedback


def create_agent_app(service: AgentService | None = None) -> FastAPI:
    service = service or AgentService(
        ConversationOrchestrator(registry=CapabilityRegistry.local_ui())
    )
    app = FastAPI(title="ASTRA Agent offline transport", version="0.1")

    @app.post("/agent/turns", response_model=TurnResponse)
    def turn(request: TurnRequest):
        try:
            return service.turn(request)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from None

    @app.post("/agent/execution-results", response_model=TurnResponse)
    def feedback(request: ExecutionFeedback):
        try:
            return service.feedback(request)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from None

    return app
