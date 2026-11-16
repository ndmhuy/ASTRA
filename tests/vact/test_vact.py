import asyncio
import json
from hashlib import sha256

import pytest
from pydantic import ValidationError

from exam_baseline.core.contracts import Completion
from exam_baseline.vact import template
from exam_baseline.vact.agents import ComposerAgent
from exam_baseline.vact.models import Request, Section
from exam_baseline.vact.orchestrator import Orchestrator
from exam_baseline.vact.rendering import render
from exam_baseline.vact.schema import compact_schema
from tests.paths import ROOT


def request():
    return Request.model_validate_json((ROOT / "examples/vact/request.json").read_bytes())


def section(batch):
    passages = [
        dict(
            id=g.id,
            heading=f"Fixture {g.id}",
            text=(
                "This is synthetic contract-test data, not an exam for students. "
                "Every item in this group uses the stated numbers: 1, 2, 3 and 4."
            ),
        )
        for g in batch.groups
        if g.shared
    ]
    for p in passages:
        if p["id"] == "g97_99":
            p["table"] = dict(columns=["Label", "Value"], rows=[["A", "$1$"], ["B", "$2$"]])
    questions = []
    for g in batch.groups:
        for i in range(g.start, g.end + 1):
            questions.append(
                dict(
                    id=f"q{i}",
                    stem=f"Contract fixture question {i}: compute $1+1$.",
                    choices=dict(A="$2$", B="$3$", C="$4$", D="$5$"),
                    answer="A",
                    solution="PRIVATE_COMPOSER_REASONING",
                    passage_id=g.id if g.shared else None,
                    illustration_request="Plot a line y=x." if i == 1 else None,
                )
            )
    return Section.model_validate(dict(questions=questions, passages=passages))


def test_exact_template_plan_and_frame():
    raw = template.original()
    assert sha256(raw).hexdigest() == template.TEMPLATE_SHA256
    assert [i for b in template.batches() for i in b.ids] == [f"q{i}" for i in range(1, 121)]
    assert [
        sum(len(b.ids) for b in template.batches() if b.section == s) for s in template.SECTIONS
    ] == [30, 30, 30, 12, 18]
    assert all(len(b.ids) <= 12 for b in template.batches())
    parts = {s: f"NEW_{s}" for s in template.SECTIONS}
    generated = template.assemble(parts)
    cursor = 0
    for s, (a, b) in zip(template.SECTIONS, template.spans(raw), strict=True):
        prefix = raw[cursor:a]
        assert generated.startswith(prefix + parts[s].encode())
        generated = generated[len(prefix) + len(parts[s]) :]
        cursor = b
    assert generated == raw[cursor:]


def test_matrix_and_group_bindings_reject_missing_data():
    data = request().model_dump()
    data["slots"][0]["part"] = "invalid"
    with pytest.raises(ValidationError):
        Request.model_validate(data)
    batch = next(b for b in template.batches() if b.id == "TV_21_30")
    agent = ComposerAgent()
    scope = agent.data(request(), batch.id, "reference", None)
    model = agent.contract(scope)
    output = section(batch).model_dump()
    model.model_validate(output)
    output["questions"][0]["passage_id"] = "g26_30"
    with pytest.raises(ValidationError):
        model.model_validate(output)
    output = section(batch).model_dump()
    output["passages"].pop()
    with pytest.raises(ValidationError):
        model.model_validate(output)


class Scripted:
    def __init__(self, role, correct=False):
        self.role = role
        self.correct = correct
        self.calls = []

    async def complete(self, prompt):
        data = json.loads(prompt.user)
        self.calls.append(data)
        if self.role == "composer":
            batch = next(b for b in template.batches() if b.id == data["part"])
            result = section(batch).model_dump()
        elif self.role == "illustrator":
            result = dict(
                drawings=[
                    dict(
                        question_id=r["question_id"],
                        latex=(r"\begin{tikzpicture}\draw (0,0)--(1,1);\end{tikzpicture}"),
                    )
                    for r in data["requests"]
                ]
            )
        elif self.role == "solver":
            assert "PRIVATE_COMPOSER_REASONING" not in prompt.user
            assert all("answer" not in q and "solution" not in q for q in data["questions"])
            for q in data["questions"]:
                if q["passage_id"]:
                    assert q["passage_id"] in {p["id"] for p in data["passages"]}
            result = dict(
                entries=[
                    dict(
                        question_id=i, answer="A", reasoning="Independent fixture.", status="solved"
                    )
                    for i in data["question_ids"]
                ]
            )
        else:
            assert len(data["passages"]) == 21
            assert len(data["questions"]) == 120
            result = dict(
                checked_ids=[f"q{i}" for i in range(1, 121)],
                decision="needs_revision" if self.correct else "approved",
                issues=["q1: revise this test fixture"] if self.correct else [],
            )
        return Completion(text=json.dumps(result), model="offline-vact-contract-fixture")


