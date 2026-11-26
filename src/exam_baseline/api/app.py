"""HTTP application composition, settings and baseline service lifetime."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from exam_baseline import __version__
from exam_baseline.agent.routes import Interpreter, create_agent_router
from exam_baseline.api.routes_baseline import root
from exam_baseline.api.routes_baseline import router as baseline_router
from exam_baseline.api.routes_pipeline import router as pipeline_router
from exam_baseline.api.routes_ui import router as ui_router
from exam_baseline.baseline.bootstrap import service_scope
from exam_baseline.baseline.service import GenerationService
from exam_baseline.config import Settings
from exam_baseline.core.contracts import LLMProvider
from exam_baseline.ui.errors import UiError
from exam_baseline.ui.jobs import JobManager
from exam_baseline.ui.storage import JobConflict


def create_app(
    settings: Settings | None = None,
    *,
    provider: LLMProvider | None = None,
    service: GenerationService | None = None,
    pipeline_providers: dict[str, LLMProvider] | None = None,
    pipeline_output_root: Path | None = None,
    ui_output_root: Path | None = None,
    workspace_dir: Path | None = None,
    ui_runner=None,
    rag_retriever=None,
    agent_interpreter: Interpreter | None = None,
) -> FastAPI:
    settings = settings if settings is not None else Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.ui_jobs = JobManager(
            settings,
            root=ui_output_root,
            providers=pipeline_providers,
            retriever=rag_retriever,
            runner=ui_runner,
        )
        try:
            if service is not None:
                app.state.service = service
                yield
            else:
                async with service_scope(settings, provider) as current:
                    app.state.service = current
                    yield
        finally:
            await app.state.ui_jobs.close()

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
    app.include_router(ui_router)
    app.include_router(create_agent_router(agent_interpreter))
    if workspace_dir is None:
        app.add_api_route("/", root, methods=["GET"], include_in_schema=False)
    else:
        app.mount("/", StaticFiles(directory=workspace_dir, html=True), name="workspace")

    @app.exception_handler(UiError)
    async def ui_error(request, exc):
        return JSONResponse(status_code=exc.status, content={"error": exc.payload()})

    @app.exception_handler(JobConflict)
    async def job_conflict(request, exc):
        return JSONResponse(
            status_code=409,
            content={"error": {"code": "idempotency_conflict", "message": str(exc)}},
        )

    @app.exception_handler(ValidationError)
    async def contract_error(request, exc):
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "invalid_contract",
                    "message": (
                        "Nội dung câu hỏi chưa đúng định dạng "
                        "(thầy cô kiểm tra lại các ký hiệu công thức hoặc lựa chọn đáp án)."
                    ),
                    "fields": [
                        {"location": list(e["loc"]), "type": e["type"]}
                        for e in exc.errors(include_input=False, include_url=False)
                    ],
                }
            },
        )

    return app


def create_web_app() -> FastAPI:
    """Serve the built teacher workspace and its API from the same local port."""
    configure_logging()
    return create_app(workspace_dir=Path("astra-frontend/dist"))


def configure_logging() -> None:
    logger = logging.getLogger("exam_baseline.baseline.evaluation")
    if not logger.handlers:
        logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    logger.propagate = False
