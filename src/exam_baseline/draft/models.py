"""Contracts for Composer drafts, visual specifications and handoff artifacts."""

from typing import Literal

from pydantic import Field, TypeAdapter, model_validator

from exam_baseline.core.hashing import digest
from exam_baseline.core.models import GeneratedExam, GenerationRequest, Model, TokenUsage
from exam_baseline.draft.prompts import PROMPT_VERSION, SYSTEM


class Evidence(Model):
    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    role: Literal["content_support", "form_example"]
    locator: str | None = None


class SourceRef(Model):
    evidence_id: str
    role: Literal["content_support", "form_example"]


class VisualSpec(Model):
    visual_id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    question_id: str
    revision: int = Field(ge=1)
    required: bool = True
    purpose: str
    kind: Literal["line_graph", "bar_chart", "geometry_segments"]
    labels: list[str] = Field(default_factory=list)
    units: str | None = None
    x_label: str | None = None
    y_label: str | None = None
    x_domain: tuple[float, float] | None = None
    y_domain: tuple[float, float] | None = None
    points: list[tuple[float, float]] = Field(default_factory=list)
    segments: list[tuple[int, int]] = Field(default_factory=list)
    values: list[float] = Field(default_factory=list)
    scaling: Literal["equal", "linear"] = "linear"

    @model_validator(mode="after")
    def shape(self):
        if self.kind == "line_graph" and (
            len(self.points) < 2 or not self.x_domain or not self.y_domain
        ):
            raise ValueError("line_graph needs points and explicit axis domains")
        if self.kind == "bar_chart" and (not self.values or len(self.values) != len(self.labels)):
            raise ValueError("bar_chart needs one label per value")
        if self.kind == "geometry_segments" and (
            not self.points
            or len(self.labels) != len(self.points)
            or not self.segments
            or any(
                a >= len(self.points) or b >= len(self.points) or a < 0 or b < 0
                for a, b in self.segments
            )
        ):
            raise ValueError("geometry_segments needs labeled points and valid segments")
        if any(domain[0] >= domain[1] for domain in (self.x_domain, self.y_domain) if domain):
            raise ValueError("axis domain must increase")
        if self.kind == "line_graph" and any(
            not self.x_domain[0] <= x <= self.x_domain[1]
            or not self.y_domain[0] <= y <= self.y_domain[1]
            for x, y in self.points
        ):
            raise ValueError("points must lie within axes")
        return self


class DraftQuestion(Model):
    id: str
    source_refs: list[SourceRef] = Field(default_factory=list)
    figure_refs: list[str] = Field(default_factory=list)
    stem_format: Literal["plain", "latex"] = "plain"


class ComposerOutput(Model):
    exam: GeneratedExam
    questions: list[DraftQuestion]
    visuals: list[VisualSpec] = Field(default_factory=list)


class ComposerFailureDetail(Model):
    code: str
    message: str


class ComposerFailure(Model):
    error: ComposerFailureDetail


COMPOSER_RESPONSE = TypeAdapter(ComposerOutput | ComposerFailure)


class MiniRequest(Model):
    request: GenerationRequest
    evidence: list[Evidence] = Field(default_factory=list)
    require_evidence: bool = False
    required_visual_question_ids: list[str] = Field(default_factory=list)
    latex_template: str | None = Field(default=None, max_length=100000)
    user_prompt: str | None = Field(default=None, max_length=10000)
    exam_family: Literal["hcm_dgnl", "thpt"] | None = None

    @model_validator(mode="after")
    def unique_input_ids(self):
        ids = [item.id for item in self.evidence]
        if len(ids) != len(set(ids)):
            raise ValueError("evidence IDs must be unique")
        if len(self.required_visual_question_ids) != len(set(self.required_visual_question_ids)):
            raise ValueError("required visual question IDs must be unique")
        if self.latex_template is not None and "%% ASTRA_BODY %%" not in self.latex_template:
            raise ValueError("latex_template requires %% ASTRA_BODY %% marker")
        return self


class StageError(Model):
    code: str
    stage: Literal["composer", "illustrator"]
    message: str
    artifact_id: str | None = None


class FigureArtifact(Model):
    visual_id: str
    question_id: str
    revision: int
    path: str
    asset_sha256: str
    spec_sha256: str
    mime: Literal["image/png"] = "image/png"
    width_px: int
    height_px: int
    renderer: str = "pillow-primitives-v1"
    status: Literal["succeeded"] = "succeeded"


class StageResult(Model):
    status: Literal["succeeded", "skipped", "failed"]
    errors: list[StageError] = Field(default_factory=list)
    reason: str | None = None
    calls: int = 0
    latency_ms: float | None = None
    usage: TokenUsage = Field(default_factory=TokenUsage)


class ExamDraft(Model):
    schema_version: Literal["mini-v1"] = "mini-v1"
    exam_id: str
    draft_id: str
    revision: int = 1
    exam: GeneratedExam
    questions: list[DraftQuestion]
    visuals: list[VisualSpec]
    figures: list[FigureArtifact] = Field(default_factory=list)
    composer: StageResult
    illustrator: StageResult
    prompt_version: str = PROMPT_VERSION
    prompt_sha256: str = digest(SYSTEM.encode())
    provider: str
    model: str
    input_sha256: str
    output_sha256: str
