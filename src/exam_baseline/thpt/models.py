"""An explicit per-question blueprint; cognitive levels are not inferred from difficulty."""

import re
from typing import Literal

from pydantic import Field, field_validator, model_validator

from exam_baseline.core.models import Model, Text
from exam_baseline.thpt.content import choice_latex, content_latex
from exam_baseline.thpt.fonts import DEFAULT_FONT_PROFILE, FontProfile
from exam_baseline.thpt.visuals import validate_table_source, visual_issues

Level = Literal["NB", "TH", "VD", "VDC"]
Part = Literal["P1", "P2", "P3"]
COUNTS = {"P1": 12, "P2": 4, "P3": 6}


class Slot(Model):
    id: str = Field(pattern=r"^P[123]-[1-9][0-9]?$")
    part: Part
    topic: Text
    objective: Text
    level: Level
    statement_levels: list[Level] = Field(default_factory=list)


class Request(Model):
    template_id: Literal["thpt_math_v2"] = "thpt_math_v2"
    font_profile: FontProfile = DEFAULT_FONT_PROFILE
    composer_concurrency: int = Field(default=3, ge=1, le=3, strict=True)
    slots: list[Slot] = Field(min_length=22, max_length=22)
    reference_material: list[Text] = Field(default_factory=list, max_length=20)
    requirements: list[Text] = Field(default_factory=list, max_length=30)

    @model_validator(mode="after")
    def valid_matrix(self):
        expected = [f"{part}-{i}" for part, count in COUNTS.items() for i in range(1, count + 1)]
        if [s.id for s in self.slots] != expected:
            raise ValueError("slots must be ordered P1-1..12, P2-1..4, P3-1..6")
        for slot in self.slots:
            if not slot.id.startswith(slot.part + "-"):
                raise ValueError("slot part mismatch")
            if len(slot.statement_levels) != (4 if slot.part == "P2" else 0):
                raise ValueError("P2 requires four statement_levels; other parts require none")
        return self


class Statement(Model):
    text: Text
    answer: bool = Field(strict=True)
    solution: Text

    @field_validator("text", "solution")
    @classmethod
    def validate_math_text(cls, value, info):
        content_latex(value, check_equations=info.field_name != "solution")
        return value


class Question(Model):
    id: str
    stem: Text
    choices: dict[str, Text] = Field(default_factory=dict)
    statements: list[Statement] = Field(default_factory=list)
    answer: str | None = None
    solution: Text
    illustration_request: str | None = None

    @field_validator("stem", "solution")
    @classmethod
    def validate_math_text(cls, value, info):
        if info.field_name == "stem":
            validate_table_source(value)
        content_latex(value, check_equations=info.field_name != "solution")
        return value

    @model_validator(mode="after")
    def shape(self):
        if issues := visual_issues(self.stem, self.illustration_request):
            raise ValueError("; ".join(issues))
        for choice in self.choices.values():
            choice_latex(choice)
        if self.id.startswith("P1-"):
            if set(self.choices) != set("ABCD") or self.answer not in self.choices:
                raise ValueError("P1 requires A/B/C/D and a valid answer")
            if len(set(self.choices.values())) != 4 or self.statements:
                raise ValueError("P1 requires distinct choices and no statements")
        elif self.id.startswith("P2-"):
            if len(self.statements) != 4 or self.choices or self.answer is not None:
                raise ValueError("P2 requires exactly four statements and per-statement answers")
        elif self.id.startswith("P3-"):
            if (
                self.choices
                or self.statements
                or not re.fullmatch(r"-?\d+(?:,\d+)?", self.answer or "")
            ):
                raise ValueError("P3 requires a numeric answer using a decimal comma")
            if len(self.answer) > 4:
                raise ValueError("P3 answer must fit four answer cells")
        else:
            raise ValueError("unknown question ID")
        return self


class Section(Model):
    questions: list[Question] = Field(min_length=1, max_length=12)


class MultipleChoiceQuestion(Question):
    answer: Literal["A", "B", "C", "D"]
    choices: dict[str, Text] = Field(min_length=4, max_length=4)


class TrueFalseQuestion(Question):
    statements: list[Statement] = Field(min_length=4, max_length=4)


class ShortAnswerQuestion(Question):
    answer: str = Field(min_length=1, max_length=4, pattern=r"^-?\d+(?:,\d+)?$")


class MultipleChoiceSection(Model):
    questions: list[MultipleChoiceQuestion] = Field(min_length=12, max_length=12)


class TrueFalseSection(Model):
    questions: list[TrueFalseQuestion] = Field(min_length=4, max_length=4)


class ShortAnswerSection(Model):
    questions: list[ShortAnswerQuestion] = Field(min_length=6, max_length=6)


class Drawing(Model):
    question_id: str
    latex: Text


class Illustrations(Model):
    drawings: list[Drawing] = Field(default_factory=list, max_length=22)


class Solution(Model):
    question_id: str
    answer: Text
    reasoning: Text
    status: Literal["solved", "ambiguous", "unsolvable"]


class Solutions(Model):
    entries: list[Solution] = Field(min_length=22, max_length=22)


class Review(Model):
    decision: Literal["approved", "needs_revision"]
    checked_ids: list[str] = Field(min_length=22, max_length=22)
    issues: list[Text] = Field(default_factory=list)

    @model_validator(mode="after")
    def consistent(self):
        if (self.decision == "needs_revision") != bool(self.issues):
            raise ValueError("needs_revision requires actionable issues; approved requires none")
        return self
