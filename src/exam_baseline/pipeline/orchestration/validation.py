"""Deterministic admission and artifact checks, independent of workflow control."""

from collections.abc import Iterable
from pathlib import Path

from exam_baseline.draft.models import ComposerOutput, ExamDraft, MiniRequest
from exam_baseline.draft.validation import validate_output
from exam_baseline.pipeline.agents.validation import validate_review, validate_solutions
from exam_baseline.pipeline.contracts import (
    IllustrationBook,
    PipelineRequest,
    ReviewReport,
    SolutionBook,
)
from exam_baseline.pipeline.errors import PipelineFailure
from exam_baseline.pipeline.rendering.syntax import format_errors, prose, validate_template
from exam_baseline.pipeline.views import student_view, validate_illustrations


def validate_request(
    payload: PipelineRequest, output: Path, providers: Iterable[str], roles: Iterable[str]
) -> None:
    if output.exists():
        raise ValueError("output directory already exists")
    validate_template(payload.latex_template)
    for text in (
        payload.request.matrix.title,
        payload.request.matrix.subject,
        *(topic.name for topic in payload.request.matrix.topics),
    ):
        prose(text)
    if payload.request.matrix.question_count > payload.workflow.max_questions:
        raise ValueError("question count exceeds workflow limit")
    if len(payload.required_visual_question_ids) > payload.workflow.max_figures:
        raise ValueError("required figures exceed workflow limit")
    if payload.require_evidence and not any(e.role == "content_support" for e in payload.evidence):
        raise ValueError("content-support evidence is required")
    missing = set(roles) - set(providers)
    if missing:
        raise ValueError("missing providers: " + ", ".join(sorted(missing)))


def validate_draft(draft: ExamDraft, request: MiniRequest, book: IllustrationBook) -> None:
    checks = request.model_copy(deep=True)
    checks.request.include_answers = checks.request.include_solutions = False
    for question in checks.request.question_bank.questions:
        question.answer = question.solution = None
    errors = validate_output(
        ComposerOutput(exam=draft.exam, questions=draft.questions, visuals=draft.visuals),
        checks,
        draft.revision,
    )
    if errors or format_errors(draft):
        raise PipelineFailure("finalizer", "final_validation", "Draft failed final checks.")
    validate_illustrations(book, draft)


def validate_publication(
    draft: ExamDraft,
    request: MiniRequest,
    book: IllustrationBook,
    root: Path,
    source: str,
    previous_student: dict,
    solutions: SolutionBook,
    current_review: ReviewReport | None,
) -> None:
    validate_draft(draft, request, book)
    student, _ = student_view(draft, root, book, source)
    if student != previous_student:
        raise PipelineFailure("finalizer", "stale_artifact", "Merged source changed.")
    validate_solutions(solutions, student)
    if current_review is not None:
        validate_review(current_review, student, solutions)
