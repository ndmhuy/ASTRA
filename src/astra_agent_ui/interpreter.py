from __future__ import annotations

import re
import unicodedata
import uuid
from typing import Literal

from .gemini_provider import GeminiProviderError, InterpretationProvider
from .knowledge import ApplicationKnowledgeSource, RegistryKnowledgeSource
from .models import (
    AgentDecision,
    AgentTurnRequest,
    AgentTurnResponse,
    GeminiDecision,
    GeminiPlan,
    UiContextSnapshot,
)


def normalize_vietnamese(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.casefold().replace("đ", "d"))
    return " ".join("".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn").split())


class AgentInterpreter:
    def __init__(
        self,
        provider: InterpretationProvider | None = None,
        knowledge: ApplicationKnowledgeSource | None = None,
        mode: Literal["offline", "gemini"] = "offline",
    ):
        self.provider = provider
        self.knowledge = knowledge or RegistryKnowledgeSource()
        self.mode = mode

    def _action(
        self,
        context: UiContextSnapshot,
        capability_id: str,
        text: str,
        params: dict[str, object] | None = None,
        target: dict[str, object] | None = None,
    ) -> AgentDecision:
        return AgentDecision(
            kind="propose_ui_action",
            text=text,
            actionId=str(uuid.uuid4()),
            capabilityId=capability_id,
            expectedStateVersion=context.state_version,
            params=params or {},
            target=target or {},
        )

    @staticmethod
    def _callable(context: UiContextSnapshot, capability_id: str) -> bool:
        return any(
            item.id == capability_id and item.callable and item.status == "available_real"
            for item in context.capabilities
        )

    def deterministic(self, message: str, context: UiContextSnapshot) -> AgentDecision | None:
        normalized = normalize_vietnamese(message)
        if len(message) > 4000:
            return AgentDecision(
                kind="clarify",
                text="Yêu cầu quá dài. Thầy cô vui lòng rút gọn còn dưới 4.000 ký tự.",
            )
        if re.search(r"\b(word|docx)\b", normalized):
            return AgentDecision(
                kind="unsupported",
                text=(
                    "Hiện ASTRA chưa hỗ trợ xuất Word trong phiên bản đang sử dụng. "
                    "Các định dạng đã xác minh là PDF, LaTeX và JSON sau quy trình "
                    "xem trước, phê duyệt."
                ),
            )
        if "v-act" in normalized or "vact" in normalized or "danh gia nang luc" in normalized:
            return AgentDecision(
                kind="unsupported",
                text=(
                    "Hiện giao diện đang dùng chưa hỗ trợ luồng V-ACT. ASTRA chỉ xác minh "
                    "thiết lập Toán THPT lớp 12, 22 câu, 90 phút."
                ),
            )
        if any(term in normalized for term in ("dinh kem", "tai tep", "upload")):
            return AgentDecision(
                kind="unsupported",
                text=(
                    "Hiện ASTRA chưa hỗ trợ tải hoặc đọc tệp đính kèm trong phiên bản đang sử dụng."
                ),
            )
        if any(term in normalized for term in ("tim web", "tim mang", "search web")):
            return AgentDecision(
                kind="unsupported",
                text=(
                    "Hiện ASTRA chưa có chức năng tìm web đã được xác minh "
                    "trong phiên bản đang sử dụng."
                ),
            )
        if re.search(r"\b(xoa|delete)\b.*\b(workspace|de|phien)\b", normalized):
            return AgentDecision(
                kind="unsupported",
                text=(
                    "Agent chưa được phép xóa workspace. Thầy cô có thể dùng nút Xóa "
                    "trong danh sách và xác nhận trực tiếp trên giao diện."
                ),
            )
        if "lich su" in normalized:
            return AgentDecision(
                kind="unsupported",
                text=(
                    "Agent chưa có hành động mở màn hình lịch sử đã được xác minh. "
                    "Tôi không thực hiện bước tiếp theo của yêu cầu nhiều bước này."
                ),
            )
        if any(term in normalized for term in ("lam duoc gi", "co chuc nang gi", "giup duoc gi")):
            answer = self.knowledge.answer(message, context.capabilities)
            return AgentDecision(
                kind="answer", text=answer or "Thông tin trợ giúp hiện chưa khả dụng."
            )
        if any(term in normalized for term in ("dang toi dau", "tien do", "trang thai")):
            if context.active_job:
                return AgentDecision(
                    kind="answer",
                    text=(
                        f"Đề đang ở giai đoạn “{context.active_job.stage}”, "
                        f"tiến độ {context.active_job.percent}% "
                        f"(nguồn trạng thái: {context.active_job.source}). "
                        "ASTRA không suy đoán thời gian hoàn tất hay tiến độ từng câu."
                    ),
                )
            return AgentDecision(
                kind="answer", text="Workspace hiện tại không có tác vụ tạo đề đang chạy."
            )

        note_id_match = re.search(r"(?:sua ghi chu|huy ghi chu)\s+([0-9a-f-]{20,})", normalized)
        if note_id_match:
            note_id = note_id_match.group(1)
            note = next(
                (item for item in context.notes if item.id == note_id and item.status == "pending"),
                None,
            )
            if not note:
                return AgentDecision(
                    kind="clarify", text="Tôi không tìm thấy ghi chú đang chờ có mã đó."
                )
            if normalized.startswith("huy ghi chu") and self._callable(context, "ui.note.cancel"):
                return self._action(
                    context, "ui.note.cancel", "Tôi sẽ hủy ghi chú đã chọn.", {"noteId": note_id}
                )
            updated_text = message.split(":", 1)[1].strip() if ":" in message else ""
            if not updated_text:
                return AgentDecision(
                    kind="clarify", text="Thầy cô muốn đổi nội dung ghi chú thành gì?"
                )
            if self._callable(context, "ui.note.update"):
                return self._action(
                    context,
                    "ui.note.update",
                    "Tôi sẽ cập nhật ghi chú đang chờ; thay đổi này vẫn chưa sửa đề.",
                    {"noteId": note_id, "requestedChange": updated_text[:500]},
                )

        question_match = re.search(r"\bcau\s+(\d{1,3})\b", normalized)
        explicit_change = any(term in normalized for term in ("sua", "doi", "de hon", "kho hon"))
        remark_only = (
            any(term in normalized for term in ("nhi", "ha", "khong")) and not explicit_change
        )
        if context.active_job and question_match and explicit_change and not remark_only:
            if self._callable(context, "ui.note.add"):
                return self._action(
                    context,
                    "ui.note.add",
                    "Tôi sẽ ghi lại yêu cầu để thầy cô xem sau khi đề hoàn tất; "
                    "ghi chú này chưa sửa đề đang chạy.",
                    {
                        "targetQuestion": int(question_match.group(1)),
                        "requestedChange": message[:500],
                        "teacherText": message[:500],
                    },
                )
        if (
            context.active_job
            and question_match
            and any(term in normalized for term in ("bo note", "huy note", "thoi giu"))
        ):
            matching = [
                note
                for note in context.notes
                if note.target_question == int(question_match.group(1)) and note.status == "pending"
            ]
            if len(matching) == 1 and self._callable(context, "ui.note.cancel"):
                return self._action(
                    context,
                    "ui.note.cancel",
                    "Tôi sẽ hủy ghi chú đang chờ cho câu này.",
                    {"noteId": matching[0].id},
                )
            return AgentDecision(
                kind="clarify",
                text=(
                    "Tôi chưa xác định được đúng ghi chú cần hủy. Thầy cô vui lòng nêu mã ghi chú."
                ),
            )
        if question_match and any(term in normalized for term in ("xem", "mo", "focus")):
            if self._callable(context, "ui.question.focus"):
                return self._action(
                    context,
                    "ui.question.focus",
                    "Tôi sẽ chuyển tiêu điểm đến câu hỏi đã chọn.",
                    {"questionId": int(question_match.group(1))},
                )
            return AgentDecision(
                kind="unsupported",
                text="Hiện ASTRA chưa có hành động Agent để chuyển tiêu điểm đến một câu cụ thể.",
            )
        if any(
            term in normalized for term in ("thu gon sidebar", "thu gon thanh", "an sidebar")
        ) and self._callable(context, "ui.sidebar.set_collapsed"):
            return self._action(
                context,
                "ui.sidebar.set_collapsed",
                "Tôi sẽ thu gọn thanh điều hướng.",
                {"collapsed": True},
            )
        if any(
            term in normalized for term in ("mo sidebar", "mo rong thanh", "hien sidebar")
        ) and self._callable(context, "ui.sidebar.set_collapsed"):
            return self._action(
                context,
                "ui.sidebar.set_collapsed",
                "Tôi sẽ mở rộng thanh điều hướng.",
                {"collapsed": False},
            )
        if any(
            term in normalized for term in ("trang dau", "man hinh dau", "ve nha")
        ) and self._callable(context, "ui.navigate"):
            return self._action(
                context,
                "ui.navigate",
                "Tôi sẽ đưa thầy cô về trang bắt đầu.",
                {"destination": "start"},
            )
        setup_terms = ("mo setup", "mo cau hinh", "mo thiet lap", "soan tu mau", "ra de", "tao de")
        if any(term in normalized for term in setup_terms):
            if re.search(r"\b(dung|khong|chua)\s+tao\b", normalized) and "mo" not in normalized:
                return AgentDecision(
                    kind="answer", text="Đã hiểu: tôi sẽ không mở hay bắt đầu tạo đề."
                )
            if self._callable(context, "ui.exam.open_setup"):
                return self._action(
                    context,
                    "ui.exam.open_setup",
                    "Tôi sẽ mở thiết lập thật của giao diện. Việc tạo đề chỉ bắt đầu "
                    "khi thầy cô xác nhận trong hộp thiết lập.",
                    {},
                )
        if any(
            term in normalized for term in ("mo trang soan", "man hinh soan", "soan chi tiet")
        ) and self._callable(context, "ui.session.create"):
            return self._action(
                context,
                "ui.session.create",
                "Tôi sẽ mở một workspace soạn chi tiết mới.",
                {"mode": "custom"},
            )
        if any(term in normalized for term in ("de vua roi", "de hoi nay", "workspace vua")):
            if len(context.sessions) == 1 and self._callable(context, "ui.session.open"):
                return self._action(
                    context,
                    "ui.session.open",
                    "Tôi sẽ mở workspace duy nhất đang có.",
                    {"workspaceId": context.sessions[0].id},
                )
            if len(context.sessions) > 1:
                names = ", ".join(session.title for session in context.sessions[:4])
                return AgentDecision(
                    kind="clarify",
                    text=f"Có nhiều workspace: {names}. Thầy cô muốn mở workspace nào?",
                )
        return None

    def _validate_model_decision(
        self, decision: GeminiDecision, context: UiContextSnapshot
    ) -> AgentDecision:
        if decision.kind != "propose_ui_action":
            return AgentDecision(**decision.model_dump(by_alias=True))
        if not decision.capability_id or not self._callable(context, decision.capability_id):
            return AgentDecision(
                kind="clarify",
                text=(
                    "Tôi chưa thể xác minh hành động đó trong giao diện hiện tại. "
                    "Thầy cô vui lòng chọn một thao tác đang được hỗ trợ."
                ),
            )
        return self._action(
            context,
            decision.capability_id,
            decision.text,
            decision.params,
            decision.target,
        )

    async def interpret(self, request: AgentTurnRequest) -> AgentTurnResponse:
        if self.mode == "offline":
            deterministic = self.deterministic(request.message, request.context)
            if deterministic is None:
                deterministic = AgentDecision(
                    kind="clarify",
                    text=(
                        "Chế độ offline chưa hiểu chắc yêu cầu. Thầy cô có thể nói rõ muốn mở "
                        "trang, mở thiết lập hay xem trạng thái đề không?"
                    ),
                )
            return AgentTurnResponse(
                turnId=request.turn_id,
                decisions=[deterministic],
                provider="offline",
                knowledgeStatus=self.knowledge.status,
            )
        if self.provider is None:
            raise GeminiProviderError(
                "provider_not_configured", "Gemini provider is not configured for AI mode"
            )
        model_plan = await self.provider.interpret(request.message, request.context)
        raw_decisions = model_plan.decisions if isinstance(model_plan, GeminiPlan) else [model_plan]
        decisions: list[AgentDecision] = []
        seen: set[tuple[str | None, str, str]] = set()
        for raw in raw_decisions[:4]:
            key = (raw.capability_id, repr(raw.params), repr(raw.target))
            if raw.kind == "propose_ui_action" and key in seen:
                continue
            seen.add(key)
            decisions.append(self._validate_model_decision(raw, request.context))
        if not decisions:
            decisions = [
                AgentDecision(kind="clarify", text="Kế hoạch không có bước giao diện hợp lệ.")
            ]
        return AgentTurnResponse(
            turnId=request.turn_id,
            decisions=decisions,
            provider="gemini",
            knowledgeStatus=self.knowledge.status,
        )
