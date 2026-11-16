import asyncio
import json

import httpx
import pytest

from exam_baseline.config import Settings
from exam_baseline.core.contracts import CompletionRequest, ImageInput, ProviderError
from exam_baseline.providers.chat_completions import ChatCompletionsProvider


def test_provider_sends_actual_image_content_and_blocks_text_only_adapter():
    seen = []

    def handler(request):
        seen.append(json.loads(request.content))
        return httpx.Response(
            200, json={"choices": [{"message": {"content": "{}"}, "finish_reason": "stop"}]}
        )

    async def run():
        settings = Settings(
            _env_file=None,
            provider="chat_completions",
            model="test-model",
            api_key="test-key",
            supports_images=True,
        )
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = ChatCompletionsProvider(settings, client)
            request = CompletionRequest("system", "question", {}, (ImageInput(b"actual-bytes"),))
            await provider.complete(request)
            provider.supports_images = False
            with pytest.raises(ProviderError, match="not configured"):
                await provider.complete(request)

    asyncio.run(run())
    assert len(seen) == 1
    assert seen[0]["messages"][1]["content"][1]["image_url"]["url"] == (
        "data:image/png;base64,YWN0dWFsLWJ5dGVz"
    )
