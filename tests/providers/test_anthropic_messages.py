"""Anthropic wire compatibility using synthetic HTTP only; never real inference."""

import asyncio
import json

import httpx
import pytest

from exam_baseline.config import Settings
from exam_baseline.core.contracts import CompletionRequest, ImageInput, ProviderError
from exam_baseline.core.recovery import classify
from exam_baseline.providers.anthropic_messages import AnthropicMessagesProvider
from exam_baseline.providers.http import http_provider

KEY = "fixture-anthropic-key"
SCHEMA = {"type": "object", "properties": {"answers": {"type": "object"}}, "required": ["answers"]}
REQUEST = CompletionRequest("Original academic system", "Original academic input", SCHEMA)


def settings(**overrides):
    return Settings(
        _env_file=None,
        provider="anthropic",
        model="nghi/claude-haiku-4.5",
        api_key=KEY,
        base_url=overrides.pop("base_url", "https://api.nghimmo.com/v1"),
        **overrides,
    )


def envelope(**overrides):
    return {
        "type": "message",
        "role": "assistant",
        "id": "msg_fixture",
        "model": "resolved-claude",
        "stop_reason": "tool_use",
        "content": [
            {"type": "text", "text": "Non-authoritative prose"},
            {"type": "tool_use", "name": "astra_output", "input": {"answers": {"1": "A"}}},
        ],
        "usage": {
            "input_tokens": 12,
            "cache_creation_input_tokens": 3,
            "cache_read_input_tokens": 5,
            "output_tokens": 7,
        },
        **overrides,
    }


def invoke(handler, config=None, request=REQUEST):
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await http_provider(config or settings(), client).complete(request)

    return asyncio.run(run())


@pytest.mark.parametrize("base", ["https://api.nghimmo.com", "https://api.nghimmo.com/v1/"])
def test_native_endpoint_auth_and_schema_are_independent_of_openai_wire(base):
    def handler(request):
        assert str(request.url) == "https://api.nghimmo.com/v1/messages"
        assert request.headers["x-api-key"] == KEY
        assert request.headers["anthropic-version"] == "2023-06-01"
        assert "authorization" not in request.headers
        payload = json.loads(request.content)
        assert payload["system"] == REQUEST.system
        assert payload["messages"] == [{"role": "user", "content": REQUEST.user}]
        assert payload["model"] == "nghi/claude-haiku-4.5"
        assert payload["tools"][0]["input_schema"] == SCHEMA
        assert payload["tool_choice"] == {"type": "tool", "name": "astra_output"}
        assert payload["max_tokens"] == 8192
        assert not {"response_format", "max_completion_tokens", "seed"} & payload.keys()
        return httpx.Response(200, json=envelope())

    result = invoke(handler, settings(base_url=base))
    assert json.loads(result.text) == {"answers": {"1": "A"}}
    assert result.model == "resolved-claude" and result.response_id == "msg_fixture"
    assert result.usage.input_tokens == 20 and result.usage.output_tokens == 7


@pytest.mark.parametrize(
    "stop,code",
    [
        ("max_tokens", "provider_incomplete"),
        ("end_turn", "provider_incomplete"),
        ("pause_turn", "provider_incomplete"),
        ("refusal", "provider_refusal"),
    ],
)
def test_incomplete_or_refused_tool_result_is_not_accepted(stop, code):
    with pytest.raises(ProviderError) as error:
        invoke(lambda _: httpx.Response(200, json=envelope(stop_reason=stop)))
    assert error.value.code == code and error.value.completion.usage.input_tokens == 20


@pytest.mark.parametrize(
    "content",
    [
        [],
        [{"type": "text", "text": "{}"}],
        [{"type": "tool_use", "name": "wrong", "input": {}}],
        [{"type": "tool_use", "name": "astra_output", "input": "{}"}],
        [
            {"type": "tool_use", "name": "astra_output", "input": {}},
            {"type": "tool_use", "name": "astra_output", "input": {}},
        ],
    ],
)
def test_missing_or_ambiguous_structured_output_cannot_fall_back_to_prose(content):
    with pytest.raises(ProviderError) as error:
        invoke(lambda _: httpx.Response(200, json=envelope(content=content)))
    assert error.value.code == "provider_protocol_error"


@pytest.mark.parametrize(
    "status,code",
    [
        (401, "provider_auth_error"),
        (403, "provider_access_denied"),
        (404, "provider_not_found"),
        (429, "provider_rate_limited"),
        (503, "provider_unavailable"),
        (529, "provider_unavailable"),
    ],
)
def test_http_categories_retry_after_and_secret_safe_errors(status, code):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(
            status,
            headers={"Retry-After": "2"},
            json={"type": "error", "error": {"type": "permission_error", "message": KEY}},
        )

    with pytest.raises(ProviderError) as error:
        invoke(handler)
    assert error.value.code == code and error.value.http_status == status
    assert error.value.retry_after_seconds == 2 and KEY not in str(error.value)
    assert len(calls) == 1
    if status == 529:
        assert classify(error.value).retryable


def test_uncertain_timeout_does_not_replay_and_redirect_never_forwards_key():
    calls = []

    def timeout(request):
        calls.append(request)
        raise httpx.ReadTimeout("Synthetic", request=request)

    with pytest.raises(ProviderError) as error:
        invoke(timeout)
    assert error.value.outcome_uncertain and len(calls) == 1
    with pytest.raises(ProviderError):
        invoke(lambda request: httpx.Response(307, headers={"Location": "https://other.example"}))


def test_image_wire_and_unsupported_option_fail_before_inference():
    def handler(request):
        content = json.loads(request.content)["messages"][0]["content"]
        assert content[1] == {
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": "eA=="},
        }
        return httpx.Response(200, json=envelope())

    request = CompletionRequest(
        "system", "input", SCHEMA, images=(ImageInput(data=b"x", mime="image/png"),)
    )
    invoke(handler, settings(supports_images=True), request)

    def forbidden(_):
        raise AssertionError("Unsupported configuration must not call provider")

    with pytest.raises(ProviderError, match="images"):
        invoke(forbidden, request=request)
    with pytest.raises(ProviderError, match="seed"):
        invoke(forbidden, settings(seed=42))


def test_native_settings_read_canonical_key_without_affecting_explicit_key(tmp_path):
    path = tmp_path / ".env"
    path.write_text(
        "EXAM_PROVIDER=anthropic\nEXAM_MODEL=nghi/claude-haiku-4.5\n"
        "EXAM_BASE_URL=https://api.nghimmo.com/v1\nANTHROPIC_API_KEY=" + KEY
    )
    config = Settings(_env_file=path)
    assert config.api_key.get_secret_value() == KEY
    assert "anthropic_api_key" not in config.model_dump() and KEY not in repr(config)
    explicit = Settings(_env_file=path, api_key="fixture-explicit")
    assert explicit.api_key.get_secret_value() == "fixture-explicit"
    assert AnthropicMessagesProvider(config, None).name == "anthropic"
