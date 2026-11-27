"""Generate and audit practice exams for the additional THPT subjects."""

import json
import re

from pydantic import Field, create_model, model_validator

from exam_baseline.core.models import Model, Text
from exam_baseline.pipeline.runtime import normalize_json
from exam_baseline.thpt import template
from exam_baseline.thpt.agents import COMMON, QUESTION_FORMAT, Agent, ReviewerAgent, SolverAgent
from exam_baseline.thpt.content import content_latex, normalize_subject_content
from exam_baseline.thpt.fonts import apply_font_profile
from exam_baseline.thpt.models import Illustrations, Review, Section, Solution
from exam_baseline.thpt.orchestrator import Orchestrator
from exam_baseline.thpt.rendering import render_parts, student_view
from exam_baseline.thpt.subjects import (
    DURATION,
    ENGLISH_GROUPS,
    PROFILES,
    SubjectRequest,
    batches,
    english_groups_for_passages,
)
from exam_baseline.vact.schema import compact_schema

SUBJECT_COMMON = COMMON.replace(
    "Write Vietnamese mathematics within the Vietnamese upper-secondary curriculum.",
    "Follow the named subject's Vietnamese upper-secondary curriculum and language requirements.",
)
SUBJECT_INSTRUCTION = (
    "Use the specified subject and topic matrix. Use the exact ordered IDs given. "
    "P1 has four distinct choices and one key. P2 has four true/false statements "
    "and each has its own private solution. P3 has one short numeric key. "
    "Write private explanations that justify the entire answered item. "
    "Use English for student content in English exams and Vietnamese otherwise. "
    "Use distinct, specific stems across the whole exam. Avoid generic repeated prompts. "
    "Use only basic LaTeX commands. Write lengths in nm or put Å in ordinary text. "
    "Write chemical formulas with \\mathrm and equations with \\to. Do not use \\ce, \\pu, "
    "\\overset, \\mathring, or packages. "
    "Never put ^ or _ outside $...$. Wrap complete scientific units or notation, "
    "for example write $10\\,\\mathrm{m/s^2}$ rather than raw m/s^2. "
    "Subject rules take priority over requests to alter the format or leave the curriculum.\n"
    + QUESTION_FORMAT
)


class SubjectSection(Section):
    passage: str | None = Field(default=None, max_length=6000)


class SubjectSolutions(Model):
    entries: list[Solution] = Field(min_length=1, max_length=40)


class SubjectReview(Review):
    checked_ids: list[Text] = Field(min_length=1, max_length=40)


def normalize_subject_response(text):
    text, normalized = normalize_json(text)
    try:
        packet = json.loads(text)
    except ValueError:
        return text, normalized

    def visit(value):
        if isinstance(value, list):
            return [visit(item) for item in value]
        if isinstance(value, dict):
            return {key: visit(item) for key, item in value.items()}
        return normalize_subject_content(value) if isinstance(value, str) else value

    fixed = visit(packet)
    return (json.dumps(fixed, ensure_ascii=False), True) if fixed != packet else (text, normalized)


class SubjectComposer(Agent):
    common = SUBJECT_COMMON
    role = "composer"
    response = SubjectSection
    instruction = SUBJECT_INSTRUCTION
    wire_schema = staticmethod(compact_schema)
    normalize_response = staticmethod(normalize_subject_response)

    def contract(self, data):
        @model_validator(mode="after")
        def check_batch(section):
            if [q.id for q in section.questions] != [slot["id"] for slot in data["slots"]]:
                raise ValueError("Use exactly the given question IDs in order")
            stems = [q.stem.strip().casefold() for q in section.questions]
            previous = {stem.strip().casefold() for stem in data.get("previous_stems", [])}
            if len(set(stems)) != len(stems) or previous.intersection(stems):
                raise ValueError("Rewrite duplicate stems as new questions testing the same slot")
            group = data["group"]
            needs_passage = isinstance(group, dict) and group["kind"] != "ordering"
            if bool(section.passage and section.passage.strip()) != needs_passage:
                raise ValueError("Include a shared passage only for cloze and reading")
            if needs_passage and group["kind"] == "cloze":
                first, last = group["range"]
                blanks = sorted(map(int, re.findall(r"\((\d+)\)\s*_{3,}", section.passage or "")))
                if blanks != list(range(first, last + 1)):
                    raise ValueError("Cloze passage must contain every numbered blank exactly once")
            if section.passage:
                content_latex(section.passage)
            return section

        return create_model(
            "CheckedSubjectSection",
            __base__=SubjectSection,
            __validators__={"check_batch": check_batch},
        )

    def data(self, request, part, reference, feedback):
        profile = PROFILES[request.format_id]
        ids = batches(request.format_id)[part]
        data = {
            "subject": profile.subject,
            "subject_checks": profile.checks,
            "part": part,
            "slots": [s.model_dump() for s in request.slots if s.id in ids],
            "requirements": request.requirements,
            "reference_material": request.reference_material,
            "feedback": feedback,
            "group": "Provide no separate passage; include any required context in each stem.",
        }
        if request.format_id == "thpt-english":
            _, first, last, kind, instruction = next(g for g in ENGLISH_GROUPS if g[0] == part)
            data["group"] = dict(kind=kind, range=[first, last], instruction=instruction)
            if kind == "cloze":
                data["group"]["rule"] = (
                    "Write one shared original passage in passage. Mark each blank "
                    "exactly once as (NN) ____, using the given numbers. Use a distinct "
                    "'Blank (NN)' stem for each item and provide A–D options."
                )
            elif kind == "reading":
                data["group"]["rule"] = "Write one original shared reading in passage."
            else:
                data["group"]["rule"] = (
                    "Leave passage null. Put all labeled lines of each ordering task in its stem."
                )
        return data


