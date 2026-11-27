"""Workspace message persistence only; no provider or academic job is invoked."""

from exam_baseline.ui.contracts import WorkspaceDraft


def test_agent_message_marker_survives_workspace_validation_and_storage():
    draft = WorkspaceDraft.model_validate(
        {
            "schema_version": 1,
            "revision": 0,
            "mode": "custom",
            "title": "Offline workspace fixture",
            "draft": "",
            "messages": [
                {
                    "id": "agent-source",
                    "role": "user",
                    "content": "Open configuration",
                    "timestamp": "2026-11-27T07:00:00Z",
                    "agentTurn": True,
                }
            ],
        }
    )
    assert draft.storage_content()["messages"][0]["agentTurn"] is True
