import asyncio
import json
import subprocess
import sys

import pytest

from exam_baseline.config import Settings
from exam_baseline.core.contracts import Completion
from exam_baseline.thpt import cli
from exam_baseline.thpt.agents import ComposerAgent
from exam_baseline.thpt.orchestrator import Orchestrator, compare_answers
from exam_baseline.thpt.planner import plan_request_from_prompt
from exam_baseline.thpt.rag import (
    RagHandoffError,
    bind_retrieval,
    default_request,
    retrieval_matrix,
    retrieve_request,
)
from rag_workflow import retrieve_exam_context
from tests.paths import ROOT
from tests.thpt.test_generation import Scripted, question

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
        name = model = "offline-contract-fixture"
        parameters = {}

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
    assert len(replay["solver"].calls) == 3
    for solver_call in replay["solver"].calls:
        assert set(solver_call) == {"questions", "drawings", "output_schema"}
        assert all(
            set(q) == {"id", "stem", "choices", "statements"} for q in solver_call["questions"]
        )
    [reviewer_call] = replay["reviewer"].calls
    assert "rag_evidence" not in reviewer_call["matrix"]
    assert (output / "de_thi.tex").is_file()

    retrieval = retrieve_exam_context(retrieval_matrix(default_request()), ref=CORPUS)
    compact = bind_retrieval(default_request(), retrieval).rag_evidence
    assert sum(len(item.text) for item in compact.values()) < (
        sum(len(item["text"]) for item in retrieval.mas_intake_rag) / 2
    )
    picked = set()
    for context in retrieval.question_contexts:
        evidence_text = compact[context["question_id"]].text
        eligible = {pattern["pattern_id"] for pattern in context["construction_patterns"]}
        if not eligible:
            eligible = {observation["ref"] for observation in context["construction_observations"]}
            eligible |= {example["example_id"] for example in context["examples"]}
        [line] = [line for line in evidence_text.splitlines() if line.startswith("- Dạng [")]
        shape = line.removeprefix("- Dạng [").split("]: ", 1)[0]
        assert shape in eligible
        assert shape not in picked or eligible <= picked
        assert evidence_text.count("- Lỗi thường gặp:") <= 1
        picked.add(shape)
    variants = [
        bind_retrieval(default_request(), retrieval, variant_key=name).rag_evidence
        for name in ("first", "second", "first")
    ]
    assert variants[0] != variants[1]
    assert variants[0] == variants[2]
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


def test_default_curriculum_linking_avoids_cross_topic_drift(monkeypatch):
    if subprocess.run(["git", "cat-file", "-e", CORPUS], cwd=ROOT, capture_output=True).returncode:
        pytest.skip("Fetch origin/staging/rag to run the corpus integration test")
    monkeypatch.chdir(ROOT)
    resolved = retrieve_request(default_request(), corpus_ref=CORPUS)
    ev = resolved.rag_evidence
    assert "toan-11-c8-b30" not in ev["P1-10"].curriculum_unit_ids
    assert any(u.startswith("toan-11-c6-") for u in ev["P1-10"].curriculum_unit_ids)
    assert "toan-11-c8-b30" not in ev["P1-11"].curriculum_unit_ids
    assert any(u.startswith("toan-11-c2-") for u in ev["P1-11"].curriculum_unit_ids)
    assert "toan-12-c1-b5" not in ev["P2-4"].curriculum_unit_ids
    assert any(u.startswith(("toan-11-c8-", "toan-10-c9-")) for u in ev["P2-4"].curriculum_unit_ids)
    assert any(u.startswith("toan-12-c5-") for u in ev["P1-9"].curriculum_unit_ids)
    assert any(u.startswith("toan-12-c3-") for u in ev["P1-12"].curriculum_unit_ids)


