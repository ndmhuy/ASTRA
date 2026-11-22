"""Zero-cost local demo exam generator with valid THPT and V-ACT artifacts."""

import asyncio
import json
from pathlib import Path

from exam_baseline.vact import template as vact_template


def _thpt_demo_questions(slots) -> list[dict]:
    questions = []
    for slot in slots:
        number = slot.id.split("-")[1]
        if slot.part == "P1":
            questions.append(
                {
                    "id": slot.id,
                    "stem": (
                        f"[Bản mẫu chạy thử - Câu {number}] Cho hàm số $f(x) = x + {number}$ "
                        f"thuộc chủ đề {slot.topic}. Giá trị của $f(1)$ bằng bao nhiêu?"
                    ),
                    "choices": {
                        "A": f"${int(number)}$",
                        "B": f"${int(number) + 1}$",
                        "C": f"${int(number) + 2}$",
                        "D": f"${int(number) + 3}$",
                    },
                    "statements": [],
                    "answer": "B",
                    "solution": (
                        f"Thay $x = 1$ vào hàm số mẫu ta được "
                        f"$f(1) = 1 + {number} = {int(number) + 1}$."
                    ),
                    "illustration_request": None,
                }
            )
        elif slot.part == "P2":
            questions.append(
                {
                    "id": slot.id,
                    "stem": (
                        f"[Bản mẫu chạy thử - Phần II, Câu {number}] "
                        f"Xét các nhận định sau về chủ đề {slot.topic} "
                        f"với giá trị tham chiếu $k = {number}$:"
                    ),
                    "choices": {},
                    "statements": [
                        {
                            "text": (
                                f"Nhận định a) Với $k = {number}$, "
                                "giá trị $k + 1$ là số lớn hơn $k$."
                            ),
                            "answer": True,
                            "solution": "Vì $k + 1 > k$ với mọi số thực.",
                        },
                        {
                            "text": f"Nhận định b) Với $k = {number}$, biểu thức $k - k$ bằng $1$.",
                            "answer": False,
                            "solution": "Hiệu của một số với chính nó luôn bằng $0$.",
                        },
                        {
                            "text": f"Nhận định c) Tổng $k + 2$ bằng ${int(number) + 2}$.",
                            "answer": True,
                            "solution": f"Phép cộng trực tiếp cho kết quả ${int(number) + 2}$.",
                        },
                        {
                            "text": f"Nhận định d) Giá trị $2k$ nhỏ hơn $k$ với $k = {number}$.",
                            "answer": False,
                            "solution": f"Với $k = {number} > 0$ thì $2k > k$.",
                        },
                    ],
                    "answer": None,
                    "solution": "Lời giải mẫu chạy thử (Demo) cho bốn nhận định a, b, c, d.",
                    "illustration_request": None,
                }
            )
        else:
            questions.append(
                {
                    "id": slot.id,
                    "stem": (
                        f"[Bản mẫu chạy thử - Phần III, Câu {number}] "
                        f"Tính giá trị biểu thức mẫu $S = 10 + {number}$ thuộc chủ đề {slot.topic}."
                    ),
                    "choices": {},
                    "statements": [],
                    "answer": str(10 + int(number)),
                    "solution": (
                        f"Kết quả mẫu chạy thử là $S = 10 + {number} = {10 + int(number)}$."
                    ),
                    "illustration_request": None,
                }
            )
    return questions


def _vact_demo_passage(group) -> dict:
    if group.kind == "vact_passage_en":
        return {
            "id": group.id,
            "heading": f"Sample Reading Passage ({group.start}-{group.end})",
            "text": (
                f"[Demo mode] Urban green spaces (questions {group.start}-{group.end}) help "
                "moderate local temperatures and improve air quality for residents. "
                "Local planners collect annual tree-canopy measurements to evaluate "
                "neighborhood cooling."
            ),
            "table": None,
        }
    if group.id == "g97_99":
        return {
            "id": group.id,
            "heading": "Bảng số liệu minh họa thị phần (Chế độ chạy thử)",
            "text": (
                "[Bản mẫu chạy thử] Bảng dưới đây mô phỏng số liệu doanh số của hai doanh nghiệp "
                "X và Y trong các năm 2015 và 2025 để thầy cô xem trước giao diện bảng."
            ),
            "table": {
                "columns": ["Doanh nghiệp", "Năm 2015 (triệu máy)", "Năm 2025 (triệu máy)"],
                "rows": [
                    ["Công ty X", "$12$", "$38$"],
                    ["Công ty Y", "$15$", "$29$"],
                ],
            },
        }
    if group.id == "g100_102":
        return {
            "id": group.id,
            "heading": "Bảng tần số minh họa (Chế độ chạy thử)",
            "text": (
                "[Bản mẫu chạy thử] Bảng phân bố tần số mẫu dùng để kiểm tra hiển thị thống kê."
            ),
            "table": {
                "columns": ["Khoảng giá trị", "Tần số"],
                "rows": [
                    ["$[2{,}0; 2{,}5)$", "$60$"],
                    ["$[2{,}5; 3{,}0)$", "$280$"],
                    ["$[3{,}0; 3{,}5)$", "$820$"],
                ],
            },
        }
    if group.id == "g109_111":
        return {
            "id": group.id,
            "heading": "Thí nghiệm minh họa (Chế độ chạy thử)",
            "text": (
                "[Bản mẫu chạy thử] Nhóm nghiên cứu theo dõi độ hấp thụ ánh sáng ở 4 nghiệm thức "
                "mẫu ở nhiệt độ $25^{\\circ}\\text{C}$."
            ),
            "table": {
                "columns": ["Nghiệm thức", "Dung dịch xử lý", "Độ hấp thụ"],
                "rows": [
                    ["NT 1", "Nước sạch đối chứng", "$0{,}09$"],
                    ["NT 2", "Mẫu pha loãng 25%", "$0{,}15$"],
                ],
            },
        }
    return {
        "id": group.id,
        "heading": f"Ngữ liệu minh họa câu {group.start}–{group.end} (Chế độ chạy thử)",
        "text": (
            f"[Bản mẫu chạy thử] Đây là đoạn thông tin mẫu dùng chung cho các câu từ "
            f"{group.start} đến {group.end}, giúp thầy cô xem trước cách đề V-ACT hiển thị "
            "ngữ cảnh trên web và PDF."
        ),
        "table": None,
    }


