"""HTTP application composition, settings and baseline service lifetime."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from exam_baseline import __version__
from exam_baseline.api.routes_baseline import router as baseline_router
from exam_baseline.api.routes_pipeline import router as pipeline_router
from exam_baseline.baseline.bootstrap import service_scope
from exam_baseline.baseline.service import GenerationService
from exam_baseline.config import Settings
from exam_baseline.core.contracts import LLMProvider


def create_app(
    settings: Settings | None = None,
    *,
    provider: LLMProvider | None = None,
    service: GenerationService | None = None,
    pipeline_providers: dict[str, LLMProvider] | None = None,
    pipeline_output_root: Path | None = None,
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
        title="ASTRA Exam Generation",
        version=__version__,
        lifespan=lifespan,
        description="V1: JSON baseline. V2: four agents, one feedback, human visual review.",
    )

    app.state.settings = settings
    app.state.pipeline_providers = pipeline_providers
    app.state.pipeline_output_root = pipeline_output_root
    app.include_router(baseline_router)
    app.include_router(pipeline_router)
    return app


def configure_logging() -> None:
    logger = logging.getLogger("exam_baseline.baseline.evaluation")
    if not logger.handlers:
        logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    logger.propagate = False