def test_prompt_planner_grounds_slots_in_rag_and_blocks_invalid_scope(
    tmp_path, monkeypatch, capsys
):
    if subprocess.run(["git", "cat-file", "-e", CORPUS], cwd=ROOT, capture_output=True).returncode:
        pytest.skip("Fetch origin/staging/rag to run the corpus integration test")
    monkeypatch.chdir(ROOT)
    prompt = (
        "Tạo đề Toán THPT (cấu trúc 12 câu trắc nghiệm, 4 câu đúng/sai, 6 câu trả lời ngắn) "
        "tập trung vào Ứng dụng đạo hàm và Tích phân (kèm nguyên hàm). "
        "Yêu cầu: không có câu hỏi nằm ngoài 2 chuyên đề này; "
        "Phần III ưu tiên bài toán thực tiễn tối ưu và ứng dụng tích phân."
    )
    planned = plan_request_from_prompt(prompt, corpus_ref=CORPUS)
    bound = retrieve_request(planned, corpus_ref=CORPUS)
    assert len(bound.slots) == 22
    assert bound.requirements[0] == prompt
    for slot in bound.slots:
        assert slot.curriculum_unit_ids
        assert all(
            u.startswith(("toan-11-c9-", "toan-12-c1-", "toan-12-c4-"))
            for u in bound.rag_evidence[slot.id].curriculum_unit_ids
        )
    composer = ComposerAgent()
    for part in ("P1", "P2", "P3"):
        assert composer.data(bound, part, "Mixed template", None)["reference_exam"] == ""

    plan_out = tmp_path / "plan-only"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "exam-thpt",
            "--prompt",
            prompt,
            "--plan-only",
            "--rag-corpus-ref",
            CORPUS,
            "--output",
            str(plan_out),
        ],
    )
    monkeypatch.setattr(cli, "Settings", lambda: pytest.fail("plan-only called Settings"))
    assert cli.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "planned"
    assert payload["slot_count"] == 22
    assert (plan_out / "planned_request.json").is_file()
    assert (plan_out / "rag_audit.json").is_file()

    for bad_prompt, expected_code in (
        ("Tạo đề Toán có câu Số phức", "out_of_curriculum_topic"),
        ("Tạo đề về vật lý lượng tử", "topic_not_found"),
        ("Chỉ tạo đề về Hàm lượng giác", "part_not_covered"),
    ):
        with pytest.raises(RagHandoffError) as exc:
            plan_request_from_prompt(bad_prompt, corpus_ref=CORPUS)
        assert exc.value.gaps[0]["code"] == expected_code


def test_orchestrator_passes_rag_scope_to_reviewer_and_gates_solver_mismatch(tmp_path, monkeypatch):
    if subprocess.run(["git", "cat-file", "-e", CORPUS], cwd=ROOT, capture_output=True).returncode:
        pytest.skip("Fetch origin/staging/rag to run the corpus integration test")
    monkeypatch.chdir(ROOT)
    bound = retrieve_request(default_request(), corpus_ref=CORPUS)
    ids = [slot.id for slot in bound.slots]

    class MismatchSolver(Scripted):
        async def complete(self, prompt):
            data = json.loads(prompt.user)
            self.calls.append(data)
            entries = []
            requested = {q["id"] for q in data["questions"]}
            for slot in bound.slots:
                if slot.id not in requested:
                    continue
                n = int(slot.id.split("-")[1])
                if slot.id == "P1-1" and len(self.calls) == 1:
                    ans = "B"  # disagrees with Composer's A on revision 1
                elif slot.part == "P1":
                    ans = "A"
                elif slot.part == "P2":
                    ans = "a: Đúng; b: Đúng; c: Đúng; d: Đúng"
                else:
                    ans = str(n + 1)
                entries.append(
                    dict(question_id=slot.id, answer=ans, reasoning="Solved.", status="solved")
                )
            return Completion(text=json.dumps({"entries": entries}), model=self.model)

    reviewer = Scripted("reviewer", False)
    providers = {
        "composer": Scripted("composer", False),
        "illustrator": Scripted("illustrator", False),
        "solver": MismatchSolver("solver", False),
        "reviewer": reviewer,
    }
    out = tmp_path / "mismatch-gate"
    report = asyncio.run(Orchestrator(providers).run(bound, out))
    assert report["execution_status"] == "completed"
    assert report["reviewer_feedback_sent"] is True
    assert report["revision"] == 2
    assert report["solver_agreement"]["agreed_count"] == 22
    assert report["solver_agreement"]["mismatched_count"] == 0
    assert "rag_evidence" not in reviewer.calls[0]["matrix"]
    assert set(reviewer.calls[0]["rag_scope"]) == set(ids)
    review_saved = json.loads((out / "_internal/revision_1/review.json").read_text("utf-8"))
    assert review_saved["decision"] == "needs_revision"
    assert any("P1-1" in issue for issue in review_saved["issues"])

    qs = [question(s) for s in bound.slots]
    from exam_baseline.thpt.models import Solution, Solutions

    sols = Solutions(
        entries=[
            Solution(
                question_id=s.id,
                answer=(
                    "A"
                    if s.part == "P1"
                    else (
                        "a: Đúng; b: Sai; c: Đúng; d: Đúng"
                        if s.id == "P2-1"
                        else (
                            "a: Đúng; b: Đúng; c: Đúng; d: Đúng"
                            if s.part == "P2"
                            else ("99" if s.id == "P3-1" else str(int(s.id.split("-")[1]) + 1))
                        )
                    )
                ),
                reasoning="Check.",
                status="solved",
            )
            for s in bound.slots
        ]
    )
    summary = compare_answers(qs, sols)
    assert summary["agreed_count"] == 20
    assert {m["question_id"] for m in summary["mismatched"]} == {"P2-1", "P3-1"}
