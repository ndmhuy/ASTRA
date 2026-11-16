"""Backend-owned requirement ports with an explicitly fictional Phase 1 fixture."""

from __future__ import annotations

import hashlib
import json
from typing import Protocol

from .models import (
    DraftEvaluation,
    RequirementField,
    RequirementPreset,
    RequirementsDescriptor,
    TeacherIntakeDraft,
)


class RequirementsProvider(Protocol):
    def get_descriptor(self) -> RequirementsDescriptor: ...


class DraftEvaluationPort(Protocol):
    def evaluate(
        self, draft: TeacherIntakeDraft, descriptor: RequirementsDescriptor
    ) -> DraftEvaluation: ...


class FixtureRequirementsProvider:
    """Fictional descriptor for offline tests; it is not a backend contract."""

    def __init__(self, descriptor: RequirementsDescriptor | None = None):
        self._descriptor = descriptor or RequirementsDescriptor(
            schema_version="teacher-intake/fixture-0.1",
            availability="mock",
            fields=[
                RequirementField(
                    key="subject",
                    ask_label="môn học",
                    value_type="enum",
                    required=True,
                    allowed_values=["mathematics", "physics", "chemistry"],
                ),
                RequirementField(
                    key="grade",
                    ask_label="khối/lớp",
                    value_type="integer",
                    required=True,
                    minimum=1,
                    maximum=12,
                ),
                RequirementField(
                    key="topics",
                    ask_label="chủ đề kiến thức",
                    value_type="string_list",
                    required=True,
                    depends_on=["subject", "grade"],
                ),
                RequirementField(
                    key="question_count",
                    ask_label="số câu",
                    value_type="integer",
                    required=True,
                    minimum=1,
                    maximum=100,
                ),
                RequirementField(
                    key="duration_minutes",
                    ask_label="thời lượng làm bài",
                    value_type="integer",
                    required=True,
                    minimum=5,
                    maximum=180,
                ),
            ],
            presets=[
                RequirementPreset(
                    preset_id="fixture-practice-20x45",
                    label="Bài luyện tập 20 câu trong 45 phút",
                    values={"question_count": 20, "duration_minutes": 45},
                    source="ASTRA Phase 1 fictional test fixture",
                    version="fixture-0.1",
                )
            ],
        )

    def get_descriptor(self) -> RequirementsDescriptor:
        return self._descriptor.model_copy(deep=True)


def missing_required_fields(
    draft: TeacherIntakeDraft, descriptor: RequirementsDescriptor
) -> list[RequirementField]:
    missing: list[RequirementField] = []
    for field in descriptor.fields:
        if field.key in draft.fields:
            continue
        if field.default is not None:
            continue
        if field.required:
            missing.append(field)
    return missing


def apply_descriptor_defaults(
    draft: TeacherIntakeDraft, descriptor: RequirementsDescriptor, message_id: str
) -> None:
    defaults = {
        field.key: field.default
        for field in descriptor.fields
        if field.default is not None and field.key not in draft.fields
    }
    if defaults:
        draft.patch(defaults, message_id, source="backend_default", status="confirmed")


def validate_collected_values(
    draft: TeacherIntakeDraft, descriptor: RequirementsDescriptor
) -> list[str]:
    errors: list[str] = []
    fields = {item.key: item for item in descriptor.fields}
    for key, collected in draft.fields.items():
        requirement = fields.get(key)
        if requirement is None:
            errors.append(f"unknown field: {key}")
            continue
        value = collected.value
        if requirement.value_type == "integer" and type(value) is not int:
            errors.append(f"{key} must be an integer")
            continue
        if requirement.minimum is not None and value < requirement.minimum:
            errors.append(f"{key} is below minimum {requirement.minimum}")
        if requirement.maximum is not None and value > requirement.maximum:
            errors.append(f"{key} exceeds maximum {requirement.maximum}")
        if requirement.allowed_values and value not in requirement.allowed_values:
            errors.append(f"{key} is not an allowed value")
    return errors


class MockDraftEvaluationPort:
    """Strict local evaluator; never evidence of backend readiness."""

    def evaluate(
        self, draft: TeacherIntakeDraft, descriptor: RequirementsDescriptor
    ) -> DraftEvaluation:
        missing = missing_required_fields(draft, descriptor)
        errors = validate_collected_values(draft, descriptor)
        if errors:
            return DraftEvaluation(
                status="invalid",
                source="mock",
                requirements_schema_version=descriptor.schema_version,
                validation_errors=errors,
            )
        if missing:
            return DraftEvaluation(
                status="needs_input",
                source="mock",
                requirements_schema_version=descriptor.schema_version,
                missing_fields=[field.key for field in missing],
                allowed_suggestions=descriptor.presets,
            )
        values = {key: field.value for key, field in sorted(draft.fields.items())}
        canonical = json.dumps(
            {
                "draft_id": draft.draft_id,
                "revision": draft.revision,
                "schema": descriptor.schema_version,
                "values": values,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        request_hash = hashlib.sha256(canonical.encode()).hexdigest()
        return DraftEvaluation(
            status="validated_ready",
            source="mock",
            requirements_schema_version=descriptor.schema_version,
            normalized_preview={
                "teacher_readable_values": values,
                "disclosure": "MOCK: no ExamMatrix was produced and no backend was called",
            },
            request_hash=request_hash,
        )
