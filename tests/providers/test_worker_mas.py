"""MAS transport remains closed and preserves the existing academic request."""

import asyncio
import json

import httpx
import pytest
from pydantic import ValidationError

from exam_baseline.config import Settings
from exam_baseline.core.contracts import CompletionRequest, ImageInput, ProviderError
from exam_baseline.providers.worker_mas import (
    DisabledWorkerMasProvider,
    MasSettings,
    WorkerMasProvider,
    configured_worker_mas,
)


def test_mas_adapter_preserves_schema_images_model_and_independent_limits():
    settings = Settings.for_offline().model_copy(update={"model": "academic-fixture"})
    request = CompletionRequest(
        "academic-system", "academic-data", {"type": "object"}, (ImageInput(b"synthetic-image"),)
    )
    provider = DisabledWorkerMasProvider(settings, "solver")
    envelope = provider.prepare(request)
    assert envelope["model"] == "academic-fixture"
    assert envelope["request"]["system"] == request.system
    assert envelope["request"]["user"] == request.user
    assert envelope["request"]["images"][0]["base64"] == "c3ludGhldGljLWltYWdl"
    assert envelope["limits"]["max_output_tokens"] == 8192
    assert envelope["limits"]["timeout_seconds"] == 90
    envelope["request"]["output_schema"]["new"] = "field"
    assert request.output_schema == {"type": "object"}

    with pytest.raises(ProviderError) as error:
        asyncio.run(provider.complete(request))
    assert error.value.code == "mas_forwarding_disabled"


def test_paid_public_mas_cannot_be_enabled_by_a_local_boolean():
    with pytest.raises(ValidationError):
        MasSettings(_env_file=None, forwarding_enabled=True)


def profile():
    return MasSettings(
        _env_file=None, transport="worker", forwarding_enabled=True, caller_token="a" * 64
    )


def test_worker_mas_reuses_academic_wire_and_existing_completion_parser():
    async def run():
        seen = []

        def transport(request):
            seen.append(request)
            return httpx.Response(
                200,
                json={
                    "id": "synthetic-completion",
                    "model": "gemini-academic-fixture",
                    "choices": [{"finish_reason": "stop", "message": {"content": '{"value":42}'}}],
                    "usage": {"prompt_tokens": 123, "completion_tokens": 45, "total_tokens": 168},
                },
            )

        settings = Settings(
            _env_file=None,
            provider="worker_mas",
            model="gemini-academic-fixture",
            token_limit_field="max_tokens",
            response_format="json_schema",
            supports_images=True,
        )
        schema = {"type": "object", "properties": {"value": {"type": "integer"}}}
        request = CompletionRequest(
            "unchanged academic instruction",
            "unchanged academic data",
            schema,
            (ImageInput(b"synthetic-image"),),
        )
        async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
            providers = configured_worker_mas(settings, client, profile())
            assert set(providers) == {"composer", "illustrator", "solver", "reviewer"}
            result = await providers["solver"].complete(request)
            assert result.text == '{"value":42}'
            assert result.model == "gemini-academic-fixture"
            assert result.usage.input_tokens == 123
            assert result.usage.output_tokens == 45
        assert len(seen) == 1
        wire = json.loads(seen[0].content)
        assert str(seen[0].url) == profile().worker_url + "/v1/chat/completions"
        assert seen[0].headers["Authorization"] == "Bearer " + "a" * 64
        assert seen[0].headers["X-Astra-MAS-Stage"] == "solver"
        assert "cf-aig-authorization" not in seen[0].headers
        assert wire["messages"][0] == {"role": "system", "content": request.system}
        assert wire["messages"][1]["content"][0]["text"] == request.user
        assert wire["response_format"]["json_schema"]["schema"] == schema
        assert wire["max_tokens"] == 8192
        assert wire["model"] == settings.model
        assert "schemaVersion" not in wire and "goals" not in wire
        assert schema == request.output_schema

    asyncio.run(run())


@pytest.mark.parametrize(
    "status,code",
    [
        (400, "provider_bad_request"),
        (401, "provider_auth_error"),
        (429, "provider_rate_limited"),
        (504, "provider_gateway_timeout"),
    ],
)
def test_worker_mas_retains_provider_error_parser_without_retry(status, code):
    async def run():
        seen = []

        def transport(request):
            seen.append(request)
            return httpx.Response(status, json={"error": {"code": "synthetic"}})

        settings = Settings(_env_file=None, provider="worker_mas", model="gemini-fixture")
        async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
            provider = WorkerMasProvider(settings, client, profile(), "composer")
            with pytest.raises(ProviderError) as error:
                await provider.complete(CompletionRequest("academic", "data", {}))
        assert len(seen) == 1
        assert error.value.code == code
        assert error.value.http_status == status

    asyncio.run(run())


def test_worker_profile_requires_explicit_non_demo_model_and_caller_access():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, provider="worker_mas")
    for url in [
        "http://worker.example",
        "https://user:pass@worker.example",
        "https://worker.example?token=x",
    ]:
        with pytest.raises(ValidationError):
            MasSettings(_env_file=None, worker_url=url)
    assert "a" * 64 not in repr(profile())
