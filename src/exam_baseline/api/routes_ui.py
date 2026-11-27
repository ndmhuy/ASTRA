"""UI adapter over native THPT jobs; existing V1/V2 routes remain compatible."""

import asyncio
import json
from datetime import timezone
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Header, Path, Query, Request, Response
from fastapi.responses import FileResponse, StreamingResponse

from exam_baseline.ui.contracts import (
    ApprovalRequest,
    EditRequest,
    ExamGenerateRequest,
    GenerationControlRequest,
    PreviewRequest,
    QuestionApprovalRequest,
    RegenerateRequest,
    RevisionRequest,
    WorkspaceBranchRequest,
    WorkspaceDraft,
    WorkspaceImport,
    WorkspaceRestoreRequest,
    format_catalog,
)
from exam_baseline.ui.errors import UiError
from exam_baseline.ui.input_documents import POLICY, DocumentKind, save_document, validate_filename

router = APIRouter(prefix="/api")


@router.get("/input-documents/policy")
async def document_policy():
    return POLICY


@router.post("/input-documents", status_code=201)
async def upload_document(
    request: Request,
    filename: Annotated[str, Query(min_length=1, max_length=1024)],
    kind: DocumentKind = "supplementary",
):
    validate_filename(filename)
    content = bytearray()
    async for chunk in request.stream():
        if len(content) + len(chunk) > POLICY["max_bytes"]:
            raise UiError("document_too_large", "Mỗi tài liệu tối đa 10 MiB.", 413)
        content.extend(chunk)
    return await asyncio.to_thread(
        save_document, request.app.state.ui_jobs.root, filename, kind, bytes(content)
    )


