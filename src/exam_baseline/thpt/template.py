"""Byte-preserving template registry. Only three question-content spans are replaceable."""

import re
from hashlib import sha256
from importlib.resources import files

TEMPLATE_SHA256 = "e1af472a5363364814072625c40c98f7e6a77a00093d709568068826feacfdb7"


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
    if set(parts) != {"P1", "P2", "P3"}:
        raise ValueError("All three parts are mandatory")
    raw = original()
    chunks, cursor = [], 0
    for part, (start, end) in zip(("P1", "P2", "P3"), spans(raw), strict=True):
        chunks.extend((raw[cursor:start], parts[part].encode("utf-8")))
        cursor = end
    chunks.append(raw[cursor:])
    return b"".join(chunks)


def reference_parts() -> dict[str, str]:
    raw = original()
    return {
        p: raw[a:b].decode("utf-8")
        for p, (a, b) in zip(("P1", "P2", "P3"), spans(raw), strict=True)
    }
