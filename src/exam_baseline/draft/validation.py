"""Check matrix, provenance and legacy PNG handoff without model calls."""

from collections import Counter
from pathlib import Path

from pydantic import ValidationError

from exam_baseline.core.hashing import digest
from exam_baseline.core.models import GeneratedExam
from exam_baseline.core.validation import ExamValidator
from exam_baseline.draft.models import (
    ComposerOutput,
    DraftQuestion,
    ExamDraft,
    MiniRequest,
    StageError,
)


def validate_output(
    output: ComposerOutput, payload: MiniRequest, revision: int = 1
) -> list[StageError]:
    errors = []
    report = ExamValidator().validate(output.exam, payload.request)
    for check in report.checks:
        if not check.passed:
            detail = f"{check.code}: {check.message}"
            if isinstance(check.expected, (int, float)) and isinstance(check.actual, (int, float)):
                detail = f"{check.code}: expected {check.expected}, received {check.actual}."
            errors.append(StageError(code=check.code, stage="composer", message=detail))
    ids = [q.id for q in output.exam.questions]
    if Counter(ids) != Counter(q.id for q in output.questions):
        errors.append(
            StageError(
                code="question_metadata_mismatch",
                stage="composer",
                message="Question metadata IDs differ from exam.",
            )
        )
    evidence = {item.id: item for item in payload.evidence}
    for q in output.questions:
        if payload.require_evidence and not any(
            ref.role == "content_support" for ref in q.source_refs
        ):
            errors.append(
                StageError(
                    code="missing_evidence",
                    stage="composer",
                    message="Question has no content-support evidence.",
                    artifact_id=q.id,
                )
            )
        for ref in q.source_refs:
            if ref.evidence_id not in evidence or evidence[ref.evidence_id].role != ref.role:
                errors.append(
                    StageError(
                        code="invalid_evidence_ref",
                        stage="composer",
                        message="Unknown or mismatched evidence reference.",
                        artifact_id=q.id,
                    )
                )
    visual_ids = [v.visual_id for v in output.visuals]
    if len(visual_ids) != len(set(visual_ids)):
        errors.append(
            StageError(
                code="duplicate_visual_id", stage="composer", message="Visual IDs must be unique."
            )
        )
    for q in output.questions:
        if len(q.figure_refs) != len(set(q.figure_refs)) or any(
            v not in visual_ids for v in q.figure_refs
        ):
            errors.append(
                StageError(
                    code="invalid_figure_ref",
                    stage="composer",
                    message="Missing or duplicate visual reference.",
                    artifact_id=q.id,
                )
            )
    for visual in output.visuals:
        if (
            visual.question_id not in ids
            or visual.revision != revision
            or not any(
                q.id == visual.question_id and visual.visual_id in q.figure_refs
                for q in output.questions
            )
        ):
            errors.append(
                StageError(
                    code="visual_binding",
                    stage="composer",
                    message="Visual question/revision/reference mismatch.",
                    artifact_id=visual.visual_id,
                )
            )
    for question_id in payload.required_visual_question_ids:
        if question_id not in ids or not any(
            v.question_id == question_id and v.required for v in output.visuals
        ):
            errors.append(
                StageError(
                    code="required_visual_missing",
                    stage="composer",
                    message="Required visual has no specification.",
                    artifact_id=question_id,
                )
            )
    return errors


def verify_handoff(draft: ExamDraft, root: Path) -> list[StageError]:
    """Reject changed/missing assets before a downstream exporter consumes the draft."""
    errors = []
    if draft.composer.status != "succeeded" or draft.illustrator.status == "failed":
        errors.append(
            StageError(
                code="stage_failed",
                stage="illustrator",
                message="A required stage has not succeeded.",
            )
        )
    if any(q.answer is not None or q.solution is not None for q in draft.exam.questions):
        errors.append(
            StageError(
                code="student_answer_leak",
                stage="composer",
                message="Student exam contains a private answer or solution.",
            )
        )
    try:
        student = GeneratedExam.model_validate_json(
            (root / "student_view.json").read_text(encoding="utf-8")
        )
        if student != draft.exam:
            raise ValueError("student view differs from draft")
    except (OSError, ValidationError, ValueError):
        errors.append(
            StageError(
                code="student_view_mismatch",
                stage="composer",
                message="Student view is missing or differs from draft.",
            )
        )
    specs = {spec.visual_id: spec for spec in draft.visuals}
    questions = {question.id: question for question in draft.questions}
    figures = {figure.visual_id: figure for figure in draft.figures}
    for spec in draft.visuals:
        figure = figures.get(spec.visual_id)
        if figure is None:
            if spec.required:
                errors.append(
                    StageError(
                        code="figure_missing",
                        stage="illustrator",
                        message="Required figure is absent.",
                        artifact_id=spec.visual_id,
                    )
                )
            continue
        if (
            figure.question_id != spec.question_id
            or figure.revision != spec.revision
            or spec.revision != draft.revision
            or spec.visual_id
            not in questions.get(spec.question_id, DraftQuestion(id="_missing")).figure_refs
            or figure.spec_sha256 != digest(spec.model_dump_json().encode())
        ):
            errors.append(
                StageError(
                    code="figure_binding",
                    stage="illustrator",
                    message="Figure binding or spec hash differs.",
                    artifact_id=spec.visual_id,
                )
            )
        expected_path = f"figures/{spec.visual_id}.png"
        if figure.path != expected_path:
            errors.append(
                StageError(
                    code="figure_path",
                    stage="illustrator",
                    message="Unexpected asset path.",
                    artifact_id=spec.visual_id,
                )
            )
            continue
        try:
            asset = (root / figure.path).read_bytes()
        except OSError:
            asset = b""
        if digest(asset) != figure.asset_sha256 or not asset.startswith(b"\x89PNG\r\n\x1a\n"):
            errors.append(
                StageError(
                    code="figure_hash",
                    stage="illustrator",
                    message="Asset is missing or changed.",
                    artifact_id=spec.visual_id,
                )
            )
        elif (
            int.from_bytes(asset[16:20], "big") != figure.width_px
            or int.from_bytes(asset[20:24], "big") != figure.height_px
            or figure.mime != "image/png"
            or figure.renderer != "pillow-primitives-v1"
        ):
            errors.append(
                StageError(
                    code="figure_metadata",
                    stage="illustrator",
                    message="Figure dimensions or renderer differ.",
                    artifact_id=spec.visual_id,
                )
            )
    for visual_id in figures.keys() - specs.keys():
        errors.append(
            StageError(
                code="orphan_figure",
                stage="illustrator",
                message="Figure has no spec.",
                artifact_id=visual_id,
            )
        )
    return errors
