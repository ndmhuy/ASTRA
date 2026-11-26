"""Validate frontend requests before any retrieval or model call."""

import json
from datetime import datetime
from importlib.resources import files
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, ConfigDict, Field, model_validator

from exam_baseline.core.models import Model
from exam_baseline.thpt.models import Slot
from exam_baseline.thpt.subjects import DURATION, PROFILES, FormatId, subject_catalog
from exam_baseline.vact.models import Slot as VactSlot


def format_catalog(*, demo_mode: bool = False) -> list[dict]:
    resources = files("exam_baseline.resources").joinpath("exam_formats")
    return [
        json.loads(resources.joinpath(name).read_text(encoding="utf-8"))
        for name in ("thpt_math_v1.json", "vact_v1.json")
    ] + [dict(item, available=not demo_mode) for item in subject_catalog()]


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


class SubjectGenerateRequest(Model):
    formatId: FormatId
    formatVersion: Literal["1"] = "1"
    subject: str
    grade: Literal[12]
    examType: Literal["THPT_STANDARD"]
    durationMinutes: Literal[DURATION]
    itemCount: int = Field(strict=True)
    prompt: str = Field(default="", max_length=10000)
    uploadedFiles: list[str] = Field(default_factory=list, max_length=0)

    @model_validator(mode="after")
    def validate_format(self):
        profile = PROFILES[self.formatId]
        if self.subject != profile.subject or self.itemCount != len(profile.ids):
            raise ValueError("Subject and item count must agree with the selected THPT format")
        return self


ExamGenerateRequest = GenerateRequest | VactGenerateRequest | SubjectGenerateRequest


class ExamVersionRef(Model):
    jobId: UUID
    revision: int = Field(ge=1)


class WorkspaceMessage(Model):
    model_config = ConfigDict(str_strip_whitespace=False)

    id: str
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime
    examVersion: ExamVersionRef | None = None
    recorded: bool = False


class WorkspaceContent(Model):
    model_config = ConfigDict(str_strip_whitespace=False)

    schema_version: Literal[1] = 1
    mode: Literal["template", "custom"]
    title: str
    draft: str
    messages: list[WorkspaceMessage]

    def storage_content(self, *exclude: str) -> dict:
        content = self.model_dump(mode="json", exclude={"messages", *exclude})
        content["messages"] = [
            item.model_dump(mode="json", exclude_unset=True) for item in self.messages
        ]
        return content


class WorkspaceDraft(WorkspaceContent):
    revision: int = Field(ge=0, strict=True)


class WorkspaceImport(WorkspaceContent):
    createdAt: AwareDatetime
    jobId: UUID | None


class WorkspaceBranchRequest(Model):
    destinationId: UUID
    messageId: str = Field(min_length=1, max_length=256)
    copyCurrent: bool = False


class PreviewRequest(Model):
    revision: int = Field(ge=1)
    contentHash: str = Field(pattern=r"^[a-f0-9]{64}$")


class ApprovalRequest(PreviewRequest):
    reviewer: str = Field(min_length=1, max_length=120)


class RevisionRequest(Model):
    revision: int = Field(ge=1)


class WorkspaceRestoreRequest(RevisionRequest):
    jobId: UUID
    targetJobId: UUID
    targetRevision: int = Field(ge=1)


class EditRequest(RevisionRequest):
    question: dict


class RegenerateRequest(RevisionRequest):
    instruction: str = Field(default="Sửa câu hỏi và kiểm tra lại lời giải.", max_length=4000)
