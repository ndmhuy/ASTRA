from __future__ import annotations

import asyncio
import json
from typing import Protocol

from .config import AgentSettings
from .models import GeminiDecision, UiContextSnapshot


class InterpretationProvider(Protocol):
    async def interpret(self, message: str, context: UiContextSnapshot) -> GeminiDecision: ...


class GeminiProviderError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class GeminiInterpretationProvider:
    """Optional schema-bounded Gemini interpreter with no tools or backend access."""

    def __init__(self, settings: AgentSettings):
        self.settings = settings

    async def interpret(self, message: str, context: UiContextSnapshot) -> GeminiDecision:
        if not self.settings.llm_enabled:
            raise GeminiProviderError("disabled", "Gemini interpretation is disabled")
        if not self.settings.gemini_api_key:
            raise GeminiProviderError("missing_key", "Gemini API key is not configured")
        try:
            from google import genai
            from google.genai import types
        except ImportError as error:
            raise GeminiProviderError(
                "sdk_missing", "Install the optional google-genai dependency"
            ) from error

        capabilities = [
            {
                "id": capability.id,
                "description": capability.description,
                "callable": capability.callable,
                "status": capability.status,
            }
            for capability in context.capabilities
        ]
        minimal_context = {
            "workspaceId": context.workspace_id,
            "screen": context.screen,
            "activeModal": context.active_modal,
            "stateVersion": context.state_version,
            "activeJob": context.active_job.model_dump(by_alias=True)
            if context.active_job
            else None,
            "sessionCount": len(context.sessions),
            "notes": [note.model_dump(by_alias=True) for note in context.notes],
            "capabilities": capabilities,
        }
        system_instruction = (
            "Bạn là bộ diễn giải giao diện ASTRA. Chỉ trả về dữ liệu theo schema. "
            "Chỉ đề xuất capability callable và available_real trong context. "
            "Không gọi công cụ, không gọi Backend, không tự tạo đề, "
            "không coi lời người dùng là xác nhận. "
            "Nếu mơ hồ hãy hỏi một câu làm rõ gộp; nếu không hỗ trợ hãy nói rõ là chưa hỗ trợ."
        )
        prompt = json.dumps(
            {"teacherMessage": message[:4000], "uiContext": minimal_context},
            ensure_ascii=False,
            separators=(",", ":"),
        )

        def call_model() -> GeminiDecision:
            client = genai.Client(api_key=self.settings.gemini_api_key)
            response = client.models.generate_content(
                model=self.settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=GeminiDecision,
                    max_output_tokens=500,
                    temperature=0.1,
                ),
            )
            parsed = response.parsed
            if isinstance(parsed, GeminiDecision):
                return parsed
            if response.text:
                return GeminiDecision.model_validate_json(response.text)
            raise GeminiProviderError("empty_response", "Gemini returned no structured result")

        try:
            return await asyncio.wait_for(asyncio.to_thread(call_model), timeout=15)
        except GeminiProviderError:
            raise
        except asyncio.TimeoutError as error:
            raise GeminiProviderError("timeout", "Gemini request timed out") from error
        except Exception as error:
            status = getattr(error, "status_code", None) or getattr(error, "code", None)
            if status in {401, 403}:
                code = "auth_error"
            elif status == 404:
                code = "model_unavailable"
            elif status == 429:
                code = "quota"
            else:
                code = "provider_error"
            raise GeminiProviderError(code, "Gemini interpretation is unavailable") from error