@router.get("/workspaces")
def workspaces(request: Request, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return {"workspaces": request.app.state.ui_jobs.store.list_workspaces()}


@router.get("/workspaces/search")
def search_workspaces(
    request: Request, response: Response, q: Annotated[str, Query(min_length=1, max_length=200)]
):
    response.headers["Cache-Control"] = "no-store"
    return {"workspaceIds": request.app.state.ui_jobs.store.search_workspaces(q)}


@router.put("/workspaces/{workspace_id}")
def save_workspace(request: Request, workspace_id: UUID, payload: WorkspaceDraft):
    revision = request.app.state.ui_jobs.store.save_workspace(
        str(workspace_id), payload.revision, payload.storage_content("revision")
    )
    return {"revision": revision}


@router.get("/workspaces/{workspace_id}/versions")
async def workspace_versions(request: Request, workspace_id: UUID, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return request.app.state.ui_jobs.workspace_history(str(workspace_id))


@router.get("/workspaces/{workspace_id}/changes")
def workspace_changes(request: Request, workspace_id: UUID, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return request.app.state.ui_jobs.workspace_timeline(str(workspace_id))


@router.post("/workspaces/{workspace_id}/branch")
async def branch_workspace(request: Request, workspace_id: UUID, payload: WorkspaceBranchRequest):
    return await request.app.state.ui_jobs.branch_workspace(
        str(workspace_id), str(payload.destinationId), payload.messageId, payload.copyCurrent
    )


@router.post("/workspaces/{workspace_id}/changes/{job_id}/{change_id}/undo")
async def undo_workspace_change(
    request: Request,
    workspace_id: UUID,
    job_id: UUID,
    change_id: UUID,
    payload: RevisionRequest,
    idempotency_key: Annotated[UUID | None, Header()] = None,
):
    return await request.app.state.ui_jobs.undo_change(
        str(workspace_id),
        str(job_id),
        str(change_id),
        payload.revision,
        str(idempotency_key) if idempotency_key else None,
    )


@router.post("/workspaces/{workspace_id}/versions/restore")
async def restore_workspace_version(
    request: Request, workspace_id: UUID, payload: WorkspaceRestoreRequest
):
    return await request.app.state.ui_jobs.restore_workspace_version(
        str(workspace_id),
        str(payload.jobId),
        payload.revision,
        str(payload.targetJobId),
        payload.targetRevision,
    )


@router.post("/workspaces/{workspace_id}/import")
def import_workspace(request: Request, workspace_id: UUID, payload: WorkspaceImport):
    created_at = payload.createdAt.astimezone(timezone.utc).isoformat(timespec="milliseconds")
    status = request.app.state.ui_jobs.store.import_workspace(
        str(workspace_id),
        created_at.replace("+00:00", "Z"),
        str(payload.jobId) if payload.jobId else None,
        payload.storage_content("createdAt", "jobId"),
    )
    return {"status": status}


@router.delete("/workspaces/{workspace_id}", status_code=204)
def archive_workspace(request: Request, workspace_id: UUID):
    request.app.state.ui_jobs.store.archive_workspace(str(workspace_id))


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
async def formats(request: Request):
    return {
        "schemaVersion": "exam-format-catalog-v1",
        "formats": format_catalog(demo_mode=request.app.state.settings.demo_mode),
    }


@router.post("/exam-formats/evaluate")
async def evaluate(request: Request, payload: ExamGenerateRequest):
    native, matrix = await asyncio.to_thread(request.app.state.ui_jobs.resolve, payload)
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
    workspace_id: UUID | None = None,
):
    return await request.app.state.ui_jobs.start(
        payload, idempotency_key, str(workspace_id) if workspace_id else None
    )


@router.get("/exams/{job_id}/status")
async def status(request: Request, job_id: UUID):
    return request.app.state.ui_jobs.status(str(job_id))


@router.post("/exams/{job_id}/stop")
async def stop_generation(request: Request, job_id: UUID, payload: GenerationControlRequest):
    return request.app.state.ui_jobs.stop_generation(str(job_id), payload.executionVersion)


@router.post("/exams/{job_id}/pause", status_code=202)
async def pause_generation(request: Request, job_id: UUID, payload: GenerationControlRequest):
    return request.app.state.ui_jobs.pause_generation(str(job_id), payload.executionVersion)


@router.post("/exams/{job_id}/resume", status_code=202)
async def resume_generation(request: Request, job_id: UUID, payload: GenerationControlRequest):
    return request.app.state.ui_jobs.resume_generation(str(job_id), payload.executionVersion)


@router.post("/exams/{job_id}/retry", status_code=202)
async def retry_generation(request: Request, job_id: UUID, payload: GenerationControlRequest):
    return request.app.state.ui_jobs.resume_generation(
        str(job_id), payload.executionVersion, retry=True
    )


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
            if packet["status"] in {"completed", "failed", "cancelled", "paused", "interrupted"}:
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


@router.get("/exams/{job_id}/versions")
async def versions(request: Request, job_id: UUID, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return request.app.state.ui_jobs.versions(str(job_id))


@router.get("/exams/{job_id}/versions/{version}")
async def exam_version(request: Request, job_id: UUID, version: Annotated[int, Path(ge=1)]):
    return request.app.state.ui_jobs.version(str(job_id), version)


@router.post("/exams/{job_id}/versions/{version}/restore")
async def restore_version(
    request: Request, job_id: UUID, version: Annotated[int, Path(ge=1)], payload: RevisionRequest
):
    return await request.app.state.ui_jobs.restore_version(str(job_id), payload.revision, version)


@router.put("/exams/{job_id}/questions/{question_id}")
async def edit(
    request: Request,
    job_id: UUID,
    question_id: int,
    payload: EditRequest,
    idempotency_key: Annotated[UUID | None, Header()] = None,
    workspace_id: UUID | None = None,
):
    return await request.app.state.ui_jobs.question_change(
        str(job_id),
        question_id,
        payload.revision,
        "edited",
        payload.question,
        str(idempotency_key) if idempotency_key else None,
        workspace_id=str(workspace_id) if workspace_id else None,
    )


@router.post("/exams/{job_id}/questions/{question_id}/regenerate")
async def regenerate(
    request: Request,
    response: Response,
    job_id: UUID,
    question_id: int,
    payload: RegenerateRequest,
    idempotency_key: Annotated[UUID | None, Header()] = None,
    workspace_id: UUID | None = None,
    background: bool = False,
):
    result = await request.app.state.ui_jobs.question_change(
        str(job_id),
        question_id,
        payload.revision,
        "regenerated",
        payload.instruction,
        str(idempotency_key) if idempotency_key else None,
        workspace_id=str(workspace_id) if workspace_id else None,
        expected_stable_id=payload.stableId,
        background=background,
    )
    if background:
        response.status_code = 202
    return result


@router.get("/exams/{job_id}/regenerations/{change_id}")
def regeneration_status(request: Request, response: Response, job_id: UUID, change_id: UUID):
    response.headers["Cache-Control"] = "no-store"
    return request.app.state.ui_jobs.regeneration_status(str(job_id), str(change_id))


@router.post("/exams/{job_id}/regenerations/{change_id}/stop")
async def stop_regeneration(request: Request, job_id: UUID, change_id: UUID):
    return request.app.state.ui_jobs.stop_regeneration(str(job_id), str(change_id))


@router.post("/exams/{job_id}/questions/{question_id}/verify")
async def verify(request: Request, job_id: UUID, question_id: int, payload: RevisionRequest):
    return await request.app.state.ui_jobs.verify_question(
        str(job_id), question_id, payload.revision
    )


@router.post("/exams/{job_id}/questions/{question_id}/approve")
async def approve_question(
    request: Request, job_id: UUID, question_id: int, payload: QuestionApprovalRequest
):
    return await request.app.state.ui_jobs.approve_question(str(job_id), question_id, payload)


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


@router.get("/exams/{job_id}/assets/{asset_id}")
async def asset(
    request: Request,
    job_id: UUID,
    asset_id: str,
    revision: Annotated[int | None, Query(ge=1)] = None,
):
    path, media_type = request.app.state.ui_jobs.contract_asset(str(job_id), asset_id, revision)
    return FileResponse(path, media_type=media_type, headers={"Cache-Control": "no-store"})


@router.get("/exams/{job_id}/export")
async def export(
    request: Request,
    job_id: UUID,
    type: Literal["STUDENT_EXAM", "TEACHER_KEY"],
    format: Literal["tex", "json", "pdf", "docx", "md"],
):
    path, media_type, content = await request.app.state.ui_jobs.export(str(job_id), type, format)
    if content is not None:
        return Response(
            content,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{path.name}"'},
        )
    return FileResponse(path, media_type=media_type, filename=path.name)
