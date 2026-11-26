"""Validate frontend requests before any retrieval or model call."""

import json
from importlib.resources import files
from typing import Literal

from pydantic import Field, model_validator

from exam_baseline.core.models import Model
from exam_baseline.thpt.models import Slot
from exam_baseline.thpt2026.contract import (
    CONTRACT_FORMAT_IDS,
    catalog_entries,
    profile_by_format_id,
)
from exam_baseline.vact.models import Slot as VactSlot


def format_catalog() -> list[dict]:
    resources = files("exam_baseline.resources").joinpath("exam_formats")
    base = [
        json.loads(resources.joinpath(name).read_text(encoding="utf-8"))
        for name in ("thpt_math_v1.json", "vact_v1.json")
    ]
    return [*base, *catalog_entries()]


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


class ContractThptGenerateRequest(Model):
    formatId: Literal[
        "thpt_literature_2026",
        "thpt_english_2026",
        "thpt_history_2026",
        "thpt_geography_2026",
        "thpt_chemistry_2026",
        "thpt_biology_2026",
    ]
    formatVersion: Literal["1"] = "1"
    subject: str
    grade: Literal[12]
    examType: Literal["THPT_STANDARD"]
    durationMinutes: int
    itemCount: int
    prompt: str = Field(default="", max_length=10000)
    uploadedFiles: list[str] = Field(default_factory=list, max_length=0)

    @model_validator(mode="after")
    def validate_profile(self):
        if self.formatId not in CONTRACT_FORMAT_IDS:
            raise ValueError(f"Unsupported contract formatId: {self.formatId}")
        profile = profile_by_format_id(self.formatId)
        if profile is None:
            raise ValueError(f"Missing contract profile for {self.formatId}")
        if self.subject != profile["displayName"]:
            raise ValueError(f"subject must match contract displayName '{profile['displayName']}'")
        if self.durationMinutes != profile["durationMinutes"]:
            raise ValueError(
                f"durationMinutes must be {profile['durationMinutes']} for {self.formatId}"
            )
        if self.itemCount != profile["totalQuestions"]:
            raise ValueError(f"itemCount must be {profile['totalQuestions']} for {self.formatId}")
        return self


ExamGenerateRequest = GenerateRequest | VactGenerateRequest | ContractThptGenerateRequest


class PreviewRequest(Model):
    revision: int = Field(ge=1)
    contentHash: str = Field(pattern=r"^[a-f0-9]{64}$")


class ApprovalRequest(PreviewRequest):
    reviewer: str = Field(min_length=1, max_length=120)


class RevisionRequest(Model):
    revision: int = Field(ge=1)


class EditRequest(RevisionRequest):
    question: dict


class RegenerateRequest(RevisionRequest):
    instruction: str = Field(default="Sửa câu hỏi và kiểm tra lại lời giải.", max_length=4000)
