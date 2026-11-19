"""Deterministic authorization checks after interpretation, never a fallback LLM."""

import re
import unicodedata

from .models import AgentDecision, AgentTurnRequest


def normalized(text: str) -> str:
    return "".join(
        c
        for c in unicodedata.normalize("NFD", text.casefold().replace("đ", "d"))
        if unicodedata.category(c) != "Mn"
    )


def validate_plan(request: AgentTurnRequest, decisions: list[AgentDecision]) -> list[AgentDecision]:
    text = normalized(request.message)
    context = request.context
    if (
        text.strip(" .!?") in {"tiep tuc", "continue"}
        and context.active_task
        and context.active_task.get("taskStatus") == "awaiting_confirmation"
        and not context.pending_confirmation
    ):
        return [
            AgentDecision(
                kind="clarify",
                text="Xác nhận cũ đã mất hiệu lực. Hãy chuẩn bị lại thao tác với dữ liệu hiện tại.",
            )
        ]
    if re.search(r"\b(word|docx|v-act|vact|tim web|tim google|upload|tai tep)\b", text):
        return [
            AgentDecision(
                kind="unsupported",
                text=(
                    "Yêu cầu này chưa khả dụng trong giao diện hiện tại. "
                    "Không tự thay thế bằng một tác vụ khác; Toán THPT đang được hỗ trợ."
                ),
            )
        ]
    # These workflows have no UI-owned source/format contract. Do not silently
    # replace a bank-only/random request with paid THPT generation.
    if re.search(r"\b(bank_only|hybrid|custom_random|ngan hang|random|ngau nhien)\b", text):
        return [
            AgentDecision(
                kind="unsupported",
                text=(
                    "ASTRA chưa có luồng ngân hàng câu hỏi hoặc đề ngẫu nhiên qua giao diện. "
                    "RAG là tài liệu tham chiếu, không phải ngân hàng câu hỏi đã duyệt. "
                    "Thầy cô muốn dùng định dạng Toán THPT hiện có hay cần một luồng custom riêng?"
                ),
            )
        ]
    actions = [d for d in decisions if d.kind == "propose_ui_action"]
    if not actions:
        return decisions
    for action in actions:
        verbs = {
            "exam.generate.start": "tao|sinh",
            "ui.exam.open_setup": "mo",
            "exam.question.regenerate": "sua|doi|tao lai",
            "exam.export.download": "xuat|tai",
        }.get(action.capability_id or "")
        if verbs and re.search(r"\b(dung|khong|chua)\s+(" + verbs + r")\b", text):
            return [
                AgentDecision(
                    kind="clarify",
                    text="Tôi chưa thực hiện thao tác bị phủ định. Thầy cô muốn làm gì tiếp?",
                )
            ]
    if re.search(r"\b(nhi|ha)\s*[?.!]*$", text) and not re.search(
        r"\b(sua|doi|hay|giup|lam)\b", text
    ):
        return [
            AgentDecision(
                kind="answer", text="Tôi ghi nhận nhận xét; chưa thực hiện chỉnh sửa nào."
            )
        ]
    # A rejected dependency invalidates the plan, not just its own text bubble.
    if any(d.kind in {"clarify", "unsupported"} for d in decisions):
        return [d for d in decisions if d.kind in {"clarify", "unsupported"}][:1]
    if re.search(r"\b(ignore previous|bo qua.*(xac nhan|quyen)|export all)\b", text):
        return [
            AgentDecision(
                kind="clarify",
                text="Mọi thao tác vẫn cần đúng đối tượng, quyền và xác nhận của giáo viên.",
            )
        ]
    explicit_ids = {int(value) for value in re.findall(r"\b(?:cau|question)\s+(\d+)\b", text)}
    explicit = bool(explicit_ids)
    for action in actions:
        params = action.params
        question = params.get("questionId", params.get("targetQuestion"))
        if question is not None:
            if explicit and question not in explicit_ids:
                return [
                    AgentDecision(
                        kind="clarify",
                        text="Kế hoạch chưa khớp số câu yêu cầu. Thầy cô muốn thao tác câu nào?",
                    )
                ]
            if not explicit and (
                not context.selected_question or context.selected_question.get("id") != question
            ):
                return [
                    AgentDecision(
                        kind="clarify",
                        text="Thầy cô muốn thao tác câu nào? Hiện chưa có câu được chọn.",
                    )
                ]
        if action.capability_id in {"ui.session.open", "ui.navigate"} and params.get("workspaceId"):
            if not any(s.id == params["workspaceId"] for s in context.sessions):
                return [
                    AgentDecision(
                        kind="clarify",
                        text="Không tìm thấy workspace yêu cầu. Hãy chọn workspace đang có.",
                    )
                ]
        if (
            action.capability_id == "ui.note.add"
            and not explicit
            and re.search(r"\b(nhi|ha)\s*[?.!]*$", text)
        ):
            return [
                AgentDecision(
                    kind="clarify",
                    text="Thầy cô đang nhận xét hay muốn ghi một yêu cầu chỉnh sửa cụ thể?",
                )
            ]
    return decisions
