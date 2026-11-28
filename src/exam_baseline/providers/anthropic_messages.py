"""Anthropic Messages wire adapter. Academic prompts and schemas pass through intact."""

import base64
import json

from exam_baseline.core.contracts import Completion, ProviderError
from exam_baseline.core.models import TokenUsage
from exam_baseline.providers.chat_completions import ChatCompletionsProvider


class AnthropicMessagesProvider(ChatCompletionsProvider):
    name = "anthropic"

    def __init__(self, settings, client):
        if settings.use_ai_gateway:
            raise ValueError("Anthropic Messages uses its configured direct API endpoint")
        super().__init__(settings, client)
        base = settings.base_url.rstrip("/")
        self.url = base + ("/messages" if base.endswith("/v1") else "/v1/messages")
        self.headers = {
            "x-api-key": settings.api_key.get_secret_value() if settings.api_key else "",
            "anthropic-version": "2023-06-01",
        }
        self.parameters = {"max_tokens": settings.max_output_tokens}
        if settings.temperature is not None:
            self.parameters["temperature"] = settings.temperature
        self.seed = settings.seed

    async def complete(self, request):
        if request.images and not self.supports_images:
            raise ProviderError("vision_required", "This provider is not configured for images.")
        if self.seed is not None:
            raise ProviderError("provider_bad_request", "Anthropic Messages does not support seed.")
        content = request.user
        if request.images:
            content = [{"type": "text", "text": request.user}] + [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": image.mime,
                        "data": base64.b64encode(image.data).decode("ascii"),
                    },
                }
                for image in request.images
            ]
        payload = {
            "model": self.model,
            "system": request.system,
            "messages": [{"role": "user", "content": content}],
            **self.parameters,
            "tools": [
                {
                    "name": "astra_output",
                    "description": "Return the requested structured result.",
                    "input_schema": request.output_schema,
                }
            ],
            "tool_choice": {"type": "tool", "name": "astra_output"},
        }
        return await self._complete_payload(payload)

    async def _send(self, payload):
        try:
            return await super()._send(payload)
        except ProviderError as error:
            if error.http_status == 529:
                raise ProviderError(
                    "provider_unavailable",
                    "Anthropic API is temporarily overloaded.",
                    http_status=529,
                    retry_after_seconds=error.retry_after_seconds,
                    retryable=True,
                ) from error.__cause__
            raise

    def _parse_response(self, response):
        completion = None
        try:
            data = response.json()
            if data.get("type") != "message" or data.get("role") != "assistant":
                raise ValueError("invalid message envelope")
            content = data["content"]
            if not isinstance(content, list) or any(
                not isinstance(block, dict) for block in content
            ):
                raise ValueError("invalid content blocks")
            tools = [block for block in content if block.get("type") == "tool_use"]
            tool = tools[0] if len(tools) == 1 else {}
            arguments = tool.get("input") if tool.get("name") == "astra_output" else None
            text = json.dumps(arguments, ensure_ascii=False) if isinstance(arguments, dict) else ""
            raw_usage = data.get("usage") or {}
            # Anthropic separates uncached, cache-write and cache-read input tokens.
            counts = [
                raw_usage.get(name, 0)
                for name in (
                    "input_tokens",
                    "cache_creation_input_tokens",
                    "cache_read_input_tokens",
                )
            ]
            incoming = None
            if raw_usage.get("input_tokens") is not None:
                if any(type(count) is not int or count < 0 for count in counts):
                    raise ValueError("invalid input usage")
                incoming = sum(counts)
            model, response_id = data.get("model", self.model), data.get("id")
            if not isinstance(model, str) or not model:
                raise ValueError("invalid model")
            if response_id is not None and not isinstance(response_id, str):
                raise ValueError("invalid response ID")
            completion = Completion(
                text=text,
                model=model,
                response_id=response_id,
                usage=TokenUsage(
                    input_tokens=incoming, output_tokens=raw_usage.get("output_tokens")
                ),
            )
            if data.get("stop_reason") == "refusal":
                raise ProviderError(
                    "provider_refusal", "LLM provider refused the request.", completion
                )
            if data.get("stop_reason") != "tool_use":
                raise ProviderError(
                    "provider_incomplete", "Structured response was not completed.", completion
                )
            if not text:
                raise ValueError("exactly one astra_output object is required")
            return completion
        except (ValueError, KeyError, TypeError, AttributeError) as error:
            raise ProviderError(
                "provider_protocol_error", "Invalid Anthropic message envelope.", completion
            ) from error
