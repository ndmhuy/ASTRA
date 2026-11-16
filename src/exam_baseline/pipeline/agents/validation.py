"""Solution and review invariants independent of agent implementations."""

from pydantic import BaseModel

from exam_baseline.pipeline.contracts import ReviewReport, SolutionBook
from exam_baseline.pipeline.views import solution_hash


def validate_solutions(book: SolutionBook, student: dict) -> None:
    _identity(book, student)
    questions = {q["id"]: q for q in student["exam"]["questions"]}
    if len(book.entries) != len(questions) or {e.question_id for e in book.entries} != set(
        questions
    ):
        raise ValueError("solutions must cover each question exactly once")
    for entry in book.entries:
        question = questions[entry.question_id]
        if entry.solvability != "solvable":
            continue
        if (
            question["question_type"] == "multiple_choice"
            and entry.answer not in question["choices"]
        ):
            raise ValueError("multiple_choice answers must be existing choice keys")
        if question["question_type"] == "true_false" and entry.answer not in {"true", "false"}:
            raise ValueError("true_false answers must be true or false")


def validate_review(report: ReviewReport, student: dict, book: SolutionBook) -> None:
    _identity(report, student)
    question_ids = {q["id"] for q in student["exam"]["questions"]}
    if report.solution_sha256 != solution_hash(book):
        raise ValueError("review must reference the current solution book hash")
    if (
        len(report.checked_question_ids) != len(question_ids)
        or set(report.checked_question_ids) != question_ids
    ):
        raise ValueError("review must explicitly cover each question exactly once")
    visual_ids = {image["visual_id"] for image in student["image_manifest"]}
    visual_ids.update(d["visual_id"] for d in student.get("drawing_source", []))
    for issue in report.issues:
        if issue.question_id is not None and issue.question_id not in question_ids:
            raise ValueError("review issue references an unknown question")
        if issue.visual_id is not None and issue.visual_id not in visual_ids:
            raise ValueError("review issue references an unknown image")
    if report.decision == "approved" and any(e.solvability != "solvable" for e in book.entries):
        raise ValueError("cannot approve ambiguous or unsolvable questions")


def _identity(output: BaseModel, student: dict) -> None:
    for field in ("exam_id", "draft_id", "revision", "artifact_sha256"):
        if getattr(output, field) != student[field]:
            raise ValueError(f"{field} must match the current artifact exactly")
