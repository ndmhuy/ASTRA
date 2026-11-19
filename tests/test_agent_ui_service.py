from __future__ import annotations

import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from astra_agent_ui.app import create_app
from astra_agent_ui.config import AgentSettings
from astra_agent_ui.gemini_provider import GeminiInterpretationProvider, GeminiProviderError
from astra_agent_ui.interpreter import AgentInterpreter
from astra_agent_ui.knowledge import ApprovedJsonKnowledgeSource
from astra_agent_ui.models import AgentTurnRequest, GeminiDecision, UiContextSnapshot

ORIGIN = "http://127.0.0.1:5173"


def settings(mode="offline", key=None) -> AgentSettings:
    return AgentSettings(
        host="127.0.0.1",
        port=8010,
        allowed_origins=(ORIGIN,),
        mode=mode,
        gemini_model="gemini-3.8-flash",
        gemini_api_key=key,
    )


def context(**overrides):
    payload = {
        "workspaceId": "workspace-1",
        "screen": "workspace",
        "activeModal": None,
        "sidebarCollapsed": False,
        "stateVersion": 4,
        "activeJob": None,
        "examRevision": None,
        "sessions": [
            {
                "id": "workspace-1",
                "title": "Đề 1",
                "status": "draft",
                "createdAt": "2026-11-18T00:00:00Z",
            }
        ],
        "notes": [],
        "capabilities": [
            {
                "id": "ui.exam.open_setup",
                "description": "Mở thiết lập thật.",
                "status": "available_real",
                "callable": True,
                "requiresConfirmation": False,
            },
            {
                "id": "ui.session.create",
                "description": "Tạo workspace.",
                "status": "available_real",
                "callable": True,
                "requiresConfirmation": False,
            },
            {
                "id": "ui.note.add",
                "description": "Ghi chú chờ.",
                "status": "available_real",
                "callable": True,
                "requiresConfirmation": False,
            },
            {
                "id": "exam.export",
                "description": "Xuất PDF, LaTeX hoặc JSON sau phê duyệt.",
                "status": "available_real",
                "callable": False,
                "requiresConfirmation": True,
            },
            {
                "id": "exam.export.word",
                "description": "Word chưa được hỗ trợ.",
                "status": "unavailable",
                "callable": False,
                "requiresConfirmation": False,
            },
        ],
    }
    payload.update(overrides)
    return payload


def request(message: str, **context_overrides) -> AgentTurnRequest:
    return AgentTurnRequest.model_validate(
        {"turnId": "turn-1", "message": message, "context": context(**context_overrides)}
    )


def test_deterministic_setup_no_key_and_negation() -> None:
    interpreter = AgentInterpreter()
    response = __import__("asyncio").run(
        interpreter.interpret(request("Mở thiết lập đề Toán THPT"))
    )
    decision = response.decisions[0]
    assert response.provider == "offline"
    assert decision.kind == "propose_ui_action"
    assert decision.capability_id == "ui.exam.open_setup"
    assert decision.expected_state_version == 4

    response = __import__("asyncio").run(
        interpreter.interpret(request("Đừng tạo đề, chỉ mở cấu hình"))
    )
    assert response.decisions[0].capability_id == "ui.exam.open_setup"


def test_unsupported_word_vact_and_registry_help() -> None:
    interpreter = AgentInterpreter()
    word = __import__("asyncio").run(interpreter.interpret(request("Xuất file Word")))
    vact = __import__("asyncio").run(interpreter.interpret(request("Ra đề V-ACT")))
    help_result = __import__("asyncio").run(interpreter.interpret(request("ASTRA làm được gì?")))
    assert word.decisions[0].kind == "unsupported"
    assert vact.decisions[0].kind == "unsupported"
    assert help_result.knowledge_status == "verified_ui_registry_only"
    assert "Xuất PDF" in help_result.decisions[0].text


def test_generation_note_is_proposed_without_backend_edit() -> None:
    active_job = {"id": "job-1", "stage": "Đang soạn", "percent": 30, "source": "real"}
    result = __import__("asyncio").run(
        AgentInterpreter().interpret(request("Câu 3 sửa dễ hơn", activeJob=active_job))
    )
    decision = result.decisions[0]
    assert decision.capability_id == "ui.note.add"
    assert decision.params["targetQuestion"] == 3
    assert "backend" not in json.dumps(decision.model_dump()).lower()


class InventedActionProvider:
    async def interpret(self, message, ui_context):
        del message, ui_context
        return GeminiDecision(
            kind="propose_ui_action",
            text="delete",
            capabilityId="backend.deleteExam",
        )


class MissingKeyProvider:
    async def interpret(self, message, ui_context):
        del message, ui_context
        raise GeminiProviderError("missing_key", "missing")


