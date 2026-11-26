"""Byte-preserving Math template and derived frames for other THPT subjects."""

import re
from hashlib import sha256
from importlib.resources import files

TEMPLATE_SHA256 = "e1af472a5363364814072625c40c98f7e6a77a00093d709568068826feacfdb7"
PARTS = ("P1", "P2", "P3")
SHORT_ANSWER_INSTRUCTION = "Thí sinh điền đáp án vào Phiếu trả lời trắc nghiệm."


def original() -> bytes:
    raw = (
        files("exam_baseline.resources").joinpath("templates/PROTO_thptqg_toan_v2.tex").read_bytes()
    )
    if sha256(raw).hexdigest() != TEMPLATE_SHA256:
        raise ValueError("Template differs from the user's original; generation refused")
    return raw


def spans(raw: bytes) -> list[tuple[int, int]]:
    starts = [m.start() for m in re.finditer(rb"\\noindent \\textbf\{C\xc3\xa2u 1:\}", raw)]
    if len(starts) != 3:
        raise ValueError("Expected three original question sections")
    ends = [raw.rindex(b"\\vspace{0.5cm}", starts[i], starts[i + 1]) for i in (0, 1)]
    ends.append(raw.index(b"\\vspace{0.6cm}", starts[2]))
    return list(zip(starts, ends, strict=True))


def assemble(parts: dict[str, str]) -> bytes:
    if set(parts) != set(PARTS):
        raise ValueError("All three parts are mandatory")
    raw = original()
    chunks, cursor = [], 0
    for part, (start, end) in zip(PARTS, spans(raw), strict=True):
        chunks.extend((raw[cursor:start], parts[part].encode("utf-8")))
        cursor = end
    chunks.append(raw[cursor:])
    return b"".join(chunks)


def assemble_subject(
    subject: str,
    duration: int,
    counts: dict[str, int],
    bodies: dict[str, str],
    *,
    front_matter: str = "",
) -> bytes:
    """Keep the Math frame and use the subject's populated sections in order."""
    if (
        not counts
        or counts.keys() != set(PARTS[: len(counts)])
        or bodies.keys() != counts.keys()
        or any(n < 1 for n in counts.values())
    ):
        raise ValueError("Subject counts and question bodies must agree")

    raw = original()
    boundaries = spans(raw)
    start = raw.index(b"% LECTURING-PART: P1")
    header = raw[:start].decode("utf-8")
    header = header.replace("Môn thi: TOÁN", f"Môn thi: {subject.upper()}")
    header = header.replace("90 phút", f"{duration} phút")
    output = [header, front_matter]
    for index, (part, (body_start, _)) in enumerate(zip(PARTS, boundaries, strict=True)):
        if part not in counts:
            continue
        part_start = start if index == 0 else boundaries[index - 1][1]
        heading = raw[part_start:body_start].decode("utf-8")
        heading = re.sub(r"(?<=đến câu )\d+(?=\.)", str(counts[part]), heading, count=1)
        if part == "P3":
            heading = heading.replace(
                "Thí sinh chỉ điền một con số (có thể có dấu âm, dấu phẩy thập phân) vào ô trống.",
                SHORT_ANSWER_INSTRUCTION,
            )
        output.extend((heading, bodies[part]))
    output.append(raw[boundaries[-1][1] :].decode("utf-8"))
    return "".join(output).encode("utf-8")


def reference_parts() -> dict[str, str]:
    raw = original()
    return {p: raw[a:b].decode("utf-8") for p, (a, b) in zip(PARTS, spans(raw), strict=True)}
