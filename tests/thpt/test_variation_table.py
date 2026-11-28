import asyncio
import json

import pytest
from pydantic import ValidationError

from exam_baseline.core.contracts import Completion
from exam_baseline.pipeline.rendering.syntax import validate_drawing_code
from exam_baseline.thpt.orchestrator import Orchestrator
from exam_baseline.thpt.variation_table import VariationTable, render_variation_table
from tests.thpt.test_generation import Scripted, request

CONTINUOUS = {
    "points": [
        {"x": r"-\infty", "kind": "endpoint", "value": r"-\infty"},
        {"x": "-1", "kind": "stationary", "value": "3"},
        {"x": "1", "kind": "stationary", "value": "-1"},
        {"x": r"+\infty", "kind": "endpoint", "value": r"+\infty"},
    ],
    "signs": ["+", "-", "+"],
}
ASYMPTOTE = {
    "points": [
        {"x": r"-\infty", "kind": "endpoint", "value": "2"},
        {"x": "1", "kind": "break", "left_limit": r"+\infty", "right_limit": r"-\infty"},
        {"x": r"+\infty", "kind": "endpoint", "value": "2"},
    ],
    "signs": ["+", "+"],
}
DOMAIN_GAP = {
    "points": [
        {"x": r"-\infty", "kind": "endpoint", "value": r"+\infty"},
        {"x": "-1", "kind": "endpoint", "value": "0"},
        {"x": "1", "kind": "endpoint", "value": "0"},
        {"x": r"+\infty", "kind": "endpoint", "value": r"+\infty"},
    ],
    "signs": ["-", "gap", "+"],
}


@pytest.mark.parametrize(
    ("data", "segments", "arrows"),
    [
        (CONTINUOUS, [(0, 3)], 3),
        (ASYMPTOTE, [(0, 1), (1, 2)], 2),
        (DOMAIN_GAP, [(0, 1), (2, 3)], 2),
    ],
)
def test_variation_diagram_does_not_connect_disjoint_intervals(data, segments, arrows):
    table = VariationTable.model_validate(data)
    assert list(table.continuous_segments()) == segments
    source = render_variation_table(table)
    validate_drawing_code(source)
    assert source.count(r"\draw[->") == arrows
    assert " grid " not in source
    if data is ASYMPTOTE:
        assert "(v0p1)" in source and "(v1p1)" in source
    if data is DOMAIN_GAP:
        assert "pattern=north east lines" in source


def test_bad_variation_specs_fail_validation():
    with pytest.raises(ValidationError, match="one derivative sign"):
        VariationTable.model_validate({**CONTINUOUS, "signs": ["+"]})
    with pytest.raises(ValidationError, match="short math label"):
        VariationTable.model_validate(
            {
                **CONTINUOUS,
                "points": [
                    {**CONTINUOUS["points"][0], "value": r"\text{too much text}"},
                    *CONTINUOUS["points"][1:],
                ],
            }
        )


def test_thpt_generation_uses_structured_table_and_retains_solver_drawing(tmp_path):
    class Composer(Scripted):
        async def complete(self, prompt):
            result = await super().complete(prompt)
            data = json.loads(result.text)
            q = data["questions"][0]
            if q["id"] == "P1-1":
                q["stem"] = "Cho hàm số có bảng biến thiên dưới đây. Chọn một khoảng đồng biến."
                q["illustration_request"] = "Bảng biến thiên với các giá trị đã cho."
            return Completion(text=json.dumps(data), model=self.model)

    class Illustrator(Scripted):
        async def complete(self, prompt):
            data = json.loads(prompt.user)
            self.calls.append(data)
            assert data["variation_table_question_ids"] == ["P1-1"]
            drawing = {"question_id": "P1-1"}
            if len(self.calls) == 1:
                drawing["latex"] = r"\begin{tikzpicture}\draw (0,0) grid (3,3);\end{tikzpicture}"
            else:
                assert "contract_feedback" in data
                drawing["variation_table"] = CONTINUOUS
            return Completion(text=json.dumps({"drawings": [drawing]}), model=self.model)

    providers = {role: Scripted(role, False) for role in ("solver", "reviewer")}
    providers.update(
        composer=Composer("composer", False), illustrator=Illustrator("illustrator", False)
    )
    out = tmp_path / "exam"
    report = asyncio.run(Orchestrator(providers).run(request(), out))
    assert report["execution_status"] == "completed"
    assert len(providers["illustrator"].calls) == 2
    drawing = render_variation_table(VariationTable.model_validate(CONTINUOUS))
    assert drawing in (out / "de_thi.tex").read_text(encoding="utf-8")
    [section] = [call for call in providers["solver"].calls if call["questions"][0]["id"] == "P1-1"]
    assert section["drawings"]["drawings"] == [{"question_id": "P1-1", "latex": drawing}]
