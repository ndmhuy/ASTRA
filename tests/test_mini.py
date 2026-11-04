import asyncio
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from exam_baseline.contracts import Completion
from exam_baseline.mini import (
    ComposerOutput, DraftQuestion, Evidence, MiniRequest, SourceRef, StageResult,
    VisualSpec, create_draft, render_visual, validate_output,
)
from exam_baseline.samples import sample_request


class ReplayProvider:
    name = "replay"
    model = "fixture"
    parameters = {}

    def __init__(self, text):
        self.text = text
        self.calls = 0

    async def complete(self, request):
        self.calls += 1
        return Completion(text=self.text, model=self.model)


def baseline_output():
    path = Path(__file__).parents[1] / "src/exam_baseline/fixtures/mock_exam.json"
    exam = json.loads(path.read_text(encoding="utf-8"))
    return ComposerOutput.model_validate({
        "exam": exam,
        "questions": [{"id": q["id"]} for q in exam["questions"]],
    })


def test_text_only_handoff_keeps_answers_private(tmp_path):
    output = baseline_output()
    request = MiniRequest(request=sample_request())
    assert not validate_output(output, request)
    provider = ReplayProvider(output.model_dump_json())
    draft = asyncio.run(create_draft(request, provider, tmp_path / "handoff"))
    assert draft.composer.status == "succeeded"
    assert draft.illustrator.status == "skipped"
    assert provider.calls == 1
    student = (tmp_path / "handoff/student_view.json").read_text(encoding="utf-8")
    assert '"answer":' not in student or '"answer": null' in student
    assert all(q.answer is None and q.solution is None for q in draft.exam.questions)
    assert json.loads((tmp_path / "handoff/teacher_private.json").read_text())["q1"]["answer"] == "B"


def test_structural_and_evidence_failures():
    output = baseline_output()
    request = MiniRequest(request=sample_request(), evidence=[Evidence(id="e1", text="source", role="form_example")], require_evidence=True)
    assert any(e.code == "missing_evidence" for e in validate_output(output, request))
    output.questions[0].source_refs = [SourceRef(evidence_id="invented", role="content_support")]
    assert any(e.code == "invalid_evidence_ref" for e in validate_output(output, request))
    output.exam.questions[1].id = "q1"
    assert any(e.code == "unique_question_ids" for e in validate_output(output, request))


def test_matrix_count_and_points_failures():
    output = baseline_output()
    request = MiniRequest(request=sample_request())
    output.exam.questions.pop()
    codes = {e.code for e in validate_output(output, request)}
    assert "question_count" in codes and "total_points" in codes


def test_required_visual_and_render_binding(tmp_path):
    output = baseline_output()
    request = MiniRequest(request=sample_request(), required_visual_question_ids=["q4"])
    assert any(e.code == "required_visual_missing" for e in validate_output(output, request))
    spec = VisualSpec(visual_id="v1", question_id="q4", revision=1, required=True,
                      purpose="Graph of f(x)=3x+2", kind="line_graph",
                      x_domain=(0, 5), y_domain=(0, 20),
                      points=[(0, 2), (1, 5), (3, 11), (5, 17)],
                      x_label="x", y_label="f(x)")
    output.visuals = [spec]
    output.questions[3].figure_refs = ["v1"]
    assert not validate_output(output, request)
    artifact = render_visual(spec, tmp_path / "v1.png")
    assert artifact.question_id == "q4" and artifact.width_px == 900
    spec.revision = 2
    assert any(e.code == "visual_binding" for e in validate_output(output, request))


def test_schema_and_provider_failure(tmp_path):
    with pytest.raises(ValidationError):
        VisualSpec(visual_id="v", question_id="q1", revision=1, purpose="p",
                   kind="bar_chart", labels=["A"], values=[])
    request = MiniRequest(request=sample_request())
    result = asyncio.run(create_draft(request, ReplayProvider("not json"), tmp_path / "bad"))
    assert isinstance(result, StageResult)
    assert result.status == "failed" and result.errors[0].code == "invalid_composer_json"


def test_no_evidence_means_zero_calls(tmp_path):
    provider = ReplayProvider("{}")
    result = asyncio.run(create_draft(MiniRequest(request=sample_request(), require_evidence=True),
                                      provider, tmp_path / "none"))
    assert result.status == "failed" and provider.calls == 0
