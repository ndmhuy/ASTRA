"""Offline wire and admission checks for Cloudflare BYOK clients."""

import asyncio
import json

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError

from exam_baseline.agent.contracts import VERSION, Decision, Turn
from exam_baseline.agent.gateway import (
    AgentSettings,
    DailyBudget,
    DirectGeminiProvider,
    GeminiGatewayProvider,
)
from exam_baseline.agent.provider import ProviderFailure
from exam_baseline.api.app import create_app
from exam_baseline.config import Settings
from exam_baseline.core.contracts import CompletionRequest
from exam_baseline.providers.chat_completions import ChatCompletionsProvider
from exam_baseline.providers.gateway import Gateway

ACCOUNT = "a" * 32
TOKEN = "fixture-only-run-token"
TURN = Turn(
    schemaVersion=VERSION,
    clientMessageId="a" * 36,
    workspaceId="b" * 36,
    message="Mở mẫu đề",
    context={"screen": "workspace", "setup": False},
)


def gateway():
    return Gateway(ACCOUNT, "astra-fixture", SecretStr(TOKEN), "stored")


def assert_protected(request):
    assert request.url.host == "gateway.ai.cloudflare.com"
    assert request.headers["cf-aig-authorization"] == f"Bearer {TOKEN}"
    assert request.headers["cf-aig-byok-alias"] == "stored"
    assert request.headers["cf-aig-no-wholesale"] == "true"
    assert request.headers["cf-aig-skip-cache"] == "true"
    assert request.headers["cf-aig-collect-log-payload"] == "false"
    assert "authorization" not in request.headers
    assert "x-goog-api-key" not in request.headers
    assert TOKEN.encode() not in request.content


def test_gemini_gateway_uses_validated_fixed_route_and_schema():
    def transport(request):
        assert_protected(request)
        assert request.url.path == (
            f"/v1/{ACCOUNT}/astra-fixture/google-ai-studio/v1/models/gemini-fixture:generateContent"
        )
        sent = json.loads(request.content)
        assert sent["generationConfig"]["responseMimeType"] == "application/json"
        assert sent["generationConfig"]["responseJsonSchema"]["additionalProperties"] is False
        output = {
            "kind": "clarify",
            "intents": [],
            "title": "Soạn đề THPT",
            "intake": {"mode": "request", "family": "thpt"},
        }
        assert "intake" in sent["generationConfig"]["responseJsonSchema"]["properties"]
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {"finishReason": "STOP", "content": {"parts": [{"text": json.dumps(output)}]}}
                ],
            },
        )

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
            provider = GeminiGatewayProvider(client, gateway(), "gemini-fixture", 256)
            decision = await provider.interpret(TURN, 1)
            assert decision.intake and decision.intake.family == "thpt"
            assert decision.title == "Soạn đề THPT"
            with pytest.raises(ValueError):
                GeminiGatewayProvider(client, gateway(), "gemini-x/redirect", 256)

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "status,reason",
    [
        (400, "rejected"),
        (401, "auth"),
        (403, "auth"),
        (404, "model"),
        (429, "quota"),
        (503, "transient"),
        (200, "schema"),
    ],
)
def test_gateway_provider_classifies_error_without_forwarding_payload(status, reason):
    def transport(request):
        assert_protected(request)
        return httpx.Response(status, headers={"Retry-After": "40"}, json={"bad": TOKEN})

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
            provider = GeminiGatewayProvider(client, gateway(), "gemini-fixture", 256)
            with pytest.raises(ProviderFailure) as error:
                await provider.interpret(TURN, 1)
            assert str(error.value) == reason
            if status == 429:
                assert error.value.retry_after == 40

    asyncio.run(scenario())


def test_mas_gateway_preserves_openai_request_and_omits_direct_key(tmp_path):
    def transport(request):
        assert_protected(request)
        assert request.url.path == f"/v1/{ACCOUNT}/astra-fixture/openai/chat/completions"
        payload = json.loads(request.content)
        assert payload["model"] == "exam-model-fixture"
        assert payload["response_format"] == {"type": "json_object"}
        return httpx.Response(
            200,
            json={
                "choices": [{"finish_reason": "stop", "message": {"content": "{}"}}],
                "usage": {"prompt_tokens": 100, "completion_tokens": 20},
            },
        )

    config = Settings(
        _env_file=None,
        provider="chat_completions",
        model="exam-model-fixture",
        api_key="fixture-direct-key",
        use_ai_gateway=True,
        gateway_account_id=ACCOUNT,
        gateway_id="astra-fixture",
        gateway_token=TOKEN,
        gateway_byok_alias="stored",
        spend_limit_usd=1,
        input_price_per_million=1,
        output_price_per_million=1,
        spend_ledger=tmp_path / "spend.sqlite3",
    )

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
            result = await ChatCompletionsProvider(config.for_agent_generation(), client).complete(
                CompletionRequest("system", "user", {})
            )
            assert result.text == "{}"

    asyncio.run(scenario())
    with pytest.raises(ValidationError):
        Settings(_env_file=None, provider="chat_completions", model="fixture", use_ai_gateway=True)


def test_agent_daily_budget_is_durable(tmp_path):
    path = tmp_path / "attempts.sqlite3"
    assert DailyBudget(path, 2).reserve()
    assert DailyBudget(path, 2).reserve()
    assert not DailyBudget(path, 2).reserve()
    assert AgentSettings(_env_file=None, enabled=False, daily_attempts=0).daily_attempts == 0


def test_configured_turn_route_requires_loopback_origin(tmp_path):
    calls = []

    async def stub(turn):
        calls.append(turn.clientMessageId)
        return Decision(kind="answer")

    app = create_app(Settings.for_offline(), ui_output_root=tmp_path)
    marker = {"X-Astra-Agent": VERSION}
    with TestClient(app, base_url="http://127.0.0.1:8000", client=("127.0.0.1", 12345)) as client:
        app.state.configured_interpreter = stub
        assert (
            client.post(
                "/agent/turn",
                json=TURN.model_dump(),
                headers={**marker, "Host": "outside.example"},
            ).status_code
            == 403
        )
        assert (
            client.post(
                "/agent/turn",
                json=TURN.model_dump(),
                headers={**marker, "Authorization": "injected"},
            ).status_code
            == 403
        )
        assert not calls
        assert client.post("/agent/turn", json=TURN.model_dump(), headers=marker).status_code == 200
        assert len(calls) == 1


def test_direct_gemini_transport_sends_key_only_to_google():
    def transport(request):
        assert request.url.host == "generativelanguage.googleapis.com"
        assert request.headers["x-goog-api-key"] == "fixture-direct-key"
        assert "cf-aig-authorization" not in request.headers
        output = {"kind": "task", "intents": [{"id": "OPEN_SETUP", "args": {}}]}
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {"finishReason": "STOP", "content": {"parts": [{"text": json.dumps(output)}]}}
                ]
            },
        )

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
            provider = DirectGeminiProvider(
                client, SecretStr("fixture-direct-key"), "gemini-fixture", 256
            )
            assert (await provider.interpret(TURN, 1)).intents[0].id == "OPEN_SETUP"

    asyncio.run(scenario())
