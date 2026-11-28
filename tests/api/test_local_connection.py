"""Local onboarding and recovery with an in-memory HTTP provider; no paid calls."""

import asyncio
import json
import os
import socket
import ssl
from contextlib import contextmanager
from uuid import uuid4

import httpx
import pytest
from dotenv import dotenv_values
from fastapi.testclient import TestClient

from exam_baseline.agent.v3 import TurnV3
from exam_baseline.api.app import create_app, create_web_app
from exam_baseline.connection import (
    DEFAULT_MODEL,
    DEFAULT_URL,
    KEY_NAME,
    ConnectionInput,
    SharedConnection,
)
from exam_baseline.core.contracts import CompletionRequest, ProviderError

KEY = "fixture-only-key-not-a-provider-credential"
FRAME = {"dialogueAct": "REQUEST", "goals": [{"goal": "OPEN_CONFIGURATION"}]}
REQUEST = CompletionRequest("Unchanged synthetic system", "Synthetic data", {"type": "object"})


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch):
    for name in os.environ:
        if name.startswith(("EXAM_", "ASTRA_", "ANTHROPIC_")):
            monkeypatch.delenv(name)


def turn():
    return TurnV3(
        schemaVersion="astra-intent-v1",
        clientMessageId=str(uuid4()),
        workspaceId=str(uuid4()),
        message="Synthetic setup request",
        context={"screen": "workspace", "setup": False},
    )


def completion(value=FRAME):
    return httpx.Response(
        200,
        json={
            "type": "message",
            "role": "assistant",
            "stop_reason": "tool_use",
            "content": [{"type": "tool_use", "name": "astra_output", "input": value}],
            "usage": {"input_tokens": 12, "output_tokens": 8},
        },
    )


@contextmanager
def running(tmp_path, handler=None):
    calls = []

    def handle(request):
        calls.append(request)
        return handler(request) if handler else completion()

    connection = SharedConnection(tmp_path / ".env", transport=httpx.MockTransport(handle))
    app = create_app(connection=connection, ui_output_root=tmp_path / "ui")
    with TestClient(app, base_url="http://127.0.0.1", client=("127.0.0.1", 50000)) as client:
        yield client, connection, calls


def save(client, **changes):
    status = client.get("/api/connection").json()
    return client.post(
        "/api/connection",
        headers={"X-Astra-Setup": status["setupToken"]},
        json={"apiKey": KEY, "model": DEFAULT_MODEL, "baseUrl": DEFAULT_URL, **changes},
    )


def test_first_start_and_saving_are_probe_free_and_never_return_key(tmp_path):
    with running(tmp_path) as (client, connection, calls):
        status = client.get("/api/connection")
        assert status.headers["cache-control"] == "no-store"
        assert not status.json()["configured"]
        # Literal from the provider's published compatible endpoint, independent
        # of DEFAULT_URL so a typo in our bundled defaults cannot validate itself.
        assert status.json()["baseUrl"] == "https://api.nghimmo.com/v1"
        assert KEY_NAME == "ANTHROPIC_API_KEY"
        assert connection.settings.provider == "unconfigured"
        assert client.get("/api/health").json()["demoMode"] is False
        for endpoint in (
            "/agent/turn",
            "/api/exams/generate",
            "/v1/exams/generate",
            "/v2/exams/generate",
            "/api/exams/fixture/resume",
            "/api/exams/fixture/questions/1/regenerate",
        ):
            assert client.post(endpoint, json={}).status_code == 503
        assert not connection.path.exists() and not calls
        assert client.get("/api/workspaces").json() == {"workspaces": []}
        saved = save(client)
        assert saved.status_code == 200
        assert KEY not in saved.text and not saved.json()["verified"]
        assert saved.json()["configured"] and not calls
        assert client.get("/api/health").json()["providerConfigured"]
        assert client.get("/agent/capabilities").json()["workerDeploymentRequired"] is False
    loaded = SharedConnection(tmp_path / ".env")
    assert loaded.configured and not loaded.verified
    assert loaded.settings.api_key.get_secret_value() == KEY


def test_explicit_offline_demo_entry_point_remains_separate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("EXAM_DEMO_MODE", "true")
    monkeypatch.setenv("EXAM_PROVIDER", "mock")
    monkeypatch.setenv("EXAM_MODEL", "mock-fixture-v1")
    monkeypatch.setenv("ASTRA_AGENT_ENABLED", "false")
    built = tmp_path / "astra-frontend/dist"
    built.mkdir(parents=True)
    (built / "index.html").write_text("Offline fixture")
    with TestClient(create_web_app()) as client:
        assert client.get("/api/health").json()["demoMode"] is True
        assert client.get("/api/connection").status_code == 404


