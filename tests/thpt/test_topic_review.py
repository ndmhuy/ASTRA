import asyncio

import pytest
from pydantic import ValidationError

from exam_baseline.thpt.models import Statement
from exam_baseline.thpt.topic_review import StatementWriter, TopicReviewer, review_topic
from tests.thpt.test_generation import question, request


@pytest.mark.parametrize("repair_passes", [True, False])
def test_rewrite_and_recheck_only_failed_address(repair_passes):
    plan = request().model_copy(
        update={"topic_review_instruction": "Tích phân", "topic_repair_limit": 1}
    )
    original = [question(slot) for slot in plan.slots]
    target = "P2-1.d"
    checked = []
    replacement = Statement(text="Tích phân bằng 4.", solution="Tính tích phân.", answer=False)

    async def call(agent, payload, revision):
        if isinstance(agent, StatementWriter):
            assert payload["target_address"] == target
            return replacement
        addresses = list(payload["units"])
        checked.append(addresses)
        return agent.contract(payload).model_validate(
            {
                "verdicts": {
                    addr: dict(
                        on_topic=addr != target or (len(checked) == 2 and repair_passes),
                        reasoning="Kiểm tra phép toán.",
                    )
                    for addr in addresses
                }
            }
        )

    run = review_topic(call, plan, original.copy(), 1, [])
    if repair_passes:
        revised = asyncio.run(run)
        assert revised[:12] == original[:12] and revised[13:] == original[13:]
        assert revised[12].stem == original[12].stem
        assert revised[12].statements == [*original[12].statements[:3], replacement]
    else:
        with pytest.raises(ValueError, match=target):
            asyncio.run(run)
    assert len(checked[0]) == len(set(checked[0])) == 34
    assert checked[1:] == [[target]]


def test_grouped_verdict_cannot_cover_individual_statements():
    contract = TopicReviewer().contract({"units": {"P2-1.a": {}, "P2-1.b": {}}})
    with pytest.raises(ValidationError, match="P2-1.b"):
        contract.model_validate(
            {"verdicts": {"P2-1.a, P2-1.b": {"reasoning": "Tính diện tích.", "on_topic": True}}}
        )


def test_topic_review_checkpoint_round_trips_address_aliases():
    reviewer = TopicReviewer()
    contract = reviewer.contract({"units": {"P2-1.a": {}, "P2-1.b": {}}})
    original = contract.model_validate(
        {
            "verdicts": {
                "P2-1.a": {"reasoning": "Đếm số cách chọn.", "on_topic": True},
                "P2-1.b": {"reasoning": "Không dùng xác suất.", "on_topic": False},
            }
        }
    )
    for by_alias in (True, False):
        restored = contract.model_validate(original.model_dump(by_alias=by_alias))
        assert reviewer.to_audit(restored) == reviewer.to_audit(original)


@pytest.mark.parametrize("off_topic_solution", ["Tính đạo hàm.", r"Tính $\int x dx$."])
def test_integral_scope_rejects_prerequisite_only_solution_even_if_model_passes_it(
    off_topic_solution,
):
    plan = request()
    for slot in plan.slots:
        slot.topic = "Tích phân"
    plan.topic_review_instruction = "hãy cho tôi bài tập tích phân"
    item = question(plan.slots[12])
    target = "P2-1.d"
    item.statements = [
        *[s.model_copy(update={"solution": r"Tính $\int_0^1 x dx$."}) for s in item.statements[:3]],
        Statement(text="Khẳng định cần kiểm lại.", solution=off_topic_solution, answer=True),
    ]
    expected = Statement(
        text=r"Quãng đường bằng $\int_0^2 v(t)dt$.",
        solution=r"Tính $\int_0^2 v(t)dt$.",
        answer=True,
    )

    async def call(agent, payload, revision):
        if isinstance(agent, StatementWriter):
            assert payload["target_address"] == target
            return expected
        return agent.contract(payload).model_validate(
            {
                "verdicts": {
                    addr: {"on_topic": True, "reasoning": "Duyệt theo ngữ cảnh chung."}
                    for addr in payload["units"]
                }
            }
        )

    history = []
    revised = asyncio.run(review_topic(call, plan, [item], 1, history))
    assert revised[0].statements == [*item.statements[:3], expected]
    assert [f["address"] for f in history[0]["findings"] if not f["on_topic"]] == [target]
