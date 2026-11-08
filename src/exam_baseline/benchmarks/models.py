from pydantic import Field

from exam_baseline.core.models import Model


class Case(Model):
    id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    track: str = Field(pattern="^(text|visual)$")
    request: str
    fixtures: str


class Manifest(Model):
    repeats: int = Field(default=2, ge=1, le=10)
    cases: list[Case] = Field(min_length=1)


class HumanLabel(Model):
    correct_questions: int = Field(ge=0)
    requested_questions: int = Field(gt=0)
    required_figures: int = Field(default=0, ge=0)
    usable_figures: int = Field(default=0, ge=0)
    gold_defects: int = Field(default=0, ge=0)
    true_positive_defects: int = Field(default=0, ge=0)
    predicted_defects: int = Field(default=0, ge=0)
    clean_case: bool = False
    false_alarm: bool = False
    format_correct_questions: int | None = Field(default=None, ge=0)
    valid_questions: int | None = Field(default=None, ge=0)
    test_fit_questions: int | None = Field(default=None, ge=0)
