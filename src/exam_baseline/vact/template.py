"""Template database and content plan derived from the actual supplied source."""

import re
from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files

TEMPLATE_SHA256 = "88929426928a869409f9a422cedf02f1ebc2ca686e4adf208dcb94e4a113147d"
SECTIONS = ("TV", "TA", "TO", "LOGIC", "SCIENCE")


def original() -> bytes:
    raw = files("exam_baseline.resources").joinpath("templates/PROTO_vact_vact.tex").read_bytes()
    if sha256(raw).hexdigest() != TEMPLATE_SHA256:
        raise ValueError("VACT template hash differs from the user's original")
    return raw


def spans(raw: bytes) -> list[tuple[int, int]]:
    blocks = [m.start() for m in re.finditer(rb"(?m)^% LECTURING-BLOCK: ", raw)]
    boundaries = [raw.index(b"% LECTURING-PART: " + p) for p in (b"TV", b"TA", b"TO", b"KH")]
    boundaries.append(raw.index(b"% LECTURING-SUBHEADING"))
    starts = [next(b for b in blocks if b > a) for a in boundaries]
    ends = [raw.rindex(b"\\vspace{0.5cm}", starts[i], boundaries[i + 1]) for i in range(4)]
    ends.append(raw.index(b"\\interlinepenalty=0\\vspace{0.6cm}", starts[-1]))
    return list(zip(starts, ends, strict=True))


@dataclass(frozen=True)
class Group:
    section: str
    start: int
    end: int
    kind: str
    reference: str

    @property
    def id(self):
        return f"g{self.start}_{self.end}"

    @property
    def shared(self):
        return self.kind in {
            "passage",
            "vact_passage_en",
            "math_context",
            "logic_puzzle",
            "data_set",
            "science",
        }


@dataclass(frozen=True)
class Batch:
    section: str
    groups: tuple[Group, ...]

    @property
    def id(self):
        return f"{self.section}_{self.groups[0].start}_{self.groups[-1].end}"

    @property
    def ids(self):
        return [f"q{i}" for g in self.groups for i in range(g.start, g.end + 1)]


def batches() -> tuple[Batch, ...]:
    raw = original()
    result = []
    for section, (a, b) in zip(SECTIONS, spans(raw), strict=True):
        body = raw[a:b].decode("utf-8")
        blocks = list(re.finditer(r"(?m)^% LECTURING-BLOCK: (\w+)", body))
        groups = []
        for index, block in enumerate(blocks):
            chunk = body[
                block.start() : blocks[index + 1].start() if index + 1 < len(blocks) else len(body)
            ]
            headers = list(re.finditer(r"\\noindent\s*\\textbf\{Câu (\d+):\}", chunk))
            if not headers:
                raise ValueError("VACT content block has no questions")
            numbers = [int(m[1]) for m in headers]
            if numbers != list(range(numbers[0], numbers[-1] + 1)):
                raise ValueError("Non-contiguous template question numbers")
            if block[1] == "single" and len(numbers) > 12:
                for offset in range(0, len(numbers), 10):
                    end = min(offset + 10, len(numbers))
                    reference = chunk[
                        headers[offset].start() : headers[end].start()
                        if end < len(headers)
                        else len(chunk)
                    ]
                    groups.append(
                        Group(section, numbers[offset], numbers[end - 1], "single", reference)
                    )
            else:
                groups.append(Group(section, numbers[0], numbers[-1], block[1], chunk))
        pending, count = [], 0
        for group in groups:
            size = group.end - group.start + 1
            if pending and count + size > 12:
                result.append(Batch(section, tuple(pending)))
                pending, count = [], 0
            pending.append(group)
            count += size
        if pending:
            result.append(Batch(section, tuple(pending)))
    ids = [i for batch in result for i in batch.ids]
    if ids != [f"q{i}" for i in range(1, 121)]:
        raise ValueError("Template must contain q1..q120 exactly once")
    return tuple(result)


def reference_parts():
    return {b.id: "\n".join(g.reference for g in b.groups) for b in batches()}


def assemble(parts: dict[str, str]) -> bytes:
    if set(parts) != set(SECTIONS):
        raise ValueError("VACT requires all five content sections")
    raw = original()
    cursor, chunks = 0, []
    for section, (a, b) in zip(SECTIONS, spans(raw), strict=True):
        chunks.extend((raw[cursor:a], parts[section].encode("utf-8")))
        cursor = b
    return b"".join([*chunks, raw[cursor:]])
