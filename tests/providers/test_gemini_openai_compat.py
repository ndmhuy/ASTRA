from __future__ import annotations

import asyncio
import json

import httpx

from exam_baseline.config import Settings
from exam_baseline.core.contracts import CompletionRequest
from exam_baseline.providers.chat_completions import ChatCompletionsProvider


def test_existing_adapter_targets_gemini_openai_compatible_endpoint_and_parses_response() -> None:
    observed = {}

    def handler(request: httpx.Request) -> httpx.Response:
        observed["url"] = str(request.url)
        observed["authorization"] = request.headers.get("Authorization")
        observed["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "id": "synthetic-response-id",
                "model": "gemini-3.1-flash-lite",
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": '{"ok":true}'},
                    }
                ],
                "usage": {"prompt_tokens": 11, "completion_tokens": 4},
            },
        )

    settings = Settings(
        _env_file=None,
        provider="chat_completions",
        model="gemini-3.1-flash-lite",
        api_key="synthetic-test-key",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        token_limit_field="max_tokens",
        response_format="json_schema",
    )

    async def invoke():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = ChatCompletionsProvider(settings, client)
            return await provider.complete(
                CompletionRequest(
                    system="Return the schema.",
                    user="Synthetic test only.",
                    output_schema={
                        "type": "object",
                        "properties": {"ok": {"type": "boolean"}},
                        "required": ["ok"],
                    },
                )
            )

    completion = asyncio.run(invoke())
    assert observed["url"] == (
        "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    )
    assert observed["authorization"] == "Bearer synthetic-test-key"
    assert observed["payload"]["model"] == "gemini-3.1-flash-lite"
    assert observed["payload"]["max_tokens"] == 8192
    assert observed["payload"]["response_format"]["type"] == "json_schema"
    assert completion.text == '{"ok":true}'
    assert completion.model == "gemini-3.1-flash-lite"
