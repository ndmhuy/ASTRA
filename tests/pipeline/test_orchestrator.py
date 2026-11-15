import asyncio
import copy
import json
from pathlib import Path

import pytest

from exam_baseline.core.contracts import ProviderError
from exam_baseline.pipeline.bootstrap import ReplayProvider, replay_providers
from exam_baseline.pipeline.contracts import PipelineRequest
from exam_baseline.pipeline.orchestration.orchestrator import Orchestrator
from tests.pipeline.helpers import (
    TEXT,
    Scripted,
    issue,
    payload,
    repeated_providers,
    response,
)


def test_four_agents_merge_native_latex_then_handoff(tmp_path):
    result = asyncio.run(Orchestrator(replay_providers(TEXT)).run(payload(), tmp_path / "run"))
    assert result.execution_status == "completed"
    assert result.quality_decision == "pending_human_review" and result.human_review_required
    assert result.machine_approved and result.review_covers_final_revision
    assert [c.stage for c in result.calls] == ["composer", "illustrator", "solver", "reviewer"]
    assert result.deterministic_passed and not result.reviewer_feedback_sent
    output = Path(result.final_latex)
    assert sorted(p.name for p in output.parent.iterdir()) == ["_internal", "de_thi.tex"]
    text = output.read_text(encoding="utf-8")
    assert "Câu 4." in text
    for q in json.loads((TEXT / "composer_01.json").read_text(encoding="utf-8"))["exam"][
        "questions"
    ]:
        assert q["solution"] not in text
    assert (output.parent / "_internal/human_review.md").is_file()


def test_composer_count_feedback_contains_expected_actual_and_previous_output(tmp_path):
    providers = replay_providers(TEXT)
    good = json.loads((TEXT / "composer_01.json").read_text(encoding="utf-8"))

    def compose(req, count):
        body = copy.deepcopy(good)
        if count == 1:
            body["exam"]["questions"][0].update(question_type="short_answer", choices={})
        else:
            feedback = json.loads(req.user)["repair_feedback"]
            error = next(
                e for e in feedback["contract_errors"] if e["code"] == "type_count:multiple_choice"
            )
            assert "expected 2, received 1" in error["message"]
            assert feedback["previous_output"]["exam"]["questions"][0]["id"] == "q1"
        return json.dumps(body, ensure_ascii=False)

    providers["composer"] = Scripted(compose)
    result = asyncio.run(Orchestrator(providers).run(payload(), tmp_path / "run"))
    assert result.final_latex and not result.reviewer_feedback_sent
    assert len(result.calls) == 5


@pytest.mark.parametrize(
    "decision,target",
    [("needs_revision", "solver"), ("rejected", "composer"), ("inconclusive", "illustrator")],
)
def test_reviewer_feedback_goes_to_composer_once_then_stops(tmp_path, decision, target):
    providers = repeated_providers()
    original = (TEXT / "composer_01.json").read_text(encoding="utf-8")
    composer = Scripted(lambda req, _: original)
    reviewer = Scripted(
        lambda req, _: response("reviewer", req, decision=decision, issues=[issue(target)])
    )
    providers.update(composer=composer, reviewer=reviewer)
    result = asyncio.run(Orchestrator(providers).run(payload(), tmp_path / "run"))
    assert result.final_latex and result.execution_status == "completed"
    assert result.reviewer_feedback_sent and result.repairs == 1 and result.revision == 2
    assert result.quality_decision == "pending_human_review" and result.human_review_required
    assert not result.machine_approved and not result.review_covers_final_revision
    assert result.review.revision == 1 and result.solutions.revision == 2
    assert len(reviewer.requests) == 1 and len(composer.requests) == 2
    assert [c.stage for c in result.calls] == [
        "composer",
        "illustrator",
        "solver",
        "reviewer",
        "composer",
        "illustrator",
        "solver",
    ]
    feedback = json.loads(composer.requests[1].user)["repair_feedback"]
    assert feedback["review"]["issues"][0]["target"] == target
    assert sum(e.status == "repair" and "feedback" in e.detail for e in result.events) == 1


def test_callback_composer_schema_failure_is_not_retried(tmp_path):
    providers = repeated_providers()
    valid = (TEXT / "composer_01.json").read_text(encoding="utf-8")
    composer = Scripted(lambda req, count: valid if count == 1 else "not JSON")
    providers["composer"] = composer
    providers["reviewer"] = Scripted(
        lambda req, _: response("reviewer", req, decision="needs_revision", issues=[issue()])
    )
    result = asyncio.run(Orchestrator(providers).run(payload(), tmp_path / "run"))
    assert not result.final_latex and result.reviewer_feedback_sent
    assert len(composer.requests) == 2 and result.calls[-1].stage == "composer"


def test_minor_format_issue_can_request_the_single_composer_feedback(tmp_path):
    providers = repeated_providers()
    minor = {**issue("formatter"), "severity": "minor"}
    providers["reviewer"] = Scripted(
        lambda req, _: response("reviewer", req, decision="needs_revision", issues=[minor])
    )
    result = asyncio.run(Orchestrator(providers).run(payload(), tmp_path / "run"))
    assert result.final_latex and result.reviewer_feedback_sent
    assert result.repairs == 1 and result.revision == 2
    assert sum(c.stage == "reviewer" for c in result.calls) == 1


