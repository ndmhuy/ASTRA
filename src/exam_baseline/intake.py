"""Strict boundary between chatbot intent, RAG context and the mini Composer."""

import argparse
import json
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from .core.models import AdditionalContext, ExamMatrix, GenerationRequest, Model
from .draft.models import Evidence, MiniRequest
from .pipeline.contracts import PipelineRequest


class ChatbotIntent(Model):
    """The chatbot must resolve ambiguity before submitting this contract."""

    intent: Literal["generate_exam"]
    grade: int = Field(ge=1, le=12, strict=True)
    curriculum: str = Field(min_length=1)
    textbook: str = Field(min_length=1)
    textbook_year: int = Field(ge=2000, le=2100, strict=True)
    language: Literal["vi", "en"] = "vi"
    matrix: ExamMatrix
    exam_format: Literal["practice", "quiz", "midterm", "final"]
    answer_format: Literal["answer_only", "worked_solutions"]
    audience: Literal["student", "teacher"] = "teacher"
    accommodations: list[str] = Field(default_factory=list)


class RagPassage(Model):
    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    role: Literal["content_support", "form_example"]
    source_title: str = Field(min_length=1)
    locator: str = Field(min_length=1)
    subject: str = Field(min_length=1)
    grade: int = Field(ge=1, le=12, strict=True)
    textbook: str = Field(min_length=1)
    textbook_year: int = Field(ge=2000, le=2100, strict=True)
    topic_ids: list[str] = Field(min_length=1)


class UserInput(Model):
    request_text: str = Field(min_length=1, max_length=10000)
    additional_constraints: list[str] = Field(default_factory=list)


class Intake(Model):
    schema_version: Literal["mas-intake-v1"] = "mas-intake-v1"
    chatbot: ChatbotIntent
    user: UserInput | None = None
    rag: list[RagPassage] = Field(min_length=1)
    required_visual_question_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def policy(self):
        intent = self.chatbot
        if len({passage.id for passage in self.rag}) != len(self.rag):
            raise ValueError("RAG passage IDs must be unique")
        topics = {topic.id for topic in intent.matrix.topics}
        for passage in self.rag:
            if (
                passage.subject != intent.matrix.subject
                or passage.grade != intent.grade
                or passage.textbook != intent.textbook
                or passage.textbook_year != intent.textbook_year
                or not set(passage.topic_ids) <= topics
            ):
                raise ValueError(f"RAG passage {passage.id} conflicts with exam scope")
        supported = {
            topic
            for passage in self.rag
            if passage.role == "content_support"
            for topic in passage.topic_ids
        }
        missing = {topic.id for topic in intent.matrix.topics if topic.question_count} - supported
        if missing:
            raise ValueError(f"Topics lack content-support RAG evidence: {sorted(missing)}")
        return self


def encode_intake(intake: Intake) -> MiniRequest:
    intent = intake.chatbot
    context = AdditionalContext(
        custom_requirements=[
            f"Grade: {intent.grade}; curriculum: {intent.curriculum}; textbook: "
            f"{intent.textbook} ({intent.textbook_year}); language: {intent.language}.",
            f"Exam format: {intent.exam_format}; answer format: {intent.answer_format}; "
            f"audience: {intent.audience}.",
            *intent.accommodations,
            *(intake.user.additional_constraints if intake.user else []),
        ]
    )
    return MiniRequest(
        request=GenerationRequest(
            matrix=intent.matrix,
            context=context,
            include_answers=True,
            include_solutions=intent.answer_format == "worked_solutions",
        ),
        evidence=[
            Evidence(id=p.id, text=p.text, role=p.role, locator=f"{p.source_title} — {p.locator}")
            for p in intake.rag
        ],
        require_evidence=True,
        required_visual_question_ids=intake.required_visual_question_ids,
        user_prompt=intake.user.request_text if intake.user else None,
    )


def encode_pipeline(intake: Intake) -> PipelineRequest:
    """Apply the same policy at the four-agent pipeline boundary."""
    return PipelineRequest.model_validate(encode_intake(intake).model_dump())


def encode_thpt_retrieval(request, retrieval: dict):
    """Bind the RAG team's rich handoff to THPT slots without changing source metadata.

    THPT includes prerequisite material from grades 10/11, so the older generic
    intake's same-grade restriction must not be bypassed by relabeling that material.
    Preserve the original mas_intake_rag records in the job's private provenance.
    """
    if retrieval.get("status") != "success" or retrieval.get("gaps"):
        raise ValueError("RAG reported missing evidence; generation cannot proceed")
    expected = {slot.id for slot in request.slots}
    contexts = retrieval.get("question_contexts", [])
    entries = retrieval.get("mas_intake_rag", [])
    context_ids = [entry.get("question_id") for entry in contexts]
    entry_ids = [entry.get("question_id") for entry in entries]
    if (
        len(context_ids) != len(expected)
        or set(context_ids) != expected
        or len(entry_ids) != len(expected)
        or set(entry_ids) != expected
    ):
        raise ValueError("RAG handoff must cover every THPT slot exactly once")
    groups = {part: [] for part in ("P1", "P2", "P3")}
    for entry in entries:
        if entry.get("subject") != "Toán" or not entry.get("text", "").strip():
            raise ValueError("RAG handoff must contain nonempty mathematics evidence")
        groups[entry["question_id"].split("-")[0]].append(entry["text"])
    # Three section-scoped contexts fit the existing max-20 reference contract.
    return request.model_copy(
        update={
            "reference_material": [
                f"[THPT_PART:{part}]\n" + "\n\n".join(group) for part, group in groups.items()
            ]
        }
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate chatbot/RAG intake and write MiniRequest JSON"
    )
    parser.add_argument("--input", type=Path, help="Combined intake JSON")
    parser.add_argument("--user", type=Path, help="Separate user input JSON")
    parser.add_argument("--chatbot", type=Path, help="Separate chatbot intent JSON")
    parser.add_argument("--rag", type=Path, help="Separate RAG passage array JSON")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--pipeline", action="store_true", help="Write a four-agent PipelineRequest"
    )
    args = parser.parse_args()
    if args.input:
        if any((args.user, args.chatbot, args.rag)):
            parser.error("--input cannot be combined with separate JSON files")
        intake = Intake.model_validate_json(args.input.read_text(encoding="utf-8"))
    else:
        if not all((args.user, args.chatbot, args.rag)):
            parser.error("supply --input or all of --user, --chatbot and --rag")
        intake = Intake.model_validate(
            {
                "user": json.loads(args.user.read_text(encoding="utf-8")),
                "chatbot": json.loads(args.chatbot.read_text(encoding="utf-8")),
                "rag": json.loads(args.rag.read_text(encoding="utf-8")),
            }
        )
    encoded = encode_pipeline(intake) if args.pipeline else encode_intake(intake)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(encoded.model_dump_json(indent=2, exclude_none=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
