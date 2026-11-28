import asyncio
import json

import pytest

from exam_baseline.core.contracts import Completion
from exam_baseline.thpt.agents import SolverAgent
from exam_baseline.thpt.orchestrator import _parse_p2_booleans
from exam_baseline.thpt.planner import _pack_objectives
from exam_baseline.thpt.runtime import ContractError, RecordingProvider


@pytest.mark.parametrize(
    "answer",
    [
        "a: true; b: false; c: true; c: false",
        "a: true; b: false; c: true; d: false; d: true",
        "a: true; false; true; false",
    ],
)
def test_p2_invalid_labels_never_fall_back_to_position(answer):
    assert _parse_p2_booleans(answer) is None


def test_p2_accepts_exact_labels_and_bare_booleans():
    expected = [True, False, True, False]
    assert _parse_p2_booleans("d: false; b: false; a: true; c: true") == expected
    assert _parse_p2_booleans("true false true false") == expected


@pytest.mark.parametrize("repairs", [True, False])
def test_solver_coverage_uses_existing_contract_retry(tmp_path, repairs):
    class Provider:
        async def complete(self, request):
            payload = json.loads(request.user)
            repaired = repairs and "contract_feedback" in payload
            response = {
                "entries": [
                    {
                        "question_id": "P1-1" if repaired else "P1-2",
                        "answer": "A",
                        "reasoning": "Fixture.",
                        "status": "solved",
                    }
                ]
            }
            return Completion(text=json.dumps(response), model="fixture")

    calls = []
    tracer = RecordingProvider(Provider(), "solver", 1, calls, tmp_path)
    run = SolverAgent().run(tracer, {"questions": [{"id": "P1-1", "stem": "Fixture"}]})
    if repairs:
        result, _ = asyncio.run(run)
        assert result.entries[0].question_id == "P1-1"
    else:
        with pytest.raises(ContractError):
            asyncio.run(run)
    assert [call["status"] for call in calls] == [
        "invalid_contract",
        "validated" if repairs else "invalid_contract",
    ]
    assert calls[0]["request_sha256"] != calls[1]["request_sha256"]


def test_objectives_keep_distinct_operations_after_common_prefix():
    prefix = "Interpret the given values and model the scenario. " * 4
    endings = ["Identify the maximum value", "Identify the minimum value"]
    pack = {
        "construction_observations": [
            {"part": "P3", "task": prefix + ending} for ending in endings
        ],
        "patterns": [],
        "curriculum_units": [],
    }
    assert _pack_objectives(pack, "P3", "VD") == [prefix + ending for ending in endings]


def test_parallel_pause_drains_already_sent_valid_sections(tmp_path):
    from exam_baseline.core.checkpoints import GenerationPaused
    from exam_baseline.thpt.orchestrator import Orchestrator
    from tests.thpt.test_generation import Scripted, request

    async def run():
        paused = False
        started = []
        both_started = asyncio.Event()
        first_committed = asyncio.Event()

        class Composer(Scripted):
            async def complete(self, prompt):
                part = json.loads(prompt.user)["part"]
                started.append(part)
                if len(started) == 2:
                    both_started.set()
                await both_started.wait()
                if part == "P1":
                    nonlocal paused
                    paused = True
                else:
                    await first_committed.wait()
                return await super().complete(prompt)

        def admission():
            if paused:
                raise GenerationPaused

        def persist(path, data):
            from exam_baseline.core.checkpoints import atomic_json

            atomic_json(path, data)
            if path.parent.name == "checkpoints" and data.get("part") == "P1":
                first_committed.set()

        pool = {role: Scripted(role, False) for role in ("illustrator", "solver", "reviewer")}
        pool["composer"] = Composer("composer", False)
        plan = request().model_copy(update={"composer_concurrency": 2})
        with pytest.raises(GenerationPaused):
            await Orchestrator(pool, check_control=admission, checkpoint_writer=persist).run(
                plan, tmp_path / "exam"
            )
        paths = (tmp_path / "exam/_internal/checkpoints").glob("*.json")
        assert {json.loads(path.read_bytes())["part"] for path in paths} == {"P1", "P2"}
        assert started == ["P1", "P2"]

    asyncio.run(asyncio.wait_for(run(), timeout=5))
