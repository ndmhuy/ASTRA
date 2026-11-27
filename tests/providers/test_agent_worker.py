"""Worker transport failures and validated semantic envelope, with no inference."""

import asyncio
import json

import httpx
import pytest

from exam_baseline.agent.contracts import Turn
from exam_baseline.agent.gateway import AgentSettings, configured_interpreter
from exam_baseline.agent.provider import ProviderFailure
from exam_baseline.agent.worker import WorkerInterpretationProvider, log_evidence

TURN = Turn(
    schemaVersion="astra-intent-v1",
    clientMessageId="a" * 36,
    workspaceId="b" * 36,
    message="Natural request",
    context={"screen": "start", "setup": False},
)


def test_safe_evidence_keeps_latency_and_tokens_without_unrestricted_remote_text(monkeypatch):
    from exam_baseline.agent import worker

    records = []
    monkeypatch.setattr(worker.logger, "info", lambda _, value: records.append(json.loads(value)))
    log_evidence(TURN, {"evidence": ["malformed"]})
    assert not records
    log_evidence(
        TURN,
        {
            "evidence": {
                "attempts": 1,
                "providerElapsedMs": 1630,
                "requestStage": "provider_request",
                "privatePrompt": "fixture-private",
                "diagnostics": {
                    "promptTokenCount": 1515,
                    "finishReason": "STOP",
                    "rawText": "fixture-private",
                    "validationPaths": ["/goals/0/parameters", "/unsafe?fixture-private"],
                },
            }
        },
    )
    assert records[0]["promptTokenCount"] == 1515
    assert records[0]["requestStage"] == "provider_request"
    assert records[0]["validationPaths"] == ["/goals/0/parameters"]
    assert "fixture-private" not in json.dumps(records)


@pytest.mark.parametrize("error", ["auth", "quota", "timeout", "model", "schema", "disabled"])
def test_worker_remote_categories(error):
    async def run():
        def transport(request):
            assert "authorization" not in request.headers
            assert "cf-aig-authorization" not in request.headers
            return httpx.Response(503, json={"error": error})

        async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
            with pytest.raises(ProviderFailure, match=error):
                await WorkerInterpretationProvider(client, "https://worker.example").interpret(
                    TURN, 1
                )

    asyncio.run(run())


def test_worker_success_uses_existing_intake_contract():
    async def run():
        def transport(request):
            return httpx.Response(
                200,
                json={
                    "schemaVersion": TURN.schemaVersion,
                    "clientMessageId": TURN.clientMessageId,
                    "decision": {
                        "kind": "clarify",
                        "intents": [],
                        "intake": {"mode": "request", "family": "thpt"},
                    },
                },
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
            result = await WorkerInterpretationProvider(client, "https://worker.example").interpret(
                TURN, 1
            )
            assert result.intake.family == "thpt"
        settings = AgentSettings(
            _env_file=None, enabled=True, transport="worker", gateway_token=None, daily_attempts=0
        )
        async with configured_interpreter(settings) as interpreter:
            assert len(interpreter.routes) == 1
            assert interpreter.reserve()

    asyncio.run(run())
