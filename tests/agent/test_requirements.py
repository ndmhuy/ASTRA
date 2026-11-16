from exam_baseline.agent.models import RequirementField, RequirementsDescriptor, TeacherIntakeDraft
from exam_baseline.agent.requirements import (
    FixtureRequirementsProvider,
    MockDraftEvaluationPort,
    apply_descriptor_defaults,
)


def draft(version="v1"):
    return TeacherIntakeDraft(
        draft_id="d1",
        conversation_id="c1",
        workspace_session_id="w1",
        requirements_schema_version=version,
    )


def test_descriptor_change_automatically_changes_missing_fields():
    base = FixtureRequirementsProvider().get_descriptor()
    modified = base.model_copy(
        update={
            "fields": base.fields
            + [
                RequirementField(
                    key="language",
                    ask_label="ngôn ngữ",
                    value_type="enum",
                    required=True,
                    allowed_values=["vi", "en"],
                )
            ]
        }
    )
    item = draft(base.schema_version)
    item.patch(
        {
            "subject": "mathematics",
            "grade": 12,
            "topics": ["đạo hàm"],
            "question_count": 20,
            "duration_minutes": 45,
        },
        "m1",
    )
    evaluation = MockDraftEvaluationPort().evaluate(item, modified)
    assert evaluation.missing_fields == ["language"]


def test_backend_default_is_applied_and_disclosed():
    descriptor = RequirementsDescriptor(
        schema_version="fixture-default",
        availability="mock",
        fields=[
            RequirementField(
                key="language",
                ask_label="ngôn ngữ",
                value_type="enum",
                required=True,
                default="vi",
                allowed_values=["vi", "en"],
            )
        ],
    )
    item = draft(descriptor.schema_version)
    apply_descriptor_defaults(item, descriptor, "system-default")
    assert item.fields["language"].source == "backend_default"
    assert item.fields["language"].status == "confirmed"


def test_suggestion_is_not_applied_by_evaluation():
    descriptor = FixtureRequirementsProvider().get_descriptor()
    item = draft(descriptor.schema_version)
    evaluation = MockDraftEvaluationPort().evaluate(item, descriptor)
    assert evaluation.allowed_suggestions
    assert "question_count" not in item.fields


def test_patch_invalidates_preview_and_approval():
    item = draft()
    item.patch({"question_count": 20}, "m1")
    item.normalized_preview = {"value": 20}
    item.request_hash = "hash"
    item.approved_revision = item.revision
    item.patch({"question_count": 15}, "m2")
    assert item.fields["question_count"].value == 15
    assert item.normalized_preview is None
    assert item.request_hash is None
    assert item.approved_revision is None


def test_empty_or_unaccepted_topics_do_not_complete_intake():
    descriptor = FixtureRequirementsProvider().get_descriptor()
    item = draft(descriptor.schema_version)
    item.patch({"topics": []}, "m1")
    assert "topics" in MockDraftEvaluationPort().evaluate(item, descriptor).missing_fields
    item.patch({"topics": ["đạo hàm"]}, "m2", status="suggested")
    assert "topics" in MockDraftEvaluationPort().evaluate(item, descriptor).missing_fields


def test_wrong_topic_type_is_invalid_instead_of_crashing():
    descriptor = FixtureRequirementsProvider().get_descriptor()
    item = draft(descriptor.schema_version)
    item.patch({"topics": 12}, "m1")
    assert MockDraftEvaluationPort().evaluate(item, descriptor).status == "invalid"
