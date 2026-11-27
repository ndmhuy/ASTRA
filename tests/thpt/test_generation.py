import asyncio
import json
from hashlib import sha256

import pytest
from pydantic import ValidationError

from exam_baseline.core.contracts import Completion, ProviderError
from exam_baseline.thpt.fonts import apply_font_profile
from exam_baseline.thpt.models import Illustrations, Question, Request
from exam_baseline.thpt.orchestrator import Orchestrator
from exam_baseline.thpt.rendering import render, student_view
from exam_baseline.thpt.template import TEMPLATE_SHA256, assemble, original, spans
from tests.paths import ROOT


def request():
    return Request.model_validate_json((ROOT / "examples/thpt/request.json").read_bytes())


def question(slot):
    n = int(slot.id.split("-")[1])
    data = dict(id=slot.id, stem=f"Tính ${n}+1$ ({slot.id}).", solution=f"Cộng được ${n + 1}$.")
    if slot.part == "P1":
        data.update(
            choices=dict(A=str(n + 1), B=str(n + 2), C=str(n + 3), D=str(n + 4)), answer="A"
        )
    elif slot.part == "P2":
        data.update(
            statements=[
                dict(text=f"${n}+{i}={n + i}$", answer=True, solution="Cộng trực tiếp.")
                for i in range(1, 5)
            ]
        )
    else:
        data["stem"] += " Ghi kết quả chính xác, không làm tròn."
        data["answer"] = str(n + 1)
    return Question.model_validate(data)


def test_template_frame_is_byte_identical():
    raw = original()
    assert sha256(raw).hexdigest() == TEMPLATE_SHA256
    parts = {"P1": "ONE", "P2": "TWO", "P3": "THREE"}
    generated = assemble(parts)
    cursor = 0
    for part, (start, end) in zip(parts, spans(raw), strict=True):
        prefix = raw[cursor:start]
        assert generated.startswith(prefix + parts[part].encode())
        generated = generated[len(prefix) + len(parts[part]) :]
        cursor = end
    assert generated == raw[cursor:]


def test_changed_template_hash_is_rejected(monkeypatch):
    monkeypatch.setattr("exam_baseline.thpt.template.TEMPLATE_SHA256", "0" * 64)
    with pytest.raises(ValueError, match="original"):
        original()


def test_generated_content_cannot_inject_template_commands():
    questions = [question(s) for s in request().slots]
    questions[0].stem = r"$\usepackage{fontspec}$"
    with pytest.raises(ValueError):
        render(questions, Illustrations())


def test_matrix_rejects_wrong_part_count_and_missing_statement_levels():
    data = request().model_dump()
    data["slots"][0]["id"] = "P1-2"
    with pytest.raises(ValidationError):
        Request.model_validate(data)
    data = request().model_dump()
    data["slots"][12]["statement_levels"] = []
    with pytest.raises(ValidationError):
        Request.model_validate(data)


def test_private_answers_never_enter_student_view():
    questions = [question(s) for s in request().slots]
    serialized = json.dumps(student_view(questions))
    assert '"answer"' not in serialized and '"solution"' not in serialized
    source = render(questions, Illustrations()).decode()
    assert "Cộng trực tiếp" not in source
    assert source.count(r"\textbf{Câu ") == 22
    assert source.count(r"\documentclass") == 1
    assert r"\usepackage{fontspec}" in source
    assert r"\usepackage[T5]{fontenc}" not in source


def test_rejects_wrong_question_shapes_and_drawing_bindings():
    data = question(request().slots[0]).model_dump()
    data["choices"].pop("D")
    with pytest.raises(ValidationError):
        Question.model_validate(data)
    questions = [question(s) for s in request().slots]
    questions[0].illustration_request = "A graph"
    with pytest.raises(ValueError, match="exactly"):
        render(questions, Illustrations())


class Scripted:
    name = model = "offline-contract-fixture"
    parameters = {}

    def __init__(self, role, correction):
        self.role = role
        self.correction = correction
        self.calls = []

    async def complete(self, prompt):
        data = json.loads(prompt.user)
        self.calls.append(data)
        ids = [s.id for s in request().slots]
        if self.role == "composer":
            result = dict(
                questions=[
                    question(s).model_dump() for s in request().slots if s.part == data["part"]
                ]
            )
        elif self.role == "illustrator":
            result = dict(drawings=[])
        elif self.role == "solver":
            assert '"solution"' not in prompt.user and '"answer":' not in json.dumps(
                data["questions"]
            )
            result = dict(
                entries=[
                    dict(
                        question_id=q["id"], answer="A", reasoning="Test fixture.", status="solved"
                    )
                    for q in data["questions"]
                ]
            )
        else:
            result = dict(
                checked_ids=ids,
                decision="needs_revision" if self.correction else "approved",
                issues=["Raise cognitive demand."] if self.correction else [],
            )
        return Completion(text=json.dumps(result), model=self.model)


@pytest.mark.parametrize("correction", [False, True])
def test_end_to_end_review_once(tmp_path, correction):
    providers = {
        r: Scripted(r, correction) for r in ("composer", "illustrator", "solver", "reviewer")
    }
    out = tmp_path / "exam"
    result = asyncio.run(Orchestrator(providers).run(request(), out))
    assert result["execution_status"] == "completed"
    assert result["human_review_required"] is True
    assert result["reviewer_feedback_sent"] is correction
    assert len(providers["reviewer"].calls) == 1
    assert len(providers["composer"].calls) == (6 if correction else 3)
    assert len(providers["solver"].calls) == (2 if correction else 1)
    header = original()[: spans(original())[0][0]]
    assert (out / "de_thi.tex").read_bytes().startswith(apply_font_profile(header))
    assert (out / "dap_an_va_loi_giai.json").exists()
    with pytest.raises(FileExistsError):
        asyncio.run(Orchestrator(providers).run(request(), out))


def test_resume_after_correction_failure_reuses_review_and_prior_sections(tmp_path):
    class InterruptComposer(Scripted):
        interrupted = True

        async def complete(self, prompt):
            data = json.loads(prompt.user)
            if self.interrupted and data.get("feedback") and data["part"] == "P2":
                raise ProviderError(
                    "provider_bad_request", "Simulated interruption", http_status=400
                )
            return await super().complete(prompt)

    providers = {r: Scripted(r, True) for r in ("illustrator", "solver", "reviewer")}
    composer = InterruptComposer("composer", True)
    providers["composer"] = composer
    payload = request().model_copy(update={"composer_concurrency": 1})
    out = tmp_path / "exam"
    with pytest.raises(ProviderError):
        asyncio.run(Orchestrator(providers).run(payload, out))
    assert len(providers["reviewer"].calls) == 1
    assert len(composer.calls) == 4
    composer.interrupted = False
    result = asyncio.run(Orchestrator(providers).run(payload, out, resume=True))
    assert result["execution_status"] == "completed"
    assert len(providers["reviewer"].calls) == 1
    assert len(composer.calls) == 6
    changed = request().model_copy(deep=True)
    changed.requirements.append("Different matrix requirements")
    with pytest.raises(ValueError, match="same input"):
        asyncio.run(Orchestrator(providers).run(changed, out, resume=True))