def test_broken_reviewer_schema_gets_no_second_reviewer_call(tmp_path):
    providers = replay_providers(TEXT)
    reviewer = Scripted(lambda req, _: "not JSON")
    providers["reviewer"] = reviewer
    result = asyncio.run(Orchestrator(providers).run(payload(), tmp_path / "run"))
    assert not result.final_latex and result.errors[0].stage == "reviewer"
    assert len(reviewer.requests) == 1


def test_cannot_configure_a_second_quality_feedback_cycle():
    from pydantic import ValidationError

    for limit in (0, 2, 5):
        data = payload().model_dump()
        data["workflow"]["max_repair_rounds"] = limit
        with pytest.raises(ValidationError):
            PipelineRequest.model_validate(data)


def test_initial_composer_latex_error_is_corrected_before_other_agents(tmp_path):
    providers = replay_providers(TEXT)
    original = json.loads((TEXT / "composer_01.json").read_text(encoding="utf-8"))

    def compose(req, count):
        data = copy.deepcopy(original)
        if count == 1:
            data["exam"]["questions"][0]["stem"] = "Tính $3+6."
        return json.dumps(data, ensure_ascii=False)

    providers["composer"] = Scripted(compose)
    result = asyncio.run(Orchestrator(providers).run(payload(), tmp_path / "run"))
    assert result.final_latex and not result.reviewer_feedback_sent
    assert [c.stage for c in result.calls][:3] == ["composer", "composer", "illustrator"]


def test_fenced_json_normalization_does_not_add_agent_call(tmp_path):
    providers = replay_providers(TEXT)
    text = (TEXT / "composer_01.json").read_text(encoding="utf-8")
    providers["composer"] = Scripted(lambda req, _: "```json\n" + text + "\n```")
    result = asyncio.run(Orchestrator(providers).run(payload(), tmp_path / "run"))
    assert result.final_latex and len(result.calls) == 4
    assert result.calls[0].normalized_json_fence


def test_call_budget_stops_before_reviewer(tmp_path):
    request = payload()
    request.workflow.max_provider_calls = 3
    result = asyncio.run(Orchestrator(replay_providers(TEXT)).run(request, tmp_path / "run"))
    assert not result.final_latex and len(result.calls) == 3
    assert result.errors[0].code == "call_budget_exceeded"
    assert result.errors[0].stage == "reviewer"


def test_token_budget_retains_failed_call_usage_and_cost(tmp_path):
    request = payload()
    request.workflow.max_total_tokens = 29
    request.workflow.composer.input_price_per_million = 1
    request.workflow.composer.output_price_per_million = 2
    providers = replay_providers(TEXT)
    providers["composer"] = Scripted(
        lambda req, _: (TEXT / "composer_01.json").read_text(encoding="utf-8")
    )
    result = asyncio.run(Orchestrator(providers).run(request, tmp_path / "run"))
    assert not result.final_latex and result.errors[0].code == "token_budget_exceeded"
    assert result.calls[0].usage.input_tokens == 10
    assert result.calls[0].known_cost_usd == pytest.approx(0.00005)


def test_finalizer_detects_source_tampering(tmp_path):
    providers = replay_providers(TEXT)

    def tamper(req, _):
        (tmp_path / "run/_internal/drafts/r1/merged.tex").write_text("changed", encoding="utf-8")
        return response("reviewer", req)

    providers["reviewer"] = Scripted(tamper)
    result = asyncio.run(Orchestrator(providers).run(payload(), tmp_path / "run"))
    assert not result.final_latex and result.errors[0].code == "artifact_error"


def test_compile_failure_does_not_publish_uncompiled_file(tmp_path, monkeypatch):
    def broken(path):
        raise ValueError("compiler_not_installed")

    monkeypatch.setattr("exam_baseline.pipeline.orchestration.artifacts.compile_document", broken)
    result = asyncio.run(
        Orchestrator(replay_providers(TEXT)).run(payload(), tmp_path / "run", compile_latex=True)
    )
    assert not result.final_latex and result.errors


def test_timeout_does_not_trigger_retry(tmp_path):
    class Slow(Scripted):
        async def complete(self, request):
            await asyncio.sleep(0.2)

    providers = replay_providers(TEXT)
    providers["solver"] = Slow(None)
    request = payload()
    request.workflow.stage_timeout_seconds = 0.01
    result = asyncio.run(Orchestrator(providers).run(request, tmp_path / "run"))
    assert len(result.calls) == 3 and result.errors[0].code == "stage_timeout"


def test_composer_http_status_reaches_report_and_does_not_retry(tmp_path):
    class Unavailable(ReplayProvider):
        async def complete(self, request):
            raise ProviderError(
                "provider_unavailable",
                "HTTP 503: Provider temporarily unavailable.",
                http_status=503,
            )

    providers = replay_providers(TEXT)
    providers["composer"] = Unavailable([])
    result = asyncio.run(Orchestrator(providers).run(payload(), tmp_path / "run"))
    assert len(result.calls) == 1 and result.calls[0].http_status == 503
    assert "HTTP 503" in result.errors[0].message
    assert not result.reviewer_feedback_sent


def test_input_rejected_before_any_call(tmp_path):
    request = payload()
    request.latex_template = r"\begin{document}%% ASTRA_BODY %%\input{secret}\end{document}"
    with pytest.raises(ValueError, match="unsupported_command"):
        asyncio.run(Orchestrator(replay_providers(TEXT)).run(request, tmp_path / "run"))
    with pytest.raises(ValueError, match="already exists"):
        asyncio.run(Orchestrator(replay_providers(TEXT)).run(payload(), tmp_path))
