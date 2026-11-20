import json
import subprocess
import sys

import pytest

from exam_baseline.config import Settings
from exam_baseline.thpt import cli
from exam_baseline.thpt.agents import ComposerAgent
from exam_baseline.thpt.rag import (
    RagHandoffError,
    default_request,
    retrieval_matrix,
    retrieve_request,
)
from rag_workflow import retrieve_exam_context
from tests.paths import ROOT
from tests.thpt.test_generation import Scripted

CORPUS = "8b8fb7b09182b3d9d1eee0b95818027f52ab004d"


def test_missing_corpus_stops_before_opening_a_provider(tmp_path, monkeypatch, capsys):
    output = tmp_path / "exam"
    monkeypatch.setattr(
        sys,
        "argv",
        ["exam-thpt", "--rag", "--rag-corpus-ref", "missing-rag-commit", "--output", str(output)],
    )
    monkeypatch.setattr(cli, "Settings", lambda: pytest.fail("retrieval gap reached the provider"))
    assert cli.main() == 1
    failure = json.loads(capsys.readouterr().out)
    assert failure["error"] == "retrieval_gap"
    assert failure["gaps"][0]["code"] == "corpus_unavailable"
    assert not output.exists()


def test_real_rag_through_thpt_cli_and_resume(tmp_path, monkeypatch, capsys):
    if subprocess.run(["git", "cat-file", "-e", CORPUS], cwd=ROOT, capture_output=True).returncode:
        pytest.skip("Fetch origin/staging/rag to run the corpus integration test")
    monkeypatch.chdir(ROOT)
    output = tmp_path / "exam"
    argv = ["exam-thpt", "--rag", "--rag-corpus-ref", CORPUS, "--output", str(output)]
    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.setattr(
        cli,
        "Settings",
        lambda: Settings.for_offline().model_copy(update={"provider": "chat_completions"}),
    )
    replay = {
        role: Scripted(role, False) for role in ("composer", "illustrator", "solver", "reviewer")
    }

    class ReplayProvider:
        async def complete(self, prompt):
            data = json.loads(prompt.user)
            if "part" in data:
                return await replay["composer"].complete(prompt)
            if "requests" in data:
                return await replay["illustrator"].complete(prompt)
            if "matrix" in data:
                return await replay["reviewer"].complete(prompt)
            return await replay["solver"].complete(prompt)

    monkeypatch.setattr(cli, "ChatCompletionsProvider", lambda *_: ReplayProvider())
    assert cli.main() == 0
    result = json.loads(capsys.readouterr().out)
    assert result["quality_decision"] == "pending_human_review"
    evidence = result["rag_evidence"]
    assert len(evidence) == 22
    assert all(p["source_version"] == CORPUS and p["source_ids"] for p in evidence.values())
    assert {i for i, p in evidence.items() if p["warnings"]} == {"P2-1", "P2-2"}
    assert len(replay["composer"].calls) == 3
    for call in replay["composer"].calls:
        assert [
            text.split("question_id=", 1)[1].split(" ", 1)[0] for text in call["reference_material"]
        ] == [slot["id"] for slot in call["slots"]]
    [solver_call] = replay["solver"].calls
    assert set(solver_call) == {"questions", "drawings", "output_schema"}
    assert all(set(q) == {"id", "stem", "choices", "statements"} for q in solver_call["questions"])
    [reviewer_call] = replay["reviewer"].calls
    assert "rag_evidence" not in reviewer_call["matrix"]
    assert (output / "de_thi.tex").is_file()

    retrieval = retrieve_exam_context(retrieval_matrix(default_request()), ref=CORPUS)
    p2_4 = next(c for c in retrieval.question_contexts if c["question_id"] == "P2-4")
    nb = p2_4["p2_statement_coverage"]["a"]
    assert nb["covered"]
    assert set(nb["matching_example_ids"]) <= {
        example["example_id"] for example in p2_4["examples"]
    }
    assert nb["matching_example_ids"] or nb["matching_observation_refs"]

    with monkeypatch.context() as resume:
        resume.setattr(sys, "argv", [*argv, "--resume"])
        resume.setattr(cli, "retrieve_request", lambda *a, **kw: pytest.fail("resume queried RAG"))
        assert cli.main() == 0
    assert json.loads(capsys.readouterr().out)["rag_evidence"] == evidence
    assert len(replay["composer"].calls) == 3

    unsupported = default_request()
    unsupported.slots[0].topic = unsupported.slots[0].objective = "zzqxjvv"
    request_file = tmp_path / "unsupported.json"
    request_file.write_text(unsupported.model_dump_json(), encoding="utf-8")
    blocked_output = tmp_path / "blocked"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            *argv[:-2],
            "--request",
            str(request_file),
            "--output",
            str(blocked_output),
        ],
    )
    monkeypatch.setattr(
        cli, "Settings", lambda: pytest.fail("unsupported slot reached the provider")
    )
    assert cli.main() == 1
    [gap] = json.loads(capsys.readouterr().out)["gaps"]
    assert (gap["question_id"], gap["code"]) == ("P1-1", "topic_not_found")
    assert not blocked_output.exists()


def test_rag_curriculum_scope_is_applied_to_the_passage(monkeypatch):
    if subprocess.run(["git", "cat-file", "-e", CORPUS], cwd=ROOT, capture_output=True).returncode:
        pytest.skip("Fetch origin/staging/rag to run the corpus integration test")
    monkeypatch.chdir(ROOT)
    request = default_request()
    slot = request.slots[2]
    assert slot.id == "P1-3"
    slot.curriculum_unit_ids = ["toan-12-c1-b1"]
    resolved = retrieve_request(request, corpus_ref=CORPUS)
    evidence = resolved.rag_evidence[slot.id]
    assert evidence.curriculum_unit_ids == ["toan-12-c1-b1"]
    assert "[toan-12-c1-b1]" in evidence.text
    assert "toan-11-c8-b30" not in evidence.text
    composer = ComposerAgent()
    assert (
        composer.data(resolved, "P1", "Mixed-topic template questions", None)["reference_exam"]
        == ""
    )
    assert composer.data(resolved, "P2", "Mixed-topic template questions", None)["reference_exam"]

    slot.curriculum_unit_ids = ["not-in-verified-corpus"]
    with pytest.raises(RagHandoffError) as error:
        retrieve_request(request, corpus_ref=CORPUS)
    [gap] = error.value.gaps
    assert (gap["question_id"], gap["code"]) == ("P1-3", "curriculum_unit_not_found")