@pytest.mark.parametrize("source", ["legacy", "anthropic", "both"])
def test_anthropic_key_precedence_and_probe_free_migration_without_reentry(tmp_path, source):
    values = {
        "EXAM_PROVIDER": "chat_completions",
        "EXAM_MODEL": DEFAULT_MODEL,
        "EXAM_BASE_URL": DEFAULT_URL,
    }
    if source in {"legacy", "both"}:
        values["ASTRA_GEMINI_API_KEY"] = "fixture-legacy-key"
    if source in {"anthropic", "both"}:
        values["ANTHROPIC_API_KEY"] = "fixture-anthropic-key"
    expected = "fixture-legacy-key" if source == "legacy" else "fixture-anthropic-key"
    env = tmp_path / ".env"
    env.write_text("\n".join(f"{name}={value}" for name, value in values.items()), encoding="utf-8")
    with running(tmp_path) as (client, connection, calls):
        assert connection.configured
        assert connection.settings.api_key.get_secret_value() == expected
        response = save(client, apiKey="")
        assert response.status_code == 200 and expected not in response.text and not calls
        saved = dotenv_values(env)
        assert saved["ANTHROPIC_API_KEY"] == expected
        assert "ASTRA_GEMINI_API_KEY" not in saved
    assert SharedConnection(env).settings.api_key.get_secret_value() == expected


def test_shared_key_reaches_all_roles_and_chat_with_original_schema(tmp_path, monkeypatch):
    monkeypatch.setenv("ASTRA_AGENT_TRANSPORT", "worker")
    monkeypatch.setenv("ASTRA_MAS_TRANSPORT", "worker")
    monkeypatch.setenv("EXAM_USE_AI_GATEWAY", "true")
    with running(tmp_path) as (client, connection, calls):
        assert save(client).status_code == 200
        assert connection.settings.provider == "anthropic"
        assert dotenv_values(connection.path)["EXAM_PROVIDER"] == "anthropic"
        for provider in [connection.baseline, *connection.providers.values()]:
            result = client.portal.call(provider.complete, REQUEST)
            assert json.loads(result.text) == FRAME
        response = client.post(
            "/agent/turn",
            json=turn().model_dump(mode="json"),
            headers={
                "X-Astra-Agent": "astra-intent-v1",
                "X-Astra-Semantic": "astra-semantic-v3",
            },
        )
        assert response.status_code == 200, response.text
        assert response.json()["frame"]["goals"] == [
            {"goal": "OPEN_CONFIGURATION", "parameters": {}, "prohibited": False}
        ]
        assert len(calls) == 6
        for request in calls:
            payload = json.loads(request.content)
            assert str(request.url) == DEFAULT_URL + "/messages"
            assert request.headers["x-api-key"] == KEY
            assert request.headers["anthropic-version"] == "2023-06-01"
            assert "Authorization" not in request.headers
            assert payload["model"] == DEFAULT_MODEL
            assert "response_format" not in payload
            assert "cf-aig-authorization" not in request.headers
        assert json.loads(calls[0].content)["tools"][0]["input_schema"] == REQUEST.output_schema
        assert json.loads(calls[0].content)["system"] == REQUEST.system
        assert json.loads(calls[0].content)["max_tokens"] == 8192
        assert json.loads(calls[-1].content)["max_tokens"] == 2048
        assert client.get("/api/connection").json()["verified"]


