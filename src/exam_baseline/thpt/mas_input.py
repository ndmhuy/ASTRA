"""Translate the MAS v1 plan envelope into the THPT Math generation contract."""

import asyncio
import csv
import io
import re

from exam_baseline.core.contracts import CompletionRequest, ImageInput, ProviderError
from exam_baseline.thpt.models import COUNTS, Request, Slot
from exam_baseline.thpt.planner import plan_request_from_prompt
from exam_baseline.ui.errors import UiError
from rag_workflow.models import CONFIG
from rag_workflow.query_parser import normalize

_PROBABILITY_COMBINATORICS = "Xác suất và tổ hợp"
_PROBABILITY_TOPIC = "Xác suất cổ điển và tổ hợp"


def probability_combinatorics_request(instruction):
    lines = instruction.strip().splitlines()
    if not lines:
        return False
    return bool(
        re.fullmatch(
            r"(?:(?:m|minh|ban)\s+)?(?:co the\s+)?(?:(?:hay|vui long)\s+)?"
            r"(?:(?:tao|cho)\s+(?:toi\s+)?(?:(?:1|mot)\s+)?(?:de|bai tap)\s+)?"
            r"(?:(?:toan|toan hoc|ve)\s+)?"
            r"(?:xac suat(?:\s+va|\s*[-–,/])?\s*to hop|to hop\s+(?:va\s+)?xac suat)"
            r"(?:\s+khong)?[.!?]*",
            normalize(lines[-1].strip()),
        )
    )


def practice_matrix(instruction, settings):
    """Supply a retrieval-backed level grid for a plain single-topic exercise request.

    Free-form constraints are resolved by MAS itself. Keep objectives editable so
    MAS writes the actual learning requirements for each cell.
    """
    match = re.fullmatch(
        r"(?:(?:m|mình|bạn)\s+)?(?:có thể\s+)?(?:(?:hãy|vui lòng)\s+)?"
        r"(?:(?:tạo cho|cho|tạo)\s+(?:tôi\s+)?(?:(?:1|một)\s+)?)?"
        r"(?:(?:đề(?:\s+toán)?|bài tập|chuyên đề)\s*:?\s*(?:(?:về|toàn|chỉ)\s+)?)?"
        r"([^\n.!?]+?)(?:\s+không)?[.!?]*",
        instruction.strip(),
        re.IGNORECASE,
    )
    compound = probability_combinatorics_request(instruction)
    if not match and not compound:
        return None
    topic = _PROBABILITY_COMBINATORICS if compound else match[1].strip()
    if not compound and normalize(topic) not in CONFIG["toan_umbrella_topics"]:
        return None
    grid = plan_request_from_prompt(
        topic, corpus_ref=settings.rag_corpus_ref, pack_dir=settings.rag_pack_dir
    )
    output = io.StringIO()
    rows = csv.writer(output)
    rows.writerow(["Phần", "Câu", "Chủ đề", "Mức độ", "Dạng", "Yêu cầu cần đạt"])
    levels = {"NB": "Nhận biết", "TH": "Thông hiểu", "VD": "Vận dụng", "VDC": "Vận dụng cao"}
    formats = {"P1": "Nhiều lựa chọn", "P2": "Đúng sai", "P3": "Trả lời ngắn"}
    for slot in grid.slots:
        idx = slot.id.split("-")[1]
        for label, level in zip(
            "abcd" if slot.statement_levels else [""],
            slot.statement_levels or [slot.level],
            strict=True,
        ):
            rows.writerow(
                [
                    slot.part,
                    f"C{idx}{label}",
                    _PROBABILITY_TOPIC if compound else topic,
                    levels[level],
                    formats[slot.part],
                    "",
                ]
            )
    return output.getvalue().encode("utf-8")


