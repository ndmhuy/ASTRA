"""HTTP Chat Completions adapter. Wire-level assumptions stay in this module."""

from typing import Any

import httpx

from ..config import Settings
from ..contracts import Completion, CompletionRequest, ProviderError
from ..models import TokenUsage


class ChatCompletionsProvider:
    name = "chat_completions"

    def __init__(self, settings: Settings, client: httpx.AsyncClient):
        self.model = settings.model
        self.client = client
        self.url = settings.base_url.rstrip("/") + "/chat/completions"
        self.timeout = settings.timeout_seconds
        self.api_key = settings.api_key.get_secret_value() if settings.api_key else ""
        self.parameters: dict[str, Any] = {
            settings.token_limit_field: settings.max_output_tokens,
            "response_format": {"type": settings.response_format},
        }
        if settings.temperature is not None:
            self.parameters["temperature"] = settings.temperature
        if settings.seed is not None:
            self.parameters["seed"] = settings.seed

    async def complete(self, request: CompletionRequest) -> Completion:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": request.system},
                {"role": "user", "content": request.user},
            ],
            **self.parameters,
        }
        try:
            response = await self.client.post(
                self.url,
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise ProviderError("provider_timeout", "LLM provider timed out.") from exc
        except httpx.HTTPStatusError as exc:
            code, message = {
                400: ("provider_bad_request", "Provider rejected the model or request options."),
                401: ("provider_auth_error", "Provider authentication failed; check the API key."),
                403: ("provider_access_denied", "Provider denied access to this model or project."),
                404: ("provider_not_found", "Provider endpoint or model was not found."),
                429: ("provider_rate_limited", "Provider quota or rate limit was exceeded."),
            }.get(
                exc.response.status_code,
                ("provider_http_error", "LLM provider rejected the request."),
            )
            raise ProviderError(code, message) from exc
        except httpx.RequestError as exc:
            raise ProviderError("provider_unreachable", "Could not reach LLM provider.") from exc
        completion = None
        try:
            data = response.json()
            choice = data["choices"][0]
            message = choice["message"]
            raw_usage = data.get("usage") or {}
            usage = TokenUsage(
                input_tokens=raw_usage.get("prompt_tokens"),
                output_tokens=raw_usage.get("completion_tokens"),
            )
            model = data.get("model", self.model)
            response_id = data.get("id")
            content = message.get("content")
            if not isinstance(model, str) or not model:
                raise ValueError("invalid model")
            if response_id is not None and not isinstance(response_id, str):
                raise ValueError("invalid response ID")
            completion = Completion(
                text=content if isinstance(content, str) else "",
                model=model,
                usage=usage,
                response_id=response_id,
            )
            if message.get("refusal") or choice.get("finish_reason") == "content_filter":
                raise ProviderError(
                    "provider_refusal", "LLM provider refused the request.", completion
                )
            if choice.get("finish_reason") != "stop":
                raise ProviderError(
                    "provider_incomplete",
                    "LLM response was truncated or incomplete.",
                    completion,
                )
            if not isinstance(content, str) or not content.strip():
                raise ValueError("missing content")
            return completion
        except (
            ValueError,
            KeyError,
            IndexError,
            TypeError,
            AttributeError,
        ) as exc:
            raise ProviderError(
                "provider_protocol_error", "Invalid LLM provider envelope.", completion
            ) from exc