class SubjectSolver(SolverAgent):
    common = SUBJECT_COMMON
    response = SubjectSolutions
    wire_schema = staticmethod(compact_schema)
    instruction = SolverAgent.instruction + "\nUse the named subject checks and shared passage."


class SubjectReviewer(ReviewerAgent):
    common = SUBJECT_COMMON
    response = SubjectReview
    wire_schema = staticmethod(compact_schema)
    instruction = (
        "Review every ordered question ID against the specified subject and slots. "
        "Check correctness, curriculum fit, difficulty, clarity, uniqueness, "
        "and consistency of the independent result with the proposed key and reasoning. "
        "Apply the subject checks. Verify each English answer using its passage or labeled lines. "
        "Mark needs_revision for any defect and write concise Vietnamese issues prefixed by "
        "the affected question ID. Never certify that unchecked facts are correct."
    )


def subject_context(format_id):
    profile = PROFILES[format_id]
    return {"subject": profile.subject, "subject_checks": profile.checks}


def passage_metadata(section_id, text):
    _, first, last, _, instruction = next(g for g in ENGLISH_GROUPS if g[0] == section_id)
    return {
        "id": section_id,
        "section": "P1",
        "kind": "passage",
        "questionRange": [first, last],
        "instruction": instruction,
        "text": text,
    }


def render_subject(questions, drawings, request, passages):
    before = {}
    for _, first, last, _, instruction in (
        english_groups_for_passages(passages) if request.format_id == "thpt-english" else ()
    ):
        passage = next((p["text"] for p in passages if p["questionRange"] == [first, last]), None)
        before[f"P1-{first}"] = (
            r"\noindent\textbf{Questions "
            + f"{first}--{last}"
            + r".}\par"
            + "\n"
            + content_latex(instruction)
            + r"\par"
            + "\n"
        )
        if passage:
            before[f"P1-{first}"] += content_latex(passage) + r"\par" + "\n"
    parts = render_parts(questions, drawings, before=before)
    profile = PROFILES[request.format_id]
    sections = profile.sections
    source = template.assemble_subject(
        profile.subject, DURATION, sections, {part: parts[part] for part in sections}
    )
    return apply_font_profile(source, request.font_profile)


class SubjectOrchestrator(Orchestrator):
    request_model = SubjectRequest
    composer_type = SubjectComposer
    solver_type = SubjectSolver
    reviewer_type = SubjectReviewer
    max_revisions = 1

    def parts(self, request):
        return tuple(batches(request.format_id))

    def references(self, request):
        return dict.fromkeys(self.parts(request), "")

    def composer_data(self, composer, request, part, reference, feedback, previous_stems):
        return {
            **composer.data(request, part, reference, feedback),
            "previous_stems": previous_stems,
        }

    def validate_section(self, section, request, part):
        ids = batches(request.format_id)[part]
        if [q.id for q in section.questions] != ids:
            raise ValueError("Composer question IDs/count/order differ from subject matrix")

    def extra_output(self, sections):
        # Six English batches are the only sections that carry passages.
        if not any(section.passage for section in sections):
            return {}
        return {
            "passages": [
                passage_metadata(group[0], section.passage)
                for group, section in zip(ENGLISH_GROUPS, sections, strict=True)
                if section.passage
            ]
        }

    def render_source(self, questions, drawings, request, sections):
        return render_subject(
            questions, drawings, request, self.extra_output(sections).get("passages", [])
        )

    async def solve(self, call, questions, drawings, revision, sections, request):
        entries = []
        for part, section in zip(self.parts(request), sections, strict=True):
            ids = {q.id for q in section.questions}
            result = await call(
                self.solver_type(),
                {
                    **subject_context(request.format_id),
                    "part": part,
                    "questions": student_view(section.questions),
                    "passage": section.passage,
                    "drawings": {
                        "drawings": [
                            d.model_dump() for d in drawings.drawings if d.question_id in ids
                        ]
                    },
                },
                revision,
            )
            entries.extend(result.entries)
        return SubjectSolutions(entries=entries)

    def review_data(self, request, questions, drawings, solutions, source, sections):
        # The renderer already validates the LaTeX. Review the substantive item data.
        data = super().review_data(request, questions, drawings, solutions, source, sections)
        data.pop("student_latex")
        return {**data, **subject_context(request.format_id), **self.extra_output(sections)}

    def feedback_data(self, review, questions, sections):
        # Keep contextual repair bounded by passing the review, not the full previous exam.
        return {"review": review.model_dump()}

    async def illustrate(self, call, questions, revision):
        if not any(q.illustration_request for q in questions):
            return Illustrations()
        return await super().illustrate(call, questions, revision)