def test_atomic_update_preserves_unrelated_config_and_retains_blank_key(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text(
        "# Preserve this comment\nEXAM_TIMEOUT_SECONDS=47\n"
        'EXAM_MODEL=old\nEXAM_MODEL=duplicate\nUNRELATED="value"\n',
        encoding="utf-8",
    )
    with running(tmp_path) as (client, connection, calls):
        assert save(client).status_code == 200
        assert save(client, apiKey="", model="nghi/claude-haiku-4.5-new").status_code == 200
        values = dotenv_values(env)
        assert values[KEY_NAME] == KEY and values["EXAM_MODEL"].endswith("-new")
        assert values["UNRELATED"] == "value" and values["EXAM_TIMEOUT_SECONDS"] == "47"
        assert env.read_text().count("EXAM_MODEL=") == 1
        assert "# Preserve this comment" in env.read_text()
        assert connection.settings.timeout_seconds == 47
        before = env.read_bytes()
        monkeypatch.setattr(
            "exam_baseline.connection.os.replace",
            lambda *args: (_ for _ in ()).throw(OSError("fixture disk failure")),
        )
        failed = save(client, apiKey="fixture-replacement")
        assert failed.status_code == 503 and KEY not in failed.text
        assert env.read_bytes() == before
        assert connection.settings.api_key.get_secret_value() == KEY
        assert not list(tmp_path.glob(".astra-env-*")) and not calls


@pytest.mark.parametrize(
    "changes",
    [
        {"apiKey": ""},
        {"apiKey": "bad\nkey"},
        {"apiKey": "bad key"},
        {"model": "bad\nmodel"},
        {"baseUrl": "http://example.com/v1"},
        {"baseUrl": "https://user:secret@example.com/v1"},
        {"baseUrl": "https://example.com/v1?key=secret"},
        {"baseUrl": "https://astra-mas-proxy.workers.dev/v1"},
        {"baseUrl": "https://example.com:invalid/v1"},
        {"baseUrl": "https://example.com:0/v1"},
        {"baseUrl": "https://ex ample.com/v1"},
    ],
)
def test_invalid_configuration_is_not_written_or_reflected(tmp_path, changes):
    with running(tmp_path) as (client, connection, calls):
        response = save(client, **changes)
        assert response.status_code == 422 and KEY not in response.text
        assert "secret" not in response.text and not connection.path.exists() and not calls


@pytest.mark.parametrize(
    "headers",
    [
        {"Origin": "https://example.com"},
        {"Host": "evil.example"},
        {"Sec-Fetch-Site": "cross-site"},
        {"X-Astra-Setup": "wrong"},
    ],
)
def test_configuration_requires_local_origin_and_session_nonce(tmp_path, headers):
    with running(tmp_path) as (client, connection, calls):
        response = client.post(
            "/api/connection",
            json={"apiKey": KEY},
            headers={
                "X-Astra-Setup": connection.token,
                **headers,
            },
        )
        assert response.status_code == 403 and not connection.path.exists() and not calls
        assert client.post("/api/connection", json={"apiKey": KEY}).status_code == 403


def test_nonlocal_peer_and_oversized_body_cannot_save(tmp_path):
    connection = SharedConnection(tmp_path / ".env")
    app = create_app(connection=connection, ui_output_root=tmp_path / "ui")
    with TestClient(app, base_url="http://localhost", client=("192.0.2.5", 8000)) as client:
        assert client.get("/api/connection").status_code == 403
    with running(tmp_path) as (client, connection, calls):
        result = client.post(
            "/api/connection", content="x" * 16385, headers={"X-Astra-Setup": connection.token}
        )
        assert result.status_code == 413 and not connection.path.exists() and not calls


@pytest.mark.parametrize("status", [400, 401, 403, 404, 429, 503])
def test_provider_failure_keeps_draft_and_key_replacement_recovers(tmp_path, status):
    failed = [True]

    def handler(request):
        if failed[0]:
            return httpx.Response(
                status,
                json={
                    "error": {
                        "message": "Do not reflect remote prose " + KEY,
                        "param": "model",
                    }
                },
            )
        return completion()

    with running(tmp_path, handler) as (client, connection, calls):
        assert save(client).status_code == 200
        workspace = f"/api/workspaces/{uuid4()}"
        draft = {
            "revision": 0,
            "mode": "custom",
            "title": "Keep me",
            "draft": "Keep draft",
            "messages": [],
        }
        assert client.put(workspace, json=draft).status_code == 200
        checkpoint = tmp_path / "ui/checkpoint-sentinel.json"
        checkpoint.write_text('{"completedQuestions":["P1_1"]}')
        result = client.portal.call(connection.interpreter, turn())
        assert result.kind == "temporarily_unavailable" and len(calls) == 1
        public = client.get("/api/connection")
        assert public.json()["lastFailure"]["status"] == status
        assert public.json()["lastFailure"]["field"] == "model"
        assert KEY not in public.text and "remote prose" not in public.text
        assert client.get("/api/workspaces").json()["workspaces"][0]["draft"] == "Keep draft"
        assert checkpoint.read_text() == '{"completedQuestions":["P1_1"]}'
        assert save(client, apiKey="fixture-new-key").status_code == 200
        failed[0] = False
        recovered = client.portal.call(connection.interpreter, turn())
        assert recovered.goals[0].goal == "OPEN_CONFIGURATION" and len(calls) == 2
        assert calls[-1].headers["x-api-key"] == "fixture-new-key"
        assert client.get("/api/connection").json()["lastFailure"] is None


@pytest.mark.parametrize("html", [False, True])
def test_403_reports_protocol_metadata_without_assuming_model_entitlement(tmp_path, html):
    def handler(request):
        if html:
            return httpx.Response(403, text="<html>Private upstream details " + KEY + "</html>",
                                  headers={"content-type": "text/html"})
        return httpx.Response(403, json={"type": "error", "error": {
            "type": "permission_error", "message": "Private upstream details " + KEY}})
    with running(tmp_path, handler) as (client, connection, calls):
        assert save(client).status_code == 200
        with pytest.raises(ProviderError):
            client.portal.call(connection.providers["composer"].complete, REQUEST)
        public = client.get("/api/connection")
        failure = public.json()["lastFailure"]
        assert failure["status"] == 403 and "endpoint" in failure["message"]
        assert failure["responseFormat"] == ("html" if html else "json")
        assert failure["providerType"] == (None if html else "permission_error")
        assert KEY not in public.text and "Private upstream details" not in public.text
        assert len(calls) == 1


def test_timeout_invalid_json_and_redirect_fail_without_silent_fallback(tmp_path):
    responses = ["timeout", "invalid", "redirect"]

    def handler(request):
        mode = responses.pop(0)
        if mode == "timeout":
            raise httpx.ReadTimeout("fixture timeout", request=request)
        if mode == "invalid":
            return httpx.Response(200, text="not json")
        return httpx.Response(307, headers={"Location": "https://other.example/v1"})

    with running(tmp_path, handler) as (client, connection, calls):
        assert save(client).status_code == 200
        for _ in range(3):
            with pytest.raises(ProviderError):
                client.portal.call(connection.baseline.complete, REQUEST)
        assert len(calls) == 3 and connection.configured
        assert all(request.url.host == "api.nghimmo.com" for request in calls)


@pytest.mark.parametrize(
    "cause,expected",
    [
        (socket.gaierror(11001, "fixture private details"), "Không phân giải được tên miền API"),
        (ssl.SSLCertVerificationError(1, "fixture private details"), "kết nối HTTPS"),
        (OSError("fixture private details"), "kiểm tra API Base URL"),
    ],
)
def test_connection_failures_explain_network_cause_without_exposing_remote_text(
    tmp_path, cause, expected
):
    def handler(request):
        raise httpx.ConnectError("Never expose " + KEY, request=request) from cause

    with running(tmp_path, handler) as (client, connection, calls):
        assert save(client).status_code == 200
        with pytest.raises(ProviderError) as error:
            client.portal.call(connection.providers["composer"].complete, REQUEST)
        assert error.value.code == "provider_connection_failed"
        response = client.get("/api/connection")
        assert expected in response.json()["lastFailure"]["message"]
        assert KEY not in response.text and "fixture private details" not in response.text
        assert connection.configured and len(calls) == 1


def test_reconfiguration_is_blocked_until_inflight_work_is_finished(tmp_path):
    async def scenario():
        started, release = asyncio.Event(), asyncio.Event()

        async def handle(request):
            started.set()
            await release.wait()
            return completion()

        connection = SharedConnection(tmp_path / ".env", transport=httpx.MockTransport(handle))
        app = create_app(connection=connection, ui_output_root=tmp_path / "ui")
        async with app.router.lifespan_context(app):
            await connection.save(
                ConnectionInput(apiKey=KEY, model=DEFAULT_MODEL, baseUrl=DEFAULT_URL)
            )
            task = asyncio.create_task(connection.providers["composer"].complete(REQUEST))
            await started.wait()
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as error:
                await connection.save(
                    ConnectionInput(apiKey="replacement", model=DEFAULT_MODEL, baseUrl=DEFAULT_URL)
                )
            assert error.value.status_code == 409
            release.set()
            await task
            assert not connection.busy()
            await connection.save(
                ConnectionInput(apiKey="replacement", model=DEFAULT_MODEL, baseUrl=DEFAULT_URL)
            )
            assert connection.settings.api_key.get_secret_value() == "replacement"

    asyncio.run(scenario())
