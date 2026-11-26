"""Synthetic semantic boundary evidence, never natural-language model evaluation."""

import asyncio
import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError

from exam_baseline.agent.contracts import ExamIntake, Turn
from exam_baseline.agent.gateway import DirectGeminiProvider
from exam_baseline.agent.native import parse_native
from exam_baseline.agent.provider import ProviderFailure, ProviderRouter
from exam_baseline.agent.semantics import CATALOG, SemanticTurn, legacy_decision, normalize_frame
from exam_baseline.agent.worker import SEMANTIC_HASH, WorkerInterpretationProvider
from exam_baseline.api.app import create_app
from exam_baseline.config import Settings

FRAME = {
    "dialogueAct": "REQUEST",
    "goals": [{"goal": "PREPARE_EXAM", "parameters": {"family": "thpt"}}],
}
TURN = Turn(
    schemaVersion="astra-intent-v1",
    clientMessageId="a" * 36,
    workspaceId="b" * 36,
    message="Synthetic teacher request",
    context={"screen": "start", "setup": False},
)


def test_different_provider_envelopes_preserve_identical_meaning():
    gemini = {
        "candidates": [
            {
                "finishReason": "STOP",
                "content": {
                    "parts": [{"thought": True, "text": "ignored"}, {"text": json.dumps(FRAME)}]
                },
            }
        ]
    }
    alternate = {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"content": json.dumps({**FRAME, "title": None, "constraints": None})},
            }
        ]
    }
    assert parse_native("gemini", gemini) == parse_native("chat_completions", alternate)
    assert legacy_decision(parse_native("gemini", gemini)).intake.family == "thpt"


def test_direct_native_payload_matches_worker_parity_fixture():
    root = Path(__file__).resolve().parents[2]
    expected = json.loads(
        (root / "eval/agent-semantic/native-wire.fixture.json").read_text("utf-8")
    )

    def transport(request):
        assert json.loads(request.content) == expected["request"]
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {"finishReason": "STOP", "content": {"parts": [{"text": json.dumps(FRAME)}]}}
                ]
            },
        )

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
            provider = DirectGeminiProvider(
                client, SecretStr("fixture-only-key"), "gemini-fixture", 512, semantic=True
            )
            result = await provider.interpret(
                TURN.model_copy(update={"message": "Natural fixture"}), 1
            )
            assert result.goals[0].goal == "PREPARE_EXAM"

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "change",
    [
        {"goals": [{"goal": "RUN_SHELL"}]},
        {"goals": [{"goal": "PREPARE_EXAM", "parameters": {"family": "imagined"}}]},
        {"goals": [{"goal": "PREPARE_EXAM", "parameters": {"workspaceId": "fabricated"}}]},
        {"goals": [{"goal": "PREPARE_EXAM", "parameters": {"count": True}}]},
        {"goals": FRAME["goals"] * 5},
        {"confirmationToken": "invented"},
    ],
)
def test_unsafe_frames_are_not_repaired_to_nearest_executable_goal(change):
    with pytest.raises((ValidationError, ValueError)):
        normalize_frame({**FRAME, **change})


def test_absent_information_and_invalid_optional_titles_are_safe():
    frame = normalize_frame({**FRAME, "title": {"invalid": "metadata"}})
    assert frame.title is None
    assert frame.goals[0].parameters == {"family": "thpt"}
    for act in ["CONVERSATION", "AMBIGUOUS", "UNSUPPORTED", "OUT_OF_SCOPE", "CANCEL"]:
        assert not normalize_frame({"dialogueAct": act}).goals


def test_python_accepts_shared_corpus_and_rejects_shared_unsafe_fixtures():
    root = Path(__file__).resolve().parents[2] / "eval/agent-semantic"
    for line in (root / "semantic-corpus.jsonl").read_text("utf-8").splitlines():
        row = json.loads(line)
        frame = normalize_frame(row["expectedFrame"])
        assert frame.dialogueAct == row["expectedFrame"]["dialogueAct"]
        assert not any(item.goal in row["prohibitedGoals"] for item in frame.goals)
    for row in json.loads((root / "adversarial-corpus.json").read_text("utf-8")):
        if "invalidFrame" in row:
            with pytest.raises(ValueError):
                normalize_frame(row["invalidFrame"])


