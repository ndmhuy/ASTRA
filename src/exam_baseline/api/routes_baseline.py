"""V1 baseline JSON routes and health endpoints."""

from typing import Annotated

from fastapi import APIRouter, Body, Depends
from fastapi.responses import JSONResponse, RedirectResponse

from exam_baseline.api.dependencies import get_service
from exam_baseline.baseline.http_status import response_status
from exam_baseline.baseline.samples import sample_request
from exam_baseline.baseline.service import GenerationService
from exam_baseline.core.models import GenerationRequest, GenerationResponse

router = APIRouter()
example = {
    "algebra": {
        "summary": "Valid four-question algebra example",
        "value": sample_request().model_dump(mode="json"),
    }
}


@router.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse("/docs")


@router.get("/health")
def health(current: Annotated[GenerationService, Depends(get_service)]) -> dict[str, str]:
    metadata = current.agent.metadata
    return {"status": "ok", "provider": metadata.provider, "model": metadata.requested_model}


@router.post(
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
