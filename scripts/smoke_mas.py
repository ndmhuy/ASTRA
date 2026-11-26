"""Run a synthetic CSV-to-plan request using the public MAS callback contract."""

import asyncio
import json

from astra_mas import MasFile, MasInput, MasPrompt, prepare_plan

MATRIX = (
    "Phần,Câu,Chủ đề,Mức độ,Dạng,Yêu cầu cần đạt\n"
    "P1,C1,Đạo hàm,Nhận biết,Nhiều lựa chọn,Nhận biết đạo hàm\n"
)


async def fixture_complete(prompt: MasPrompt) -> str:
    """Return fixture JSON through the same interface as ASTRA's live LLM."""
    data = json.loads(prompt.user.splitlines()[1])
    if prompt.recipe == "PLAN_INPUT_RESOLUTION":
        return json.dumps(
            {
                "resolution": {"version": 1, "sources": [], "allocations": [], "groups": []},
                "gaps": [],
            }
        )
    if prompt.recipe == "PLAN_PART_CONTENT":
        cells = data["cells"]
        for cell in cells:
            cell["topic"] = cell["topic"] or "Đạo hàm"
            cell["requirement"] = cell["requirement"] or "Nhận biết đạo hàm"
        return json.dumps({"cells": cells})
    if prompt.recipe == "PLAN_SYNTHESIS":
        return json.dumps(
            {
                "cells": [
                    {
                        "part_id": part["part_id"],
                        "idx": cell["idx"],
                        "sub": cell.get("sub"),
                        "topic": "Đạo hàm",
                        "requirement": "Đạo hàm của hàm số",
                        "idea": "Đọc dấu đạo hàm trên bảng biến thiên.",
                    }
                    for part in data["parts"]
                    for cell in part["editable"]
                ]
            }
        )
    raise ValueError(f"Unexpected recipe in the CSV fixture {prompt.recipe}")


async def main() -> int:
    value = MasInput(
        exam_type="THPTQG",
        subject="Toán",
        grade=12,
        instruction="Chỉ dùng kiến thức đạo hàm.",
        matrix=MasFile(filename="ma-tran.csv", data=MATRIX.encode("utf-8")),
    )
    result = await prepare_plan(value, fixture_complete)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["state"] == "ready" and len(result["plan"]["cells"]) == 34 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