def _vact_demo_question(group, num: int, section: str, slot) -> dict:
    qid = f"q{num}"
    passage_id = group.id if group.shared else None
    if section == "TA":
        if group.kind == "vact_error_id":
            stem = (
                f"[Demo #{num}] Students [A] in this class [B] practices English reading [C] "
                "every morning [D] before class."
            )
            choices = {
                "A": "in this class",
                "B": "practices",
                "C": "every morning",
                "D": "before class",
            }
        elif group.kind == "vact_gap_fill":
            stem = f"[Demo #{num}] She ___ finished preparing the lesson plan before the bell rang."
            choices = {
                "A": "have",
                "B": "had",
                "C": "having",
                "D": "has been",
            }
        else:
            stem = (
                f"[Demo #{num}] Sample English question ({group.kind}) testing "
                f"item {num} in demo mode."
            )
            choices = {
                "A": f"Sample option A ({num})",
                "B": f"Sample option B ({num})",
                "C": f"Sample option C ({num})",
                "D": f"Sample option D ({num})",
            }
        solution = "Lời giải mẫu chạy thử cho câu hỏi Tiếng Anh."
    else:
        stem = (
            f"[Bản mẫu chạy thử - Câu {num}] Câu hỏi minh họa phần {slot.topic}: "
            f"giá trị biểu thức $1 + {num}$ là bao nhiêu?"
        )
        choices = {
            "A": f"${num}$",
            "B": f"${num + 1}$",
            "C": f"${num + 2}$",
            "D": f"${num + 3}$",
        }
        solution = f"Lời giải mẫu chạy thử: $1 + {num} = {num + 1}$."
    return {
        "id": qid,
        "stem": stem,
        "choices": choices,
        "answer": "B",
        "solution": solution,
        "passage_id": passage_id,
        "illustration_request": None,
    }


async def run_demo_job(request, output: Path, progress, *, is_vact: bool) -> dict:
    """Write valid local demo artifacts without calling any external AI provider."""
    output.mkdir(parents=True, exist_ok=True)
    internal = output / "_internal" / "revision_1"
    internal.mkdir(parents=True, exist_ok=True)

    if is_vact:
        batches = vact_template.batches()
        slot_by_id = {slot.id: slot for slot in request.slots}
        passages = []
        questions = []
        for batch in batches:
            progress("composer", batch.id, 1)
            await asyncio.sleep(0.02)
            for group in batch.groups:
                if group.shared:
                    passages.append(_vact_demo_passage(group))
                for num in range(group.start, group.end + 1):
                    questions.append(
                        _vact_demo_question(group, num, batch.section, slot_by_id[f"q{num}"])
                    )
        progress("solver", batches[0].id, 1)
        await asyncio.sleep(0.02)
        progress("reviewer", None, 1)
        solver_entries = [
            {
                "question_id": q["id"],
                "answer": q["answer"],
                "reasoning": "Đáp án đối chiếu mẫu (chế độ chạy thử).",
                "status": "solved",
            }
            for q in questions
        ]
        answers_payload = {
            "status": "pending_human_review",
            "revision": 1,
            "composer": questions,
            "passages": passages,
            "independent_solver": {"entries": solver_entries},
        }
    else:
        for part in ("P1", "P2", "P3"):
            progress("composer", part, 1)
            await asyncio.sleep(0.02)
        questions = _thpt_demo_questions(request.slots)
        progress("solver", None, 1)
        await asyncio.sleep(0.02)
        progress("reviewer", None, 1)
        solver_entries = [
            {
                "question_id": q["id"],
                "answer": q["answer"] or "Đ/S/Đ/S",
                "reasoning": "Đáp án đối chiếu mẫu (chế độ chạy thử).",
                "status": "solved",
            }
            for q in questions
        ]
        answers_payload = {
            "status": "pending_human_review",
            "revision": 1,
            "composer": questions,
            "independent_solver": {"entries": solver_entries},
        }

    (internal / "illustrations.json").write_text(
        json.dumps({"drawings": []}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output / "dap_an_va_loi_giai.json").write_text(
        json.dumps(answers_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {
        "execution_status": "completed",
        "revision": 1,
        "demo_mode": True,
    }


def regenerate_demo_question(old: dict, instruction: str) -> dict:
    """Return a valid locally revised THPT question in demo mode without API calls."""
    suffix = f" ({instruction.strip()[:80]})" if instruction.strip() else " (đã làm mới bản mẫu)"
    base_stem = old["stem"].split(" [Bản làm mới", 1)[0]
    return {
        **old,
        "stem": f"{base_stem} [Bản làm mới{suffix}]",
    }
