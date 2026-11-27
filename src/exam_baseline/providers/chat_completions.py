"""HTTP Chat Completions adapter. Wire-level assumptions stay in this module."""

import base64
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from math import isfinite
from typing import Any

import httpx

from exam_baseline.config import Settings
from exam_baseline.core.contracts import Completion, CompletionRequest, ProviderError
from exam_baseline.core.models import TokenUsage
from exam_baseline.providers.budget import SpendLedger


def _retry_after_seconds(value: str | None) -> float | None:
    if not value:
        return None
    try:
        delay = float(value)
    except ValueError:
        try:
            until = parsedate_to_datetime(value)
            delay = (until - datetime.now(timezone.utc)).total_seconds()
        except (TypeError, ValueError, OverflowError):
            return None
        return max(0.0, delay)
    return delay if delay >= 0 and isfinite(delay) else None


class ChatCompletionsProvider:
    name = "chat_completions"

    def __init__(self, settings: Settings, client: httpx.AsyncClient):
        self.model = settings.model
        self.supports_images = settings.supports_images
        self.input_price_per_million = settings.input_price_per_million
        self.output_price_per_million = settings.output_price_per_million
        self.client = client
        gateway = settings.gateway()
        self.url = (gateway.base("openai") if gateway else settings.base_url.rstrip("/")) + (
            "/chat/completions"
        )
        self.timeout = settings.timeout_seconds
        key = settings.api_key.get_secret_value() if settings.api_key and not gateway else ""
        self.headers = gateway.headers() if gateway else {"Authorization": f"Bearer {key}"}
        self.strict = settings.structured_output_strict
        self.schema_as_tool = settings.schema_as_tool
        self.max_output_tokens = settings.max_output_tokens
        self.ledger = SpendLedger(settings) if settings.spend_limit_usd is not None else None
        self.parameters: dict[str, Any] = {
            settings.token_limit_field: settings.max_output_tokens,
            "response_format": {"type": settings.response_format},
        }
        if settings.temperature is not None:
            self.parameters["temperature"] = settings.temperature
        if settings.seed is not None:
            self.parameters["seed"] = settings.seed
        if settings.reasoning_effort is not None:
            self.parameters["reasoning_effort"] = settings.reasoning_effort

    async def complete(self, request: CompletionRequest) -> Completion:
        if request.images and not self.supports_images:
            raise ProviderError("vision_required", "This provider is not configured for images.")
        content: Any = request.user
        if request.images:
            content = [{"type": "text", "text": request.user}] + [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{image.mime};base64,"
                        + base64.b64encode(image.data).decode("ascii")
                    },
                }
                for image in request.images
            ]
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": request.system},
                {"role": "user", "content": content},
            ],
            **self.parameters,
        }
        if self.parameters["response_format"]["type"] == "json_schema":
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "exam_response", "schema": request.output_schema},
            }
            if self.strict:
                payload["response_format"]["json_schema"]["strict"] = True
        if self.schema_as_tool:
            # Claude's strict JSON grammar cannot express arbitrary dictionaries
            # or all Pydantic bounds. Forced tool arguments carry the full schema;
            # agent boundary validation and bounded repair remain authoritative.
            payload.pop("response_format", None)
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": "astra_output",
                        "description": "Return the requested structured result.",
                        "parameters": request.output_schema,
                    },
                }
            ]
            payload["tool_choice"] = {"type": "function", "function": {"name": "astra_output"}}
        reservation = self.ledger.reserve(payload, self.max_output_tokens) if self.ledger else None
        try:
            completion = await self._send(payload)
        except ProviderError as exc:
            if self.ledger:
                self.ledger.settle(
                    reservation,
                    exc.completion.usage if exc.completion else None,
                    unbilled=exc.completion is None
                    and exc.http_status is not None
                    and 400 <= exc.http_status < 500
                    and exc.http_status != 408,
                )
            raise
        if self.ledger:
            self.ledger.settle(reservation, completion.usage)
        return completion

    async def _send(self, payload):
        try:
            response = await self.client.post(
                self.url,
                json=payload,
                headers=self.headers,
                timeout=self.timeout,
                follow_redirects=False,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise ProviderError("provider_timeout", "LLM provider timed out.") from exc
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            code, message = {
                400: ("provider_bad_request", "Provider rejected the model or request options."),
                401: ("provider_auth_error", "Provider authentication failed; check the API key."),
                403: ("provider_access_denied", "Provider denied access to this model or project."),
                404: ("provider_not_found", "Provider endpoint or model was not found."),
                429: ("provider_rate_limited", "Provider quota or rate limit was exceeded."),
                500: ("provider_internal_error", "Provider encountered an internal server error."),
                502: (
                    "provider_bad_gateway",
                    "Provider gateway could not reach its upstream service.",
                ),
                503: ("provider_unavailable", "Provider is temporarily unavailable or overloaded."),
                504: ("provider_gateway_timeout", "Provider gateway timed out."),
            }.get(
                status,
                ("provider_http_error", "LLM provider rejected the request."),
            )
            if status == 429:
                try:
                    provider_code = exc.response.json()["error"]["code"]
                except (KeyError, TypeError, ValueError):
                    provider_code = None
                if provider_code in ("insufficient_quota", "billing_hard_limit_reached"):
                    code = "provider_quota_exhausted"
                    message = "The API project has exhausted its quota or billing limit."
            raise ProviderError(
                code,
                f"HTTP {status}: {message}",
                http_status=status,
                retry_after_seconds=_retry_after_seconds(exc.response.headers.get("Retry-After")),
            ) from exc
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
            if self.schema_as_tool:
                content = None
                tools = message.get("tool_calls") or []
                if len(tools) == 1:
                    function = tools[0].get("function") or {}
                    if function.get("name") == "astra_output":
                        content = function.get("arguments")
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
            if choice.get("finish_reason") != ("tool_calls" if self.schema_as_tool else "stop"):
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
