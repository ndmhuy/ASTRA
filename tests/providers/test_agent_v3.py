"""V3 boundaries and explicit legacy compatibility. All transports are fakes."""

import asyncio
import json
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from exam_baseline.agent.contracts import Decision
from exam_baseline.agent.native import gemini_request, parse_native
from exam_baseline.agent.provider import ProviderRouter
from exam_baseline.agent.research import ResearchRequest
from exam_baseline.agent.semantics import SemanticFrame
from exam_baseline.agent.v3 import GOALS, REGISTRY, FrameV3, TurnV3, normalize_frame, upgrade_legacy
from exam_baseline.agent.worker import WorkerInterpretationProvider
from exam_baseline.api.app import create_app
from exam_baseline.config import Settings
from exam_baseline.ui.contracts import AdjacentGenerateRequest


def turn():
    return TurnV3(
        schemaVersion="astra-intent-v1",
        workspaceId=str(uuid4()),
        clientMessageId=str(uuid4()),
        message="Fixture natural request",
        context={
            "screen": "workspace",
            "setup": False,
            "grounded": {
                "workspace": "Hóa fixture",
                "lifecycle": "paused",
                "spec": ["subject: Hóa"],
                "documents": ["source.txt (supplementary, 30 characters)"],
                "itemRegeneration": True,
            },
        },
    )


def test_native_v3_registry_covers_all_local_and_new_goals_without_executable_ids():
    limits = REGISTRY["limits"]["practice"]
    generated = AdjacentGenerateRequest.model_json_schema()["properties"]
    research = ResearchRequest.model_json_schema()["properties"]
    assert (limits["countMin"], limits["countMax"]) == (
        generated["itemCount"]["minimum"],
        generated["itemCount"]["maximum"],
    )
    assert (limits["minutesMin"], limits["minutesMax"]) == (
        generated["durationMinutes"]["minimum"],
        generated["durationMinutes"]["maximum"],
    )
    assert limits["uploadedFilesMax"] == generated["uploadedFiles"]["maxItems"]
    minute = next(item for item in research["minutes"]["anyOf"] if item.get("type") == "integer")
    assert limits["researchMinutesMax"] == minute["maximum"]
    assert limits["researchMessageMax"] == research["message"]["maxLength"]
    request = gemini_request(turn(), 512)
    schema = request["generationConfig"]["responseJsonSchema"]
    assert set(schema["properties"]["goals"]["items"]["properties"]["goal"]["enum"]) == set(GOALS)
    for name in GOALS:
        assert (
            normalize_frame({"dialogueAct": "REQUEST", "goals": [{"goal": name}]}).goals[0].goal
            == name
        )
    with pytest.raises(ValidationError):
        normalize_frame(
            {
                "dialogueAct": "REQUEST",
                "goals": [{"goal": "VERIFY_ANSWER", "parameters": {"jobId": "invented"}}],
            }
        )
    with pytest.raises(ValidationError):
        normalize_frame(
            {
                "dialogueAct": "REQUEST",
                "goals": [{"goal": "PREPARE_EXAM", "parameters": {"grade": 13}}],
            }
        )
    proposal = {
        "dialogueAct": "QUESTION",
        "goals": [{"goal": "LIST_DOCUMENTS"}],
        "title": {"bad": True},
    }
    payload = {
        "candidates": [
            {"finishReason": "STOP", "content": {"parts": [{"text": json.dumps(proposal)}]}}
        ]
    }
    assert parse_native("gemini", payload, v3=True).title is None


def test_explicit_bridge_preserves_non_action_and_negation_without_raw_reinterpretation():
    legacy = SemanticFrame(
        dialogueAct="QUESTION",
        goals=[{"goal": "INSPECT_FORMAT", "parameters": {"subject": "Hóa"}}],
        constraints=["NO_GENERATION"],
    )
    upgraded = upgrade_legacy(legacy)
    assert upgraded.dialogueAct == "QUESTION"
    assert upgraded.constraints == ["NO_GENERATION"]
    assert upgraded.goals[0].goal == "READ_EXAM_STRUCTURE"
    assert upgraded.goals[0].parameters == {"subject": "Hóa"}


@pytest.mark.parametrize("version", ["astra-semantic-v1", "astra-semantic-v3"])
def test_worker_version_routes_and_bounded_context_are_negotiated_explicitly(version):
    async def run():
        seen = []

        def fake(request):
            seen.append(request)
            body = json.loads(request.content)
            assert request.url.path == (
                "/v3/agent/interpret" if version.endswith("v3") else "/v2/agent/interpret"
            )
            assert ("grounded" in body["context"]) == version.endswith("v3")
            assert "x-astra-contract" in request.headers
            return httpx.Response(
                200,
                json={
                    "schemaVersion": version,
                    "clientMessageId": body["clientMessageId"],
                    "frame": {
                        "schemaVersion": version,
                        "dialogueAct": "REQUEST",
                        "goals": [
                            {
                                "goal": "PAUSE_GENERATION"
                                if version.endswith("v3")
                                else "OPEN_CONFIGURATION"
                            }
                        ],
                    },
                    "evidence": {"attempts": 1},
                },
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(fake)) as client:
            router = ProviderRouter(
                WorkerInterpretationProvider(
                    client, "https://fixture.invalid", semantic=True, semantic_version=version
                ),
                reserve=lambda: True,
            )
            result = await router(turn())
            assert result.schemaVersion == version
            assert len(seen) == 1

    asyncio.run(run())


@pytest.mark.parametrize(
    "result",
    [
        SemanticFrame(
            dialogueAct="QUESTION",
            goals=[{"goal": "PREPARE_EXAM", "parameters": {"family": "thpt"}}],
        ),
        FrameV3(dialogueAct="REQUEST", goals=[{"goal": "RESUME_GENERATION"}]),
        Decision(kind="temporarily_unavailable", reasonCode="schema"),
    ],
)
def test_same_origin_v3_route_retains_replay_and_observed_source_contract(tmp_path, result):
    calls = []

    async def fake(payload):
        assert isinstance(payload, TurnV3)
        calls.append(payload.clientMessageId)
        return result

    app = create_app(Settings.for_offline(), agent_interpreter=fake, ui_output_root=tmp_path)
    with TestClient(app) as client:
        payload = turn().model_dump(exclude_none=True)
        headers = {"X-Astra-Agent": "astra-intent-v1", "X-Astra-Semantic": "astra-semantic-v3"}
        response = client.post("/agent/turn", json=payload, headers=headers)
        assert response.status_code == 200
        body = response.json()
        if isinstance(result, Decision):
            assert body["decision"]["kind"] == "temporarily_unavailable"
        else:
            assert body["schemaVersion"] == "astra-semantic-v3"
            assert body["sourceContract"] == result.schemaVersion
            assert body["frame"]["dialogueAct"] == result.dialogueAct
        assert client.post("/agent/turn", json=payload, headers=headers).json() == body
        assert len(calls) == 1
        assert (
            client.post(
                "/agent/turn", json=payload, headers={**headers, "Sec-Fetch-Site": "cross-site"}
            ).status_code
            == 403
        )
        assert client.get("/agent/capabilities").json()["compatibility"] == "explicit-legacy-bridge"