async def prepare_math_plan(instruction, provider, settings):
    try:
        from astra_mas import MasError, MasFile, MasInput, prepare_plan
    except ImportError as exc:
        raise UiError("mas_unavailable", "Bộ lập kế hoạch Toán cần CPython 3.11.", 503) from exc

    provider_error = None

    async def complete(prompt):
        nonlocal provider_error
        try:
            reply = await provider.complete(
                CompletionRequest(
                    system=prompt.system,
                    user=prompt.user,
                    output_schema={"type": "object"},
                    images=tuple(ImageInput(image) for image in prompt.images),
                )
            )
        except ProviderError as exc:
            provider_error = exc
            raise
        return reply.text

    grid = await asyncio.to_thread(practice_matrix, instruction, settings)
    try:
        return await prepare_plan(
            MasInput(
                exam_type="THPTQG",
                subject="Toán",
                grade=12,
                instruction=instruction,
                matrix=MasFile(filename="khung-muc-do-rag.csv", data=grid) if grid else None,
            ),
            complete,
        )
    except MasError as exc:
        if provider_error is not None:
            raise provider_error from exc
        raise UiError(exc.code, f"Không lập được kế hoạch Toán ({exc.code}).", 422) from exc


def math_request(result, instruction):
    if result.get("schema_version") != "astra-mas-plan-v1" or result.get("state") != "ready":
        raise UiError(
            "mas_plan_blocked", "Chưa xác định đủ phạm vi từng câu.", 422, result.get("gaps")
        )
    cells = result["plan"]["cells"]
    indexed = {(c["part_id"], c["idx"], c["sub"]): c for c in cells}
    expected = {
        (part, idx, sub)
        for part, count in COUNTS.items()
        for idx in range(1, count + 1)
        for sub in ("abcd" if part == "P2" else [None])
    }
    if set(indexed) != expected or len(cells) != len(expected):
        raise UiError("mas_shape_mismatch", "Ma trận không khớp cấu trúc 22 câu Toán THPT.", 422)
    slots = []
    compound = probability_combinatorics_request(instruction)
    for part, count in COUNTS.items():
        for idx in range(1, count + 1):
            group = [indexed[part, idx, sub] for sub in ("abcd" if part == "P2" else [None])]
            objectives = []
            for cell in group:
                if not cell["topic"].strip() or not cell["requirement"].strip():
                    raise UiError("mas_empty_cell", "Ô trong ma trận còn thiếu nội dung.", 422)
                if compound and normalize(cell["topic"]) != normalize(_PROBABILITY_TOPIC):
                    raise UiError(
                        "mas_scope_mismatch",
                        "Ma trận chưa bám đúng yêu cầu xác suất và tổ hợp. Hãy thử tạo lại.",
                        422,
                    )
                prefix = f"{cell['sub']}) {cell['topic']}: " if cell["sub"] else ""
                objectives.append(
                    prefix + cell["requirement"] + " " + (cell.get("assessment") or "")
                )
            slots.append(
                Slot(
                    id=f"{part}-{idx}",
                    part=part,
                    topic=" / ".join(dict.fromkeys(c["topic"] for c in group)),
                    objective="\n".join(o.strip() for o in objectives),
                    level=group[-1]["level"],
                    statement_levels=[c["level"] for c in group] if part == "P2" else [],
                )
            )
    requirements = [
        instruction,
        "Mỗi câu và từng ý đúng/sai phải thực sự kiểm tra kiến thức giáo viên yêu cầu. "
        "Kiểm tra thao tác cần dùng để giải, không chỉ nhãn chủ đề hay từ xuất hiện trong đề.",
    ]
    if all(normalize(slot.topic).strip() == "tich phan" for slot in slots):
        requirements.append(
            "Mỗi ý đúng/sai phải dùng tích phân xác định, tính chất hoặc ứng dụng của nó "
            "và thể hiện bước đó trong lời giải. Không dùng ý chỉ tìm nguyên hàm, xét dấu "
            "hay tính đạo hàm. Các ý cùng câu phải dựa trên dữ kiện chung và hỏi các đại lượng "
            "hoặc tính chất khác nhau."
        )
    if compound:
        requirements.append(
            "Chỉ dùng xác suất và tổ hợp. Mỗi câu và từng ý đúng/sai phải trực tiếp "
            "kiểm tra tính xác suất, quy tắc đếm, hoán vị, chỉnh hợp hoặc tổ hợp."
        )
    return Request(
        slots=slots,
        topic_review_instruction=_PROBABILITY_COMBINATORICS if compound else instruction,
        requirements=requirements,
    )