class QuotaProvider:
    async def interpret(self, message, ui_context):
        del message, ui_context
        raise GeminiProviderError("quota", "rate limited")


def test_model_invented_action_is_rejected_and_provider_errors_do_not_fall_back() -> None:
    invented = __import__("asyncio").run(
        AgentInterpreter(provider=InventedActionProvider(), mode="gemini").interpret(
            request("làm việc phức tạp")
        )
    )
    assert invented.decisions[0].kind == "clarify"
    assert invented.decisions[0].capability_id is None

    with pytest.raises(GeminiProviderError, match="missing"):
        __import__("asyncio").run(
            AgentInterpreter(provider=MissingKeyProvider(), mode="gemini").interpret(
                request("làm việc phức tạp")
            )
        )
    with pytest.raises(GeminiProviderError, match="rate limited"):
        __import__("asyncio").run(
            AgentInterpreter(provider=QuotaProvider(), mode="gemini").interpret(
                request("làm việc phức tạp")
            )
        )


def test_ai_mode_calls_provider_even_for_known_offline_command() -> None:
    provider = InventedActionProvider()
    result = __import__("asyncio").run(
        AgentInterpreter(provider=provider, mode="gemini").interpret(
            request("Mở thiết lập đề Toán THPT")
        )
    )
    assert result.provider == "gemini"
    assert result.decisions[0].kind == "clarify"


def test_active_job_status_is_read_only_and_oversized_message_is_rejected() -> None:
    active_job = {"id": "job-1", "stage": "Đang kiểm định", "percent": 61, "source": "real"}
    result = __import__("asyncio").run(
        AgentInterpreter().interpret(request("Đang tới đâu?", activeJob=active_job))
    )
    assert result.decisions[0].kind == "answer"
    assert "61%" in result.decisions[0].text
    assert result.decisions[0].capability_id is None
    with pytest.raises(ValueError):
        request("x" * 4001)


def test_http_origin_session_body_and_secret_boundary() -> None:
    client = TestClient(create_app(settings=settings(), interpreter=AgentInterpreter()))
    assert client.get("/agent/health").json()["businessBackendAccess"] is False
    assert (
        client.post("/agent/session", headers={"Origin": "http://evil.invalid"}).status_code == 403
    )
    session = client.post("/agent/session", headers={"Origin": ORIGIN})
    assert session.status_code == 200
    token = session.json()["token"]
    payload = request("ASTRA làm được gì?").model_dump(by_alias=True)
    assert (
        client.post("/agent/interpret", headers={"Origin": ORIGIN}, json=payload).status_code == 401
    )
    response = client.post(
        "/agent/interpret",
        headers={"Origin": ORIGIN, "X-ASTRA-Agent-Session": token},
        json=payload,
    )
    assert response.status_code == 200
    assert "token" not in response.text
    oversized = client.post(
        "/agent/interpret",
        headers={
            "Origin": ORIGIN,
            "X-ASTRA-Agent-Session": token,
            "Content-Length": str(70 * 1024),
        },
        content=b"{}",
    )
    assert oversized.status_code == 413


def test_gemini_mode_missing_key_and_quota_are_explicit_http_errors() -> None:
    missing_client = TestClient(create_app(settings=settings(mode="gemini")))
    session = missing_client.post("/agent/session", headers={"Origin": ORIGIN}).json()
    payload = request("Mở thiết lập đề").model_dump(by_alias=True)
    missing = missing_client.post(
        "/agent/interpret",
        headers={"Origin": ORIGIN, "X-ASTRA-Agent-Session": session["token"]},
        json=payload,
    )
    assert missing.status_code == 503
    assert missing.json()["error"]["code"] == "gemini_missing_key"

    quota_client = TestClient(
        create_app(
            settings=settings(mode="gemini", key="synthetic-test-key"),
            interpreter=AgentInterpreter(provider=QuotaProvider(), mode="gemini"),
        )
    )
    session = quota_client.post("/agent/session", headers={"Origin": ORIGIN}).json()
    quota = quota_client.post(
        "/agent/interpret",
        headers={"Origin": ORIGIN, "X-ASTRA-Agent-Session": session["token"]},
        json=payload,
    )
    assert quota.status_code == 429
    assert quota.json()["error"]["code"] == "gemini_quota"


