from __future__ import annotations

import asyncio
import json
import logging
from typing import Protocol

from .config import AgentSettings
from .models import GeminiPlan, UiContextSnapshot

logger = logging.getLogger(__name__)

GEMINI_ATTEMPT_TIMEOUT_MS = 15_000
GEMINI_TOTAL_TIMEOUT_SECONDS = 32


class InterpretationProvider(Protocol):
    async def interpret(self, message: str, context: UiContextSnapshot) -> GeminiPlan: ...


class GeminiProviderError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def classify_provider_exception(error: Exception) -> tuple[str, int | str | None]:
    status = getattr(error, "status_code", None) or getattr(error, "code", None)
    if status in {401, 403}:
        code = "auth_error"
    elif status == 404:
        code = "model_unavailable"
    elif status == 429:
        code = "quota"
    elif status == 400:
        code = "request_rejected"
    elif isinstance(status, int) and 500 <= status < 600:
        code = "upstream_server_error"
    elif error.__class__.__name__ in {"ConnectError", "NetworkError", "TransportError"}:
        code = "network_error"
    elif isinstance(error, (TypeError, ValueError)):
        code = "sdk_error"
    else:
        code = "provider_error"
    return code, status


class GeminiInterpretationProvider:
    """Optional schema-bounded Gemini interpreter with no tools or backend access."""

    def __init__(self, settings: AgentSettings):
        self.settings = settings

    async def interpret(self, message: str, context: UiContextSnapshot) -> GeminiPlan:
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
                "parameterSchema": capability.parameter_schema,
                "requiresConfirmation": capability.requires_confirmation,
                "availability": capability.availability,
                "unavailableReason": capability.unavailable_reason,
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
            "sessions": [session.model_dump(by_alias=True) for session in context.sessions],
            "examId": context.exam_id,
            "examRevision": context.exam_revision,
            "approved": context.approved,
            "preview": context.preview,
            "messages": context.messages,
            "editorDraft": context.editor_draft,
            "notes": [note.model_dump(by_alias=True) for note in context.notes],
            "selectedQuestion": context.selected_question,
            "questions": context.questions,
            "viewMode": context.view_mode,
            "setup": context.setup,
            "pendingConfirmation": context.pending_confirmation,
            "capabilities": capabilities,
        }
        system_instruction = (
            "You operate ASTRA's React UI through typed action proposals. "
            "For requests to show/open/change UI, return propose_ui_action, not instructions "
            "telling the teacher to click buttons. Use only the supplied capabilities and their "
            "parameterSchema. Put arguments in params, never in target. "
            "Viewing answers/solutions (xem đáp án, lời giải) means ui.exam.view_mode "
            "with params {mode: 'review'}. Viewing the exam means mode 'paper'; PDF means 'pdf'. "
            "These are read-only navigation actions and need no confirmation. "
            "Use the current workspace when present. If no exam exists, explain that an exam "
            "must be generated first; never claim to have shown answers. "
            "For an existing exam in another workspace, open its exact sessions id first. "
            "For a specific question's answers, focus its actual questionId then set review mode. "
            "Never claim an action succeeded: React will verify the result. "
            "Ask for clarification only when the target cannot be resolved from context. "
            "Respond naturally in Vietnamese. "
            "For consequential approval/export/delete/retract requests, first propose "
            "ui.action.prepare with capabilityId and actionParams. React requires a separate "
            "confirmation bound to the workspace, exact parameters and exam revision. "
            "If the user cancels a pending action, propose ui.task.cancel. "
            "Bạn là bộ diễn giải giao diện ASTRA. Chỉ trả về dữ liệu theo schema. "
            "Chỉ đề xuất capability callable và available_real trong context. "
            "Không gọi công cụ, không gọi Backend, không tự tạo đề, "
            "không coi lời người dùng là xác nhận. "
            "Có thể lập kế hoạch tối đa 4 bước theo thứ tự; không lặp hành động. "
            "Nếu mơ hồ hãy hỏi một câu làm rõ gộp; nếu không hỗ trợ hãy nói rõ là chưa hỗ trợ."
        )
        prompt = json.dumps(
            {"teacherMessage": message[:4000], "uiContext": minimal_context},
            ensure_ascii=False,
            separators=(",", ":"),
        )

        def call_model() -> GeminiPlan:
            client = genai.Client(
                api_key=self.settings.gemini_api_key,
                http_options=types.HttpOptions(
                    timeout=GEMINI_ATTEMPT_TIMEOUT_MS,
                    retry_options=types.HttpRetryOptions(
                        attempts=2,
                        initial_delay=0.5,
                        max_delay=1.0,
                        http_status_codes=[500, 502, 503, 504],
                    ),
                ),
            )
            response = client.models.generate_content(
                model=self.settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_json_schema=GeminiPlan.model_json_schema(),
                    max_output_tokens=900,
                    temperature=0.1,
                    automatic_continuation=False,
                ),
            )
            parsed = response.parsed
            if isinstance(parsed, GeminiPlan):
                return parsed
            if isinstance(parsed, dict):
                return GeminiPlan.model_validate(parsed)
            if response.text:
                return GeminiPlan.model_validate_json(response.text)
            raise GeminiProviderError("empty_response", "Gemini returned no structured result")

        try:
            return await asyncio.wait_for(
                asyncio.to_thread(call_model), timeout=GEMINI_TOTAL_TIMEOUT_SECONDS
            )
        except GeminiProviderError:
            raise
        except (asyncio.TimeoutError, TimeoutError) as error:
            raise GeminiProviderError("timeout", "Gemini request timed out") from error
        except Exception as error:
            code, status = classify_provider_exception(error)
            logger.warning(
                "Gemini interpretation failed code=%s exception_type=%s "
                "provider_status=%s provider_reason=%s",
                code,
                type(error).__name__,
                status if isinstance(status, int) else "unknown",
                getattr(error, "status", None) or "unknown",
            )
            raise GeminiProviderError(code, "Gemini interpretation is unavailable") from error