@pytest.mark.parametrize("correction", [False, True])
def test_full_120_question_pipeline_and_once_only_review(tmp_path, correction):
    providers = {
        r: Scripted(r, correction) for r in ("composer", "illustrator", "solver", "reviewer")
    }
    out = tmp_path / "exam"
    report = asyncio.run(Orchestrator(providers).run(request(), out))
    assert report["execution_status"] == "completed"
    assert report["human_review_required"]
    assert report["reviewer_feedback_sent"] == correction
    assert len(providers["reviewer"].calls) == 1
    assert len(providers["composer"].calls) == len(template.batches()) * (2 if correction else 1)
    source = (out / "de_thi.tex").read_text("utf-8")
    assert source.count(r"\textbf{Câu ") == 120
    assert "PRIVATE_COMPOSER_REASONING" not in source
    assert r"\begin{tabular}" in source and r"\begin{tikzpicture}" in source
    assert r"\usepackage{fontspec}" in source
    assert "3.2. SUY LUẬN KHOA HỌC" in source
    answers = json.loads((out / "dap_an_va_loi_giai.json").read_text("utf-8"))
    assert len(answers["composer"]) == 120 and len(answers["passages"]) == 21
    for call in providers["composer"].calls:
        feedback = call.get("feedback")
        if feedback:
            assert {q["id"] for q in feedback["previous_questions"]} == set(call["question_ids"])


def test_missing_requested_drawing_prevents_export():
    from exam_baseline.vact.models import Illustrations

    with pytest.raises(ValueError, match="bindings"):
        render([section(b) for b in template.batches()], Illustrations(), "unicode_times")


def test_compact_wire_schema_keeps_field_names_and_local_count_validation():
    schema = {
        "title": "Metadata",
        "type": "object",
        "properties": {
            "title": {"type": "string", "maxLength": 20},
        },
        "required": ["title"],
    }
    compact = compact_schema(schema)
    assert compact["properties"]["title"] == {"type": "string"}
    assert compact["required"] == ["title"]
    batch = next(b for b in template.batches() if b.id == "TV_21_30")
    agent = ComposerAgent()
    data = agent.data(request(), batch.id, "reference", None)
    model = agent.contract(data)
    assert "maxItems" not in agent.wire_schema(model.model_json_schema())["properties"]["questions"]
    invalid = section(batch).model_dump()
    invalid["questions"].pop()
    with pytest.raises(ValidationError):
        model.model_validate(invalid)


def test_solver_concurrency_limit_and_order(tmp_path):
    class DelayedSolver(Scripted):
        active = maximum = 0

        async def complete(self, prompt):
            self.active += 1
            self.maximum = max(self.maximum, self.active)
            try:
                await asyncio.sleep(0.002)
                return await super().complete(prompt)
            finally:
                self.active -= 1

    providers = {r: Scripted(r) for r in ("composer", "illustrator", "reviewer")}
    solver = DelayedSolver("solver")
    providers["solver"] = solver
    report = asyncio.run(Orchestrator(providers).run(request(), tmp_path / "exam"))
    assert report["execution_status"] == "completed"
    assert solver.maximum == request().solver_concurrency


def test_missing_shared_data_triggers_one_schema_correction():
    batch = next(b for b in template.batches() if b.id == "TV_21_30")
    agent = ComposerAgent()
    data = agent.data(request(), batch.id, "reference", None)
    correct = section(batch).model_dump()
    invalid = {**correct, "passages": []}

    class Repair:
        calls = 0

        async def complete(self, prompt):
            self.calls += 1
            payload = json.loads(prompt.user)
            if self.calls == 2:
                assert payload["contract_feedback"]["fields"]
            return Completion(
                text=json.dumps(invalid if self.calls == 1 else correct), model="fixture"
            )

    provider = Repair()
    result, _ = asyncio.run(agent.run(provider, data))
    assert provider.calls == 2 and len(result.passages) == 2


def test_legacy_range_prefix_is_normalized_without_changing_content():
    batch = next(b for b in template.batches() if b.id == "TO_73_84")
    agent = ComposerAgent()
    model = agent.contract(agent.data(request(), batch.id, "reference", None))
    data = section(batch).model_dump()
    texts = [p["text"] for p in data["passages"]]
    for passage in data["passages"]:
        passage["id"] = "p" + passage["id"][1:]
    for question in data["questions"]:
        question["passage_id"] = "p" + question["passage_id"][1:]
    validated = model.model_validate(data)
    assert [p.id for p in validated.passages] == [g.id for g in batch.groups]
    assert [p.text for p in validated.passages] == texts
    data["passages"][0]["id"] = "p73_75"
    with pytest.raises(ValidationError):
        model.model_validate(data)


def test_wire_schema_limits_shared_ids_to_actual_template_groups():
    batch = next(b for b in template.batches() if b.id == "TO_73_84")
    agent = ComposerAgent()
    data = agent.data(request(), batch.id, "reference", None)
    wire = agent.prepare_schema(agent.contract(data).model_json_schema(), data)
    assert wire["$defs"]["Passage"]["properties"]["id"]["enum"] == [g.id for g in batch.groups]
    assert "p1" not in wire["$defs"]["Passage"]["properties"]["id"]["enum"]


def test_shared_passage_and_table_cannot_hide_unwrapped_formulas():
    from exam_baseline.vact.models import Passage, Table

    with pytest.raises(ValidationError):
        Passage(id="g106_108", text="delta P = R P^2 / (U^2 cos^2 phi)")
    with pytest.raises(ValidationError):
        Table(columns=["Quantity", "Formula"], rows=[["growth", "r=(Nn/N0)^(1/n)-1"]])