def test_gemini_provider_invokes_generate_content_and_uses_structured_response(monkeypatch) -> None:
    calls = []

    class FakeModels:
        def generate_content(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(
                parsed=GeminiDecision(kind="answer", text="Phản hồi mô hình thử nghiệm."),
                text=None,
            )

    class FakeClient:
        def __init__(self, *, api_key, http_options):
            assert api_key == "synthetic-test-key"
            assert http_options["timeout"] == 15_000
            self.models = FakeModels()

    google_module = ModuleType("google")
    genai_module = ModuleType("google.genai")
    types_module = ModuleType("google.genai.types")
    genai_module.Client = FakeClient
    types_module.GenerateContentConfig = lambda **kwargs: kwargs
    types_module.HttpOptions = lambda **kwargs: kwargs
    google_module.genai = genai_module
    monkeypatch.setitem(sys.modules, "google", google_module)
    monkeypatch.setitem(sys.modules, "google.genai", genai_module)
    monkeypatch.setitem(sys.modules, "google.genai.types", types_module)

    provider = GeminiInterpretationProvider(settings(mode="gemini", key="synthetic-test-key"))
    result = __import__("asyncio").run(
        provider.interpret(
            "Hãy giải thích trạng thái hiện tại", UiContextSnapshot.model_validate(context())
        )
    )
    assert result.text == "Phản hồi mô hình thử nghiệm."
    assert calls[0]["model"] == "gemini-3.8-flash"
    assert calls[0]["config"]["response_schema"] is GeminiDecision
    assert calls[0]["config"]["max_output_tokens"] == 500
    assert calls[0]["config"]["automatic_continuation"] is False


def test_future_knowledge_fixture_requires_approval_and_matching_baseline(tmp_path: Path) -> None:
    path = tmp_path / "synthetic-knowledge.json"
    fixture = {
        "approved": True,
        "version": "synthetic-test-only",
        "compatibleBaseline": "sha-test",
        "entries": [{"question": "Cách mở setup?", "answer": "Nội dung fixture thử nghiệm."}],
    }
    path.write_text(json.dumps(fixture, ensure_ascii=False), encoding="utf-8")
    source = ApprovedJsonKnowledgeSource.load(path, "sha-test")
    assert source.status == "approved_document"
    assert source.answer("mở setup", []) == "Nội dung fixture thử nghiệm."
    fixture["approved"] = False
    path.write_text(json.dumps(fixture), encoding="utf-8")
    try:
        ApprovedJsonKnowledgeSource.load(path, "sha-test")
    except ValueError as error:
        assert "not approved" in str(error)
    else:
        raise AssertionError("unapproved fixture was accepted")
    fixture["approved"] = True
    path.write_text(json.dumps(fixture), encoding="utf-8")
    with pytest.raises(ValueError, match="stale or incompatible"):
        ApprovedJsonKnowledgeSource.load(path, "different-sha")
    path.write_text("{not-json", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        ApprovedJsonKnowledgeSource.load(path, "sha-test")


@pytest.mark.parametrize(
    ("teacher_text", "expected_kind", "expected_capability"),
    [
        ("mở setup giúp cô", "propose_ui_action", "ui.exam.open_setup"),
        ("mo cau hinh de thi", "propose_ui_action", "ui.exam.open_setup"),
        ("soạn từ mẫu", "propose_ui_action", "ui.exam.open_setup"),
        ("ra đề toán tốt nghiệp", "propose_ui_action", "ui.exam.open_setup"),
        ("đừng tạo đề", "answer", None),
        ("đừng tạo đề, chỉ mở cấu hình", "propose_ui_action", "ui.exam.open_setup"),
        ("xuất docx", "unsupported", None),
        ("cho cô file Word", "unsupported", None),
        ("ra đề đánh giá năng lực V-ACT", "unsupported", None),
        ("upload tài liệu này", "unsupported", None),
        ("tìm web hộ cô", "unsupported", None),
        ("xóa workspace này", "unsupported", None),
        ("ASTRA có chức năng gì", "answer", None),
        ("giúp được gì?", "answer", None),
        ("đang tới đâu?", "answer", None),
        ("xem câu 5", "unsupported", None),
        ("mở trang soạn", "propose_ui_action", "ui.session.create"),
        ("soan chi tiet", "propose_ui_action", "ui.session.create"),
        ("thu gọn sidebar", "clarify", None),
        ("không phải Toán, là Lý", "clarify", None),
        ("câu này khó nhỉ", "clarify", None),
        ("nói chuyện linh tinh", "clarify", None),
        ("20 câu thôi", "clarify", None),
        ("mở lịch sử rồi quay về trang đầu", "unsupported", None),
    ],
)
def test_curated_unseen_vietnamese_safety_set(
    teacher_text: str, expected_kind: str, expected_capability: str | None
) -> None:
    result = __import__("asyncio").run(AgentInterpreter().interpret(request(teacher_text)))
    decision = result.decisions[0]
    assert decision.kind == expected_kind
    assert decision.capability_id == expected_capability
