from pydantic import Field, model_validator

from exam_baseline.core.models import Model


class Case(Model):
    id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    track: str = Field(pattern="^(text|visual)$")
    request: str
    fixtures: str


class Manifest(Model):
    repeats: int = Field(default=2, ge=1, le=10)
    cases: list[Case] = Field(min_length=1)


class QuestionLabel(Model):
    question_id: str = Field(min_length=1)
    accurate: bool
    format_correct: bool
    valid: bool
    test_fit: bool
    reason: str = Field(min_length=8)


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
    question_labels: list[QuestionLabel] = Field(default_factory=list)

    @model_validator(mode="after")
    def consistent_question_labels(self):
        items = self.question_labels
        if not items:
            return self
        if len({item.question_id for item in items}) != len(items):
            raise ValueError("question labels must have unique IDs")
        counts = (
            (self.correct_questions, "accurate"),
            (self.format_correct_questions, "format_correct"),
            (self.valid_questions, "valid"),
            (self.test_fit_questions, "test_fit"),
        )
        for expected, field in counts:
            if expected is not None and expected != sum(getattr(item, field) for item in items):
                raise ValueError(f"question labels disagree with {field} count")
        return self
