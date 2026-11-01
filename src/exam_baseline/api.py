"""REST routes and dependency wiring. No external requests during import or app creation."""

import logging
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Body, Depends, FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse

from . import __version__
from .bootstrap import service_scope
from .config import Settings
from .contracts import LLMProvider
from .http_status import response_status
from .models import GenerationRequest, GenerationResponse
from .samples import sample_request
from .service import GenerationService


def get_service(request: Request) -> GenerationService:
    return request.app.state.service


def create_app(
    settings: Settings | None = None,
    *,
    provider: LLMProvider | None = None,
    service: GenerationService | None = None,
) -> FastAPI:
    settings = settings if settings is not None else Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if service is not None:
            app.state.service = service
            yield
        else:
            async with service_scope(settings, provider) as current:
                app.state.service = current
                yield

    app = FastAPI(
        title="Single-Agent Exam Baseline",
        version=__version__,
        lifespan=lifespan,
        description="One generation call followed by deterministic validation. JSON only.",
    )
    example = {
        "algebra": {
            "summary": "Valid four-question algebra example",
            "value": sample_request().model_dump(mode="json"),
        }
    }

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse("/docs")

    @app.get("/health")
    def health(current: Annotated[GenerationService, Depends(get_service)]) -> dict[str, str]:
        metadata = current.agent.metadata
        return {"status": "ok", "provider": metadata.provider, "model": metadata.requested_model}

    @app.post(
        "/v1/exams/generate",
        response_model=GenerationResponse,
        responses={code: {"model": GenerationResponse} for code in (413, 502, 503, 504)},
    )
    async def generate(
        payload: Annotated[GenerationRequest, Body(openapi_examples=example)],
        current: Annotated[GenerationService, Depends(get_service)],
    ) -> JSONResponse:
        result = await current.generate(payload)
        return JSONResponse(
            status_code=response_status(result),
            content=result.model_dump(mode="json"),
        )

    return app


def configure_logging() -> None:
    logger = logging.getLogger("exam_baseline.evaluation")
    if not logger.handlers:
        logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    logger.propagate = False
