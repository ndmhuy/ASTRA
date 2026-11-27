"""Validate the handoff with the real compiled planner and a scripted LLM callback."""

import asyncio
import json
import subprocess
import sys

import pytest

from exam_baseline.config import DEFAULT_RAG_CORPUS_REF, Settings
from exam_baseline.core.contracts import Completion
from exam_baseline.thpt.mas_input import math_request, prepare_math_plan
from exam_baseline.thpt.rag import retrieve_request
from exam_baseline.ui.errors import UiError


class TopicPlanningFixture:
    def __init__(self, topic, objective):
        self.topic = topic
        self.objective = objective

    async def complete(self, request):
        data = json.loads(request.user.splitlines()[1])
        if "parts" in data and "level_codes" in data:
            cells = [
                dict(
                    part_id=p["part_id"],
                    idx=c["idx"],
                    sub=c.get("sub"),
                    topic=self.topic,
                    requirement=self.objective,
                    idea=self.objective,
                )
                for p in data["parts"]
                for c in p["editable"]
            ]
            value = {"cells": cells}
        elif "cells" in data:
            value = {
                "cells": [
                    dict(c, topic=self.topic, requirement=self.objective) for c in data["cells"]
                ]
            }
        else:
            value = {
                "resolution": {"version": 1, "sources": [], "allocations": [], "groups": []},
                "gaps": [],
            }
        return Completion(json.dumps(value, ensure_ascii=False), "offline-test")


@pytest.mark.parametrize(
    ("instruction", "topic", "objective"),
    [
        ("hãy cho tôi bài tập tích phân", "Tích phân", "Tính tích phân xác định"),
        ("M có thể tạo 1 đề toàn tổ hợp không", "Tổ hợp", "Đếm số cách chọn"),
        (
            "M có thể tạo 1 đề toàn tổ hợp không\nM có thể tạo 1 đề toán xác suất tổ hợp không",
            "Xác suất cổ điển và tổ hợp",
            "Đếm số cách chọn và tính xác suất cổ điển",
        ),
    ],
)
def test_focused_chat_reaches_real_planner_and_rag(instruction, topic, objective):
    if sys.version_info[:2] != (3, 11):
        pytest.skip("Compiled planner requires CPython 3.11")
    if subprocess.run(
        ["git", "cat-file", "-e", DEFAULT_RAG_CORPUS_REF], capture_output=True
    ).returncode:
        pytest.skip("Pinned RAG corpus is not available")
    result = asyncio.run(
        prepare_math_plan(
            instruction, TopicPlanningFixture(topic, objective), Settings.for_offline()
        )
    )
    assert result["plan"]["plan_revision"]
    request = retrieve_request(math_request(result, instruction))
    assert len(request.rag_evidence) == 22
    assert all(slot.topic.casefold() == topic.casefold() for slot in request.slots)
    for slot in request.slots:
        if slot.part == "P2":
            assert all(f"{letter})" in slot.objective for letter in "abcd")
    cells = result["plan"]["cells"]
    if topic.startswith("Xác suất"):
        original = cells[0]["topic"]
        cells[0]["topic"] = "Đạo hàm"
        with pytest.raises(UiError, match="chưa bám đúng"):
            math_request(result, instruction)
        cells[0]["topic"] = original
    cells.append(cells[0])
    with pytest.raises(UiError, match="22 câu"):
        math_request(result, instruction)


def test_blocked_plan_keeps_address_for_teacher():
    gaps = [{"code": "mas_unfilled_cells", "address": {"part_id": "P2", "idx": 1, "sub": "c"}}]
    with pytest.raises(UiError) as error:
        math_request(
            {"schema_version": "astra-mas-plan-v1", "state": "blocked", "gaps": gaps}, "Toán"
        )
    assert error.value.details == gaps
