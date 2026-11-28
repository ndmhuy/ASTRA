import asyncio
import json
from pathlib import Path

import pytest

from exam_baseline.core.contracts import Completion
from exam_baseline.thpt.agents import ComposerAgent
from exam_baseline.thpt.orchestrator import Orchestrator
from tests.thpt.test_generation import Scripted, request


def test_first_part_is_illustrated_and_solved_while_composer_is_still_working(tmp_path):
    async def run():
        first_solver_started = asyncio.Event()
        drawing = r"\begin{tikzpicture}\draw (0,0) -- (1,1);\end{tikzpicture}"

        class Composer(Scripted):
            async def complete(self, prompt):
                part = json.loads(prompt.user)["part"]
                if part == "P2":
                    await first_solver_started.wait()
                response = await super().complete(prompt)
                if part != "P1":
                    return response
                output = json.loads(response.text)
                output["questions"][0]["illustration_request"] = "Draw a line segment."
                return Completion(json.dumps(output), self.model)

        class Illustrator(Scripted):
            async def complete(self, prompt):
                [subject] = json.loads(prompt.user)["requests"]
                assert subject["question_id"] == "P1-1"
                return Completion(
                    json.dumps({"drawings": [{"question_id": "P1-1", "latex": drawing}]}),
                    self.model,
                )

        class Solver(Scripted):
            async def complete(self, prompt):
                data = json.loads(prompt.user)
                if data["questions"][0]["id"] == "P1-1":
                    assert len(data["questions"]) == 12
                    assert data["drawings"]["drawings"] == [
                        {"question_id": "P1-1", "latex": drawing}
                    ]
                    first_solver_started.set()
                return await super().complete(prompt)

        engine = Orchestrator(
            {
                "composer": Composer("composer", False),
                "illustrator": Illustrator("illustrator", False),
                "solver": Solver("solver", False),
                "reviewer": Scripted("reviewer", False),
            }
        )
        return await asyncio.wait_for(engine.run(request(), tmp_path / "exam"), timeout=5)

    assert asyncio.run(run())["execution_status"] == "completed"


@pytest.mark.parametrize("limit", [1, 2, 3])
def test_concurrent_sections_keep_order_and_separate_trace_files(tmp_path, limit):
    class OverlappingComposer(Scripted):
        active = maximum = 0

        async def complete(self, prompt):
            part = json.loads(prompt.user)["part"]
            self.active += 1
            self.maximum = max(self.maximum, self.active)
            try:
                # Deliberately finish sections out of their requested order.
                await asyncio.sleep({"P1": 0.03, "P2": 0.02, "P3": 0.01}[part])
                return await super().complete(prompt)
            finally:
                self.active -= 1

    composer = OverlappingComposer("composer", False)
    providers = {r: Scripted(r, False) for r in ("illustrator", "solver", "reviewer")}
    providers["composer"] = composer
    payload = request().model_copy(update={"composer_concurrency": limit})
    report = asyncio.run(Orchestrator(providers).run(payload, tmp_path / "exam"))
    assert composer.maximum == limit
    assert len(providers["reviewer"].calls) == 1
    traced = [c for c in report["calls"] if c["role"] == "composer"]
    paths = [c["response_file"] for c in traced]
    assert len(set(paths)) == 3
    assert all(c["status"] == "validated" for c in traced)
    assert {json.loads(Path(p).read_text("utf-8"))["questions"][0]["id"] for p in paths} == {
        "P1-1",
        "P2-1",
        "P3-1",
    }
    ids = [q["id"] for call in providers["solver"].calls for q in call["questions"]]
    assert sorted(ids) == sorted(s.id for s in payload.slots)


def test_repair_context_is_scoped_to_the_current_part():
    feedback = {
        "review": {"issues": ["Check all numerical answers"]},
        "previous_questions": [{"id": f"{p}-1"} for p in ("P1", "P2", "P3")],
    }
    data = ComposerAgent().data(request(), "P2", "reference", feedback)
    assert data["feedback"]["previous_questions"] == [{"id": "P2-1"}]
    assert data["feedback"]["review"] == feedback["review"]
    assert len(feedback["previous_questions"]) == 3
