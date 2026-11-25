"""Validate frontend requests before any retrieval or model call."""

import json
from importlib.resources import files
from typing import Literal

from pydantic import Field, model_validator

from exam_baseline.core.models import Model
from exam_baseline.thpt.models import Slot
from exam_baseline.vact.models import Slot as VactSlot


def format_catalog() -> list[dict]:
    resources = files("exam_baseline.resources").joinpath("exam_formats")
    return [
        json.loads(resources.joinpath(name).read_text(encoding="utf-8"))
        for name in ("thpt_math_v1.json", "vact_v1.json")
    ]


class GenerateRequest(Model):
    formatId: Literal["thpt-math"] = "thpt-math"
    formatVersion: Literal["1"] = "1"
    subject: Literal["Toán Học"]
    grade: Literal[12]
    examType: Literal["THPT_STANDARD"]
    durationMinutes: Literal[90]
    itemCount: Literal[22]
    prompt: str = Field(default="", max_length=10000)
    uploadedFiles: list[str] = Field(default_factory=list, max_length=0)
    slots: list[Slot] | None = None

    @model_validator(mode="after")
    def validate_slots(self):
        if self.slots is not None:
            from exam_baseline.thpt.models import Request

            Request(slots=self.slots)
        return self


class VactGenerateRequest(Model):
    formatId: Literal["vact"] = "vact"
    formatVersion: Literal["1"] = "1"
    subject: Literal["Tổng hợp"]
    grade: Literal[12]
    examType: Literal["DGNL_DHQG"]
    durationMinutes: Literal[150]
    itemCount: Literal[120]
    prompt: str = Field(default="", max_length=10000)
    uploadedFiles: list[str] = Field(default_factory=list, max_length=0)
    slots: list[VactSlot] | None = None

    @model_validator(mode="after")
    def validate_slots(self):
        if self.slots is not None:
            from exam_baseline.vact.models import Request as VactRequest

            VactRequest(slots=self.slots)
        return self


ExamGenerateRequest = GenerateRequest | VactGenerateRequest


class PreviewRequest(Model):
    revision: int = Field(ge=1)
    contentHash: str = Field(pattern=r"^[a-f0-9]{64}$")


class ApprovalRequest(PreviewRequest):
    reviewer: str = Field(min_length=1, max_length=120)


class EditRequest(Model):
    revision: int = Field(ge=1)
    question: dict


class RegenerateRequest(Model):
    revision: int = Field(ge=1)
    instruction: str = Field(default="Sửa câu hỏi và kiểm tra lại lời giải.", max_length=4000)
