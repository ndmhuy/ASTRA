"""V2 four-agent LaTeX route with explicit human inspection headers."""

from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Body, Request
from fastapi.responses import JSONResponse, Response
from pydantic import ValidationError

from exam_baseline.baseline.samples import sample_request
from exam_baseline.pipeline.bootstrap import provider_scope
from exam_baseline.pipeline.contracts import PipelineRequest
from exam_baseline.pipeline.errors import PipelineFailure
from exam_baseline.pipeline.orchestration.orchestrator import Orchestrator

router = APIRouter()


@router.post(
    "/v2/exams/generate",
    response_class=Response,
    responses={
        200: {
            "content": {"application/x-tex": {}},
            "description": "Native LaTeX exam awaiting user visual inspection",
        }
    },
)
async def generate_pipeline(
    request: Request,
    payload: Annotated[
        PipelineRequest,
        Body(
            openapi_examples={
                "algebra": {
                    "summary": "Four agents and one feedback before human review",
                    "value": {"request": sample_request().model_dump(mode="json")},
                }
            }
        ),
    ],
) -> Response:
    settings = request.app.state.settings
    pipeline_providers = request.app.state.pipeline_providers
    pipeline_output_root = request.app.state.pipeline_output_root
    output = (pipeline_output_root or Path("runs/pipeline")) / str(uuid4())
    try:
        if pipeline_providers is not None:
            result = await Orchestrator(pipeline_providers).run(payload, output)
        else:
            async with provider_scope(payload, settings) as providers:
                result = await Orchestrator(providers).run(payload, output)
    except ValidationError:
        return JSONResponse(status_code=422, content={"error": "invalid_configuration"})
    except (ValueError, PipelineFailure) as exc:
        return JSONResponse(status_code=422, content={"error": str(exc)})
    if result.final_latex:
        return Response(
            Path(result.final_latex).read_bytes(),
            media_type="application/x-tex",
            headers={
                "Content-Disposition": 'attachment; filename="de_thi.tex"',
                "X-Run-ID": result.run_id,
                "X-LaTeX-Validation": result.latex_validation,
                "X-Human-Review-Required": "true",
                "X-Reviewer-Feedback-Sent": str(result.reviewer_feedback_sent).lower(),
            },
        )
    code = (
        504
        if any("timeout" in e.code for e in result.errors)
        else 502
        if result.execution_status == "failed"
        else 409
    )
    return JSONResponse(status_code=code, content=result.model_dump(mode="json"))
