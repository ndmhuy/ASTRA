"""Deterministic offline replay providers for THPT benchmark plumbing tests.

Replay results verify orchestration, contract validation, resuming, cost/latency
accounting, and report generation ONLY. They are never real model scores.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from exam_baseline.core.contracts import Completion, CompletionRequest
from exam_baseline.core.models import TokenUsage
from exam_baseline.thpt.models import Question, Request


def sample_question(slot, *, wrong_p1_key: bool = False) -> Question:
    n = int(slot.id.split("-")[1])
    data: dict = {
        "id": slot.id,
        "stem": f"[{slot.topic}] Tính giá trị biểu thức ${n} + 2$ ({slot.id}).",
        "solution": f"Thực hiện phép cộng cơ bản: ${n} + 2 = {n + 2}$.",
    }
    if slot.part == "P1":
        data["choices"] = {
            "A": f"${n + 2}$",
            "B": f"${n + 3}$",
            "C": f"${n + 4}$",
            "D": f"${n + 5}$",
        }
        data["answer"] = "B" if (wrong_p1_key and slot.id == "P1-1") else "A"
    elif slot.part == "P2":
        data["statements"] = [
            {
                "text": f"Giá trị ${n} + {idx} = {n + idx}$ là khẳng định đúng.",
                "answer": True,
                "solution": f"Cộng trực tiếp: ${n} + {idx} = {n + idx}$.",
            }
            for idx in range(1, 5)
        ]
    else:
        data["stem"] += " Ghi kết quả chính xác, không làm tròn."
        data["answer"] = str(n + 2)
    return Question.model_validate(data)


def sample_naive_latex(*, complete: bool = True, leak_answer: bool = False) -> str:
    """Return a deterministic LaTeX exam string for offline replay of naive_chat."""
    p1_count = 12 if complete else 8
    lines = [
        r"\documentclass[12pt,a4paper]{article}",
        r"\usepackage[utf8]{inputenc}",
        r"\usepackage{amsmath,amssymb}",
        r"\begin{document}",
        r"\section*{PHẦN I. Câu trắc nghiệm nhiều phương án lựa chọn}",
    ]
    for i in range(1, p1_count + 1):
        lines.append(rf"\noindent \textbf{{Câu {i}:}} Tính giá trị của ${i} + 2$.\\")
        lines.append(rf"A. ${i + 2}$ \quad B. ${i + 3}$ \quad C. ${i + 4}$ \quad D. ${i + 5}$\\")
        if leak_answer and i == 1:
            lines.append(r"Đáp án: A\\")
    lines.append(r"\section*{PHẦN II. Câu trắc nghiệm đúng sai}")
    for i in range(1, 5):
        lines.append(rf"\noindent \textbf{{Câu {i}:}} Xét biểu thức với $n = {i}$.\\")
        for label in "abcd":
            lines.append(rf"{label}) Khẳng định {label} đúng với $n = {i}$.\\")
    lines.append(r"\section*{PHẦN III. Câu trắc nghiệm trả lời ngắn}")
    for i in range(1, 7):
        lines.append(
            rf"\noindent \textbf{{Câu {i}:}} Tính ${i} + 2$. "
            r"Ghi kết quả chính xác, không làm tròn.\\"
        )
    lines.append(r"\end{document}")
    body = "\n".join(lines)
    return f"```latex\n{body}\n```\n\n### Bảng đáp án tham khảo\n- P1-1: A\n"


@dataclass
class ReplayThptProvider:
    """Offline deterministic LLMProvider for THPT benchmark suite replay."""

    role: str
    model: str
    request: Request
    trigger_revision: bool = False
    naive_complete: bool = True
    naive_leak: bool = False

    name: str = "replay_thpt"

    def __post_init__(self) -> None:
        self.calls: int = 0

    async def complete(self, prompt: CompletionRequest) -> Completion:
        self.calls += 1
        if self.role == "naive_chat":
            text = sample_naive_latex(complete=self.naive_complete, leak_answer=self.naive_leak)
            return Completion(
                text=text,
                model=self.model,
                usage=TokenUsage(input_tokens=1_200, output_tokens=2_800),
            )

        data = json.loads(prompt.user)
        ids = [slot.id for slot in self.request.slots]
        if self.role == "composer":
            part = data["part"]
            first_pass = data.get("feedback") is None
            questions = [
                sample_question(
                    slot, wrong_p1_key=(self.trigger_revision and first_pass)
                ).model_dump()
                for slot in self.request.slots
                if slot.part == part
            ]
            payload = {"questions": questions}
            usage = TokenUsage(input_tokens=3_200, output_tokens=1_800)
        elif self.role == "illustrator":
            payload = {"drawings": []}
            usage = TokenUsage(input_tokens=400, output_tokens=80)
        elif self.role == "solver":
            entries = []
            for q in data["questions"]:
                qid = q["id"]
                num = int(qid.split("-")[1])
                if qid.startswith("P1-"):
                    ans = "A"
                elif qid.startswith("P2-"):
                    ans = "a: Đúng; b: Đúng; c: Đúng; d: Đúng"
                else:
                    ans = str(num + 2)
                entries.append(
                    {
                        "question_id": qid,
                        "answer": ans,
                        "reasoning": f"Giải độc lập cho {qid}.",
                        "status": "solved",
                    }
                )
            payload = {"entries": entries}
            usage = TokenUsage(input_tokens=4_500, output_tokens=2_200)
        elif self.role == "reviewer":
            if self.trigger_revision:
                payload = {
                    "checked_ids": ids,
                    "decision": "needs_revision",
                    "issues": ["P1-1: Composer key (B) disagrees with independent Solver (A)."],
                }
            else:
                payload = {
                    "checked_ids": ids,
                    "decision": "approved",
                    "issues": [],
                }
            usage = TokenUsage(input_tokens=5_000, output_tokens=400)
        else:
            raise ValueError(f"Unsupported replay role: {self.role}")
        return Completion(
            text=json.dumps(payload, ensure_ascii=False),
            model=self.model,
            usage=usage,
        )
