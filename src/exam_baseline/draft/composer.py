"""Generate and validate one Composer draft; optional legacy PNG rendering."""

import json
from pathlib import Path
from time import perf_counter
from uuid import NAMESPACE_URL, uuid5

from pydantic import ValidationError

from exam_baseline.core.contracts import CompletionRequest, LLMProvider, ProviderError
from exam_baseline.core.hashing import digest
from exam_baseline.core.profiles import hcm_de11_prompt
from exam_baseline.draft.artifacts import private_artifact_path
from exam_baseline.draft.models import (
    COMPOSER_RESPONSE,
    ComposerFailure,
    ExamDraft,
    MiniRequest,
    StageError,
    StageResult,
)
from exam_baseline.draft.prompts import SYSTEM
from exam_baseline.draft.rendering import render_visual
from exam_baseline.draft.validation import validate_output


async def create_draft(
    payload: MiniRequest,
    provider: LLMProvider,
    output_dir: Path,
    *,
    revision: int = 1,
    repair_feedback: dict | None = None,
    render_figures: bool = True,
) -> ExamDraft | StageResult:
    if payload.require_evidence and not payload.evidence:
        return StageResult(
            status="failed",
            errors=[
                StageError(
                    code="missing_evidence", stage="composer", message="Evidence is required."
                )
            ],
        )
    schema = COMPOSER_RESPONSE.json_schema()
    prompt = CompletionRequest(
        system=SYSTEM,
        user=json.dumps(
            {
                "request": payload.model_dump(mode="json"),
                "output_schema": schema,
                "format_instructions": hcm_de11_prompt()
                if payload.request.format_profile == "hcm_dgnl_de11"
                else None,
                "user_prompt": payload.user_prompt,
                "latex_template_reference": payload.latex_template,
                "exam_family": payload.exam_family,
                "revision": revision,
                "repair_feedback": repair_feedback,
            },
            ensure_ascii=False,
        ),
        output_schema=schema,
    )
    start = perf_counter()
    try:
        completion = await provider.complete(prompt)
    except ProviderError as exc:
        return StageResult(
            status="failed",
            calls=1,
            latency_ms=(perf_counter() - start) * 1000,
            errors=[StageError(code=exc.code, stage="composer", message=str(exc))],
        )
    if not render_figures:
        # Private diagnostic artifact for the next Composer schema/format correction.
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "composer_last_response.json").write_text(completion.text, encoding="utf-8")
    try:
        produced = COMPOSER_RESPONSE.validate_json(completion.text)
    except ValidationError:
        return StageResult(
            status="failed",
            calls=1,
            latency_ms=(perf_counter() - start) * 1000,
            usage=completion.usage,
            errors=[
                StageError(
                    code="invalid_composer_json",
                    stage="composer",
                    message="Output violates draft schema.",
                )
            ],
        )
    if isinstance(produced, ComposerFailure):
        return StageResult(
            status="failed",
            calls=1,
            latency_ms=(perf_counter() - start) * 1000,
            usage=completion.usage,
            errors=[
                StageError(
                    code=produced.error.code, stage="composer", message=produced.error.message
                )
            ],
        )
    errors = validate_output(produced, payload, revision)
    previous = (repair_feedback or {}).get("previous_output", {}).get("exam", {})
    if previous and [q.id for q in produced.exam.questions] != [
        q["id"] for q in previous["questions"]
    ]:
        errors.append(
            StageError(
                code="repair_question_ids",
                stage="composer",
                message="Content repairs must preserve ordered question IDs.",
            )
        )
    if errors:
        return StageResult(
            status="failed",
            calls=1,
            latency_ms=(perf_counter() - start) * 1000,
            usage=completion.usage,
            errors=errors,
        )
    student = produced.exam.model_copy(deep=True)
    private = {}
    for q in student.questions:
        private[q.id] = {"answer": q.answer, "solution": q.solution}
        q.answer = q.solution = None
    composer_latency_ms = (perf_counter() - start) * 1000
    illustrator_start = perf_counter()
    figures = []
    figure_errors = []
    for spec in produced.visuals if render_figures else []:
        try:
            figures.append(render_visual(spec, output_dir / "figures" / f"{spec.visual_id}.png"))
        except (ValueError, OSError, RuntimeError) as exc:
            figure_errors.append(
                StageError(
                    code="figure_failed",
                    stage="illustrator",
                    message=type(exc).__name__,
                    artifact_id=spec.visual_id,
                )
            )
    required_failed = any(
        spec.required and any(e.artifact_id == spec.visual_id for e in figure_errors)
        for spec in produced.visuals
    )
    illustrator = StageResult(
        status="failed" if required_failed else ("succeeded" if figures else "skipped"),
        errors=figure_errors,
        reason="No figures requested." if not produced.visuals else None,
        latency_ms=(perf_counter() - illustrator_start) * 1000,
    )
    input_hash = digest(payload.model_dump_json().encode())
    if revision != 1 or repair_feedback:
        input_hash = digest(
            json.dumps(
                {"input": input_hash, "revision": revision, "feedback": repair_feedback},
                sort_keys=True,
            ).encode()
        )
    output_hash = digest(completion.text.encode())
    draft = ExamDraft(
        exam_id=str(uuid5(NAMESPACE_URL, input_hash)),
        draft_id=str(uuid5(NAMESPACE_URL, input_hash + output_hash)),
        revision=revision,
        exam=student,
        questions=produced.questions,
        visuals=produced.visuals,
        figures=figures,
        input_sha256=input_hash,
        output_sha256=output_hash,
        provider=provider.name,
        model=completion.model,
        composer=StageResult(
            status="succeeded",
            calls=1,
            latency_ms=composer_latency_ms,
            usage=completion.usage,
        ),
        illustrator=illustrator,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "exam_draft.json").write_text(
        draft.model_dump_json(indent=2, exclude_none=True), encoding="utf-8"
    )
    (output_dir / "student_view.json").write_text(
        student.model_dump_json(indent=2, exclude_none=True), encoding="utf-8"
    )
    private_path = private_artifact_path(output_dir, draft.draft_id)
    private_path.parent.mkdir(parents=True, exist_ok=True)
    private_path.write_text(json.dumps(private, ensure_ascii=False, indent=2), encoding="utf-8")
    return draft