def test_structured_question_context_is_versioned_and_forbids_application_ids():
    body = TURN.model_dump()
    body["context"]["recentQuestion"] = {"number": 1, "part": "P1"}
    assert SemanticTurn.model_validate(body).context.recentQuestion.number == 1
    with pytest.raises(ValidationError):
        Turn.model_validate(body)  # The legacy wire schema remains unchanged.
    body["context"]["recentQuestion"]["stableId"] = "fabricated"
    with pytest.raises(ValidationError):
        SemanticTurn.model_validate(body)


def test_canonical_intake_limits_remain_compatible_with_existing_execution_intake():
    properties = ExamIntake.model_json_schema()["properties"]
    for name, bounds in CATALOG["parameterBounds"].items():
        field = next(item for item in properties[name]["anyOf"] if item["type"] != "null")
        for key, limit in bounds.items():
            assert field[key] == limit
    for name, value in [("subject", "x" * 81), ("topic", "x" * 251), ("grade", 13)]:
        with pytest.raises(ValueError):
            normalize_frame(
                {
                    "dialogueAct": "REQUEST",
                    "goals": [{"goal": "PREPARE_EXAM", "parameters": {name: value}}],
                }
            )


def test_bad_provider_json_and_incomplete_output_fail_without_fallback():
    for finish, text in [("MAX_TOKENS", json.dumps(FRAME)), ("STOP", "{")]:
        with pytest.raises(ProviderFailure, match="schema"):
            parse_native(
                "gemini",
                {"candidates": [{"finishReason": finish, "content": {"parts": [{"text": text}]}}]},
            )


def test_parameter_failure_logs_exact_safe_path_and_invariant_without_private_value(caplog):
    output = {
        "dialogueAct": "REQUEST",
        "goals": [{"goal": "PREPARE_EXAM", "parameters": {"family": "PRIVATE_TEACHER_VALUE"}}],
    }
    with pytest.raises(ProviderFailure):
        parse_native(
            "gemini",
            {
                "candidates": [
                    {"finishReason": "STOP", "content": {"parts": [{"text": json.dumps(output)}]}}
                ]
            },
        )
    assert "goals/0/parameters/family" in caplog.text
    assert "semantic_parameter_enum" in caplog.text
    assert "PRIVATE_TEACHER_VALUE" not in caplog.text


def test_versioned_worker_transport_and_local_response_negotiation(tmp_path):
    async def scenario():
        def transport(request):
            assert request.url.path == "/v2/agent/interpret"
            assert request.headers["X-Astra-Contract"] == SEMANTIC_HASH
            assert "authorization" not in request.headers
            return httpx.Response(
                200,
                json={
                    "schemaVersion": "astra-semantic-v1",
                    "clientMessageId": TURN.clientMessageId,
                    "frame": normalize_frame(FRAME).model_dump(),
                },
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
            provider = WorkerInterpretationProvider(
                client, "https://fixture.example", semantic=True
            )
            result = await ProviderRouter(provider, reserve=lambda: True)(TURN)
            assert result.goals[0].goal == "PREPARE_EXAM"

    asyncio.run(scenario())

    async def interpreter(turn):
        return normalize_frame(FRAME)

    app = create_app(Settings.for_offline(), agent_interpreter=interpreter, ui_output_root=tmp_path)
    with TestClient(app) as client:
        headers = {"X-Astra-Agent": TURN.schemaVersion, "X-Astra-Semantic": "astra-semantic-v1"}
        response = client.post("/agent/turn", json=TURN.model_dump(), headers=headers)
        assert response.json()["frame"]["goals"][0]["parameters"] == {"family": "thpt"}
        # The same cached result can still be consumed by a legacy local frontend.
        response = client.post(
            "/agent/turn", json=TURN.model_dump(), headers={"X-Astra-Agent": TURN.schemaVersion}
        )
        assert response.json()["decision"]["intake"]["family"] == "thpt"
