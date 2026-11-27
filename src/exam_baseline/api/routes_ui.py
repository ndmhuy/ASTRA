"""UI adapter over native THPT jobs; existing V1/V2 routes remain compatible."""

import asyncio
import json
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Header, Query, Request, Response
from fastapi.responses import FileResponse, StreamingResponse

from exam_baseline.ui.contracts import (
    ApprovalRequest,
    EditRequest,
    ExamGenerateRequest,
    PreviewRequest,
    RegenerateRequest,
    RevisionRequest,
    format_catalog,
)
from exam_baseline.ui.jobs import resolve_request

router = APIRouter(prefix="/api")


@router.get("/health")
async def health(request: Request):
    settings = request.app.state.settings
    return {
        "status": "ok",
        "engine": "thpt_math_v2",
        "demoMode": settings.demo_mode,
        "providerConfigured": settings.provider in {"chat_completions", "worker_mas"},
        "corpusRef": settings.rag_corpus_ref,
        "latexCompilerAvailable": bool(request.app.state.ui_jobs.previews.compiler()),
    }


@router.get("/exam-formats")
async def formats():
    return {"schemaVersion": "exam-format-catalog-v1", "formats": format_catalog()}


@router.post("/exam-formats/evaluate")
async def evaluate(request: Request, payload: ExamGenerateRequest):
    native, matrix = await asyncio.to_thread(
        resolve_request, payload, settings=request.app.state.settings
    )
    return {
        "status": "validated",
        "formatId": payload.formatId,
        "formatVersion": payload.formatVersion,
        "request": native.model_dump(),
        "retrievalMatrix": matrix,
    }


@router.post("/exams/generate", status_code=202)
async def generate(
    request: Request,
    payload: ExamGenerateRequest,
    idempotency_key: Annotated[str, Header(min_length=1, max_length=128)],
):
    return await request.app.state.ui_jobs.start(payload, idempotency_key)


@router.get("/exams/{job_id}/status")
async def status(request: Request, job_id: UUID):
    return request.app.state.ui_jobs.status(str(job_id))


@router.get("/exams/{job_id}/events")
async def events(request: Request, job_id: UUID):
    manager = request.app.state.ui_jobs
    manager.get(str(job_id))

    async def stream():
        previous = None
        while not await request.is_disconnected():
            packet = manager.status(str(job_id))
            encoded = json.dumps(packet, ensure_ascii=False, sort_keys=True)
            if encoded != previous:
                yield f"data: {encoded}\n\n"
                previous = encoded
            if packet["status"] in {"completed", "failed"}:
                return
            await asyncio.sleep(0.3)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/exams/{job_id}")
async def package(request: Request, job_id: UUID):
    return request.app.state.ui_jobs.package(str(job_id))


@router.put("/exams/{job_id}/questions/{question_id}")
async def edit(request: Request, job_id: UUID, question_id: int, payload: EditRequest):
    return await request.app.state.ui_jobs.edit(
        str(job_id), question_id, payload.revision, payload.question
    )


@router.post("/exams/{job_id}/questions/{question_id}/regenerate")
async def regenerate(request: Request, job_id: UUID, question_id: int, payload: RegenerateRequest):
    return await request.app.state.ui_jobs.regenerate(
        str(job_id), question_id, payload.revision, payload.instruction
    )


@router.post("/exams/{job_id}/questions/{question_id}/verify")
async def verify(request: Request, job_id: UUID, question_id: int, payload: RevisionRequest):
    return await request.app.state.ui_jobs.verify_question(
        str(job_id), question_id, payload.revision
    )


@router.post("/exams/{job_id}/approve")
async def approve(request: Request, job_id: UUID, payload: ApprovalRequest):
    return await request.app.state.ui_jobs.approve(str(job_id), payload)


@router.post("/exams/{job_id}/preview")
async def create_preview(
    request: Request, response: Response, job_id: UUID, payload: PreviewRequest
):
    state = await request.app.state.ui_jobs.preview(
        str(job_id),
        payload.revision,
        payload.contentHash,
        start=True,
    )
    response.status_code = 200 if state["status"] == "ready" else 202
    response.headers["Cache-Control"] = "no-store"
    return state


@router.get("/exams/{job_id}/preview")
async def preview_status(
    request: Request,
    response: Response,
    job_id: UUID,
    revision: Annotated[int, Query(ge=1)],
    contentHash: Annotated[str, Query(pattern=r"^[a-f0-9]{64}$")],
):
    response.headers["Cache-Control"] = "no-store"
    return await request.app.state.ui_jobs.preview(str(job_id), revision, contentHash)


@router.get("/exams/{job_id}/preview.pdf")
async def preview_pdf(
    request: Request,
    job_id: UUID,
    revision: Annotated[int, Query(ge=1)],
    contentHash: Annotated[str, Query(pattern=r"^[a-f0-9]{64}$")],
):
    path = await request.app.state.ui_jobs.preview(str(job_id), revision, contentHash, file=True)
    return FileResponse(
        path,
        media_type="application/pdf",
        filename="de_thi.pdf",
        content_disposition_type="inline",
        headers={"Cache-Control": "no-store"},
    )


@router.get("/exams/{job_id}/preview.log")
async def preview_log(
    request: Request,
    job_id: UUID,
    revision: Annotated[int, Query(ge=1)],
    contentHash: Annotated[str, Query(pattern=r"^[a-f0-9]{64}$")],
):
    path = await request.app.state.ui_jobs.preview(str(job_id), revision, contentHash, log=True)
    return FileResponse(path, media_type="text/plain", headers={"Cache-Control": "no-store"})


@router.get("/exams/{job_id}/export")
async def export(
    request: Request,
    job_id: UUID,
    type: Literal["STUDENT_EXAM", "TEACHER_KEY"],
    format: Literal["tex", "json", "pdf"],
):
    path, media_type = await request.app.state.ui_jobs.export(str(job_id), type, format)
    return FileResponse(path, media_type=media_type, filename=path.name)
