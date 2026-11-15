import asyncio
import json
from pathlib import Path

from exam_baseline.config import Settings
from exam_baseline.core.models import BankQuestion
from exam_baseline.draft.models import Evidence
from exam_baseline.pipeline.bootstrap import ReplayProvider, replay_providers, stage_settings
from exam_baseline.pipeline.contracts import StageConfig
from exam_baseline.pipeline.orchestration.orchestrator import Orchestrator
from tests.pipeline.helpers import (
    TEXT,
    VISUAL,
    Scripted,
    payload,
    response,
)


def test_solver_receives_merged_latex_not_bank_or_composer_key(tmp_path):
    request = payload()
    request.request.context.course_materials = ["SECRET_CONTEXT"]
    request.request.question_bank.questions.append(
        BankQuestion(
            id="bank-secret",
            stem="Câu ngân hàng chưa dùng.",
            topic_id="math",
            question_type="short_answer",
            difficulty="easy",
            answer="SECRET_BANK_KEY",
        )
    )
    request.evidence = [Evidence(id="e1", text="SECRET_EVIDENCE", role="content_support")]
    providers = replay_providers(TEXT)
    solver = Scripted(lambda req, _: response("solver", req))
    providers["solver"] = solver
    result = asyncio.run(Orchestrator(providers).run(request, tmp_path / "run"))
    assert result.final_latex and "SECRET_" not in solver.requests[0].user
    packet = json.loads(solver.requests[0].user)["input"]
    assert packet["latex_source"] == Path(result.final_latex).read_text(encoding="utf-8")
    assert not solver.requests[0].images
    assert all("answer" not in q and "solution" not in q for q in packet["exam"]["questions"])


def test_illustrator_empty_spec_has_no_unrelated_questions_and_zero_drawing_schema(tmp_path):
    providers = replay_providers(TEXT)

    def draw(req, _):
        data = json.loads(req.user)["input"]
        assert data["visual_specs"] == data["questions"] == []
        schema = req.output_schema["properties"]["drawings"]
        assert schema["minItems"] == schema["maxItems"] == 0
        return json.dumps({"drawings": []})

    providers["illustrator"] = Scripted(draw)
    result = asyncio.run(Orchestrator(providers).run(payload(), tmp_path / "run"))
    assert result.final_latex and len(result.calls) == 4


def test_illustrator_is_separate_agent_produces_editable_native_code(tmp_path):
    providers = replay_providers(VISUAL)
    for provider in providers.values():
        provider.supports_images = False
    result = asyncio.run(Orchestrator(providers).run(payload(VISUAL), tmp_path / "run"))
    assert result.final_latex and len(result.calls) == 4
    source = Path(result.final_latex).read_text(encoding="utf-8")
    assert r"\begin{tikzpicture}" in source and r"\addplot" in source
    assert r"\directlua" not in source and "includegraphics" not in source
    assert ".png" not in source and "local h =" not in source
    assert all(not call.image_sha256 for call in result.calls)
    assert result.inspection_scope == "text_and_latex_source"


def test_unsafe_illustrator_code_is_rejected_before_merge(tmp_path):
    providers = replay_providers(VISUAL)
    native = json.loads((VISUAL / "illustrator_01.json").read_text(encoding="utf-8"))
    native["drawings"][0]["latex"] = r"\begin{tikzpicture}\input{secret}\end{tikzpicture}"
    providers["illustrator"] = ReplayProvider([json.dumps(native)] * 2)
    result = asyncio.run(Orchestrator(providers).run(payload(VISUAL), tmp_path / "run"))
    assert not result.final_latex and result.errors[0].stage == "illustrator"
    assert [c.stage for c in result.calls] == ["composer", "illustrator", "illustrator"]


def test_illustrator_must_cover_all_figures_and_bind_spec_hash(tmp_path):
    providers = replay_providers(VISUAL)
    native = json.loads((VISUAL / "illustrator_01.json").read_text(encoding="utf-8"))
    native["drawings"][0]["spec_sha256"] = "a" * 64
    providers["illustrator"] = ReplayProvider([json.dumps(native)] * 2)
    result = asyncio.run(Orchestrator(providers).run(payload(VISUAL), tmp_path / "run"))
    assert not result.final_latex and result.errors[0].code == "stage_contract"


def test_reviewer_cannot_approve_stale_solution_book(tmp_path):
    providers = replay_providers(TEXT)

    def stale(req, _):
        data = json.loads(response("reviewer", req))
        data["solution_sha256"] = "a" * 64
        return json.dumps(data)

    providers["reviewer"] = Scripted(stale)
    result = asyncio.run(Orchestrator(providers).run(payload(), tmp_path / "run"))
    assert not result.final_latex and len(result.calls) == 4


def test_agents_return_content_while_code_binds_identity_and_hashes(tmp_path):
    providers = replay_providers(TEXT)
    fields = {"exam_id", "draft_id", "revision", "artifact_sha256", "solution_sha256"}
    providers["illustrator"] = Scripted(lambda req, _: json.dumps({"drawings": []}))

    def content(role, req):
        assert not (fields & req.output_schema["properties"].keys())
        body = json.loads(response(role, req))
        return json.dumps({k: v for k, v in body.items() if k not in fields})

    providers["solver"] = Scripted(lambda req, _: content("solver", req))
    providers["reviewer"] = Scripted(lambda req, _: content("reviewer", req))
    result = asyncio.run(Orchestrator(providers).run(payload(), tmp_path / "run"))
    assert result.final_latex and len(result.calls) == 4
    assert result.solutions.artifact_sha256 == result.review.artifact_sha256
    assert result.solutions.revision == result.review.revision == 1


def test_illustrator_spec_hash_is_bound_without_model_copying_it(tmp_path):
    providers = replay_providers(VISUAL)
    body = json.loads((VISUAL / "illustrator_01.json").read_text(encoding="utf-8"))
    for name in ("exam_id", "draft_id", "revision"):
        body.pop(name)
    body["drawings"][0].pop("spec_sha256")
    providers["illustrator"] = Scripted(lambda req, _: json.dumps(body))
    result = asyncio.run(Orchestrator(providers).run(payload(VISUAL), tmp_path / "run"))
    assert result.final_latex and len(result.calls) == 4


def test_role_configuration_supports_an_independent_illustrator_model():
    base = Settings(
        _env_file=None, provider="chat_completions", model="composer", api_key="test-key"
    )
    native = stage_settings(base, StageConfig(model="illustrator"))
    assert native.model == "illustrator" and base.model == "composer"
