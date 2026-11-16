"""120 MCQs with explicit, complete shared-passage and data-table bindings."""

import re
from typing import Literal

from pydantic import Field, field_validator, model_validator

from exam_baseline.core.models import Model, Text
from exam_baseline.thpt.content import choice_latex, content_latex
from exam_baseline.thpt.fonts import DEFAULT_FONT_PROFILE, FontProfile
from exam_baseline.thpt.models import Drawing, Level, Review, Solution
from exam_baseline.vact.template import batches


def canonical_group_id(value):
    # Legacy model responses use p73_74 for the template's g73_74.
    # Only normalize this exact range-preserving spelling, never reorder passages.
    if isinstance(value, str) and re.fullmatch(r"p[1-9][0-9]*_[1-9][0-9]*", value):
        return "g" + value[1:]
    return value


class Slot(Model):
    id: str = Field(pattern=r"^q[1-9][0-9]{0,2}$")
    part: str
    topic: Text
    objective: Text
    level: Level


class Request(Model):
    template_id: Literal["vact_v1"] = "vact_v1"
    font_profile: FontProfile = DEFAULT_FONT_PROFILE
    composer_concurrency: int = Field(default=3, ge=1, le=3, strict=True)
    solver_concurrency: int = Field(default=2, ge=1, le=3, strict=True)
    slots: list[Slot] = Field(min_length=120, max_length=120)
    reference_material: list[Text] = Field(default_factory=list, max_length=20)
    requirements: list[Text] = Field(default_factory=list, max_length=30)

    @model_validator(mode="after")
    def matrix(self):
        expected = [(i, b.id) for b in batches() for i in b.ids]
        if [(s.id, s.part) for s in self.slots] != expected:
            raise ValueError("VACT slots must follow the original template batches and q1..q120")
        return self


class Table(Model):
    columns: list[Text] = Field(min_length=2, max_length=10)
    rows: list[list[Text]] = Field(min_length=1, max_length=40)

    @model_validator(mode="after")
    def rectangular(self):
        if any(len(row) != len(self.columns) for row in self.rows):
            raise ValueError("Table rows must match column count")
        for cell in [*self.columns, *(cell for row in self.rows for cell in row)]:
            content_latex(cell)
        return self


class Passage(Model):
    id: str
    heading: str = ""
    text: Text
    table: Table | None = None

    @field_validator("id", mode="before")
    @classmethod
    def group_id(cls, value):
        return canonical_group_id(value)

    @field_validator("text", "heading")
    @classmethod
    def format_text(cls, value, info):
        content_latex(value, check_equations=info.field_name != "solution")
        return value


class Question(Model):
    id: str = Field(pattern=r"^q[1-9][0-9]{0,2}$")
    stem: Text
    choices: dict[str, Text] = Field(min_length=4, max_length=4)
    answer: Literal["A", "B", "C", "D"]
    solution: Text
    passage_id: str | None = None
    illustration_request: str | None = None

    @field_validator("passage_id", mode="before")
    @classmethod
    def group_id(cls, value):
        return canonical_group_id(value)

    @property
    def statements(self):
        return ()

    @field_validator("stem", "solution")
    @classmethod
    def format_text(cls, value, info):
        content_latex(value, check_equations=info.field_name != "solution")
        return value

    @model_validator(mode="after")
    def four_choices(self):
        if set(self.choices) != set("ABCD") or len(set(self.choices.values())) != 4:
            raise ValueError("VACT requires four distinct choices A/B/C/D")
        for value in self.choices.values():
            choice_latex(value)
        return self


class Section(Model):
    questions: list[Question] = Field(min_length=1, max_length=12)
    passages: list[Passage] = Field(default_factory=list, max_length=6)


class Illustrations(Model):
    drawings: list[Drawing] = Field(default_factory=list, max_length=120)


class SolutionBatch(Model):
    entries: list[Solution] = Field(min_length=1, max_length=12)


class Solutions(Model):
    entries: list[Solution] = Field(min_length=120, max_length=120)


class ReviewReport(Review):
    checked_ids: list[str] = Field(min_length=120, max_length=120)
