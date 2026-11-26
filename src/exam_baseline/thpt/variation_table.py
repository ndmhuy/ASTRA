"""Structured variation tables with deterministic, print-friendly TikZ layout."""

import re
from collections.abc import Iterator
from typing import Literal

from pydantic import Field, ValidationInfo, field_validator, model_validator

from exam_baseline.core.models import Model, Text
from exam_baseline.pipeline.rendering.syntax import check_fragment, validate_drawing_code
from exam_baseline.thpt.models import Drawing, Illustrations

Sign = Literal["+", "-", "0", "gap"]
_LABEL = re.compile(
    r"(?:[-+0-9A-Za-z{}.,/()^_ ]|"
    r"\\(?:frac|dfrac|tfrac|sqrt|infty|pi|ln|log|cdot|alpha|beta|pm|mp)(?![a-zA-Z]))+"
)
_NAME = r"bảng\s+biến\s+thiên|variation\s+table"
_TABLE_NAME = re.compile(rf"\b(?:{_NAME})\b", re.IGNORECASE)
_TABLE_REFERENCE = re.compile(
    rf"\b(?:(?:có|cho|dựa vào)\s+(?:{_NAME})|(?:{_NAME})\s+(?:như|sau|dưới|bên))\b",
    re.IGNORECASE,
)
_HEIGHT = {"+": 1, "-": -1, "0": 0}


def is_variation_table(stem: str, description: str) -> bool:
    return bool(_TABLE_NAME.search(description) or _TABLE_REFERENCE.search(stem))


class VariationPoint(Model):
    x: str = Field(min_length=1, max_length=36)
    kind: Literal["endpoint", "stationary", "critical", "regular", "break"]
    value: str | None = Field(default=None, min_length=1, max_length=40)
    left_limit: str | None = Field(default=None, min_length=1, max_length=40)
    right_limit: str | None = Field(default=None, min_length=1, max_length=40)

    @field_validator("x", "value", "left_limit", "right_limit")
    @classmethod
    def valid_math_label(cls, value: str | None) -> str | None:
        if value is not None and (not _LABEL.fullmatch(value) or check_fragment(value)):
            raise ValueError("Use a short math label without delimiters or formatting commands")
        return value

    @model_validator(mode="after")
    def valid_limits(self):
        if self.kind == "break":
            if self.value is not None or self.left_limit is None or self.right_limit is None:
                raise ValueError("A break requires separate left_limit and right_limit labels")
        elif self.value is None or self.left_limit is not None or self.right_limit is not None:
            raise ValueError("A regular point or endpoint requires just a value")
        return self


class VariationTable(Model):
    points: list[VariationPoint] = Field(min_length=2, max_length=7)
    signs: list[Sign] = Field(min_length=1, max_length=6)

    @model_validator(mode="after")
    def valid_intervals(self):
        if len(self.signs) != len(self.points) - 1:
            raise ValueError("Supply one derivative sign between each pair of ordered x values")
        if len({point.x for point in self.points}) != len(self.points):
            raise ValueError("Each x label must occur once")
        if self.signs[0] == "gap" or self.signs[-1] == "gap":
            raise ValueError("Begin and end at the boundaries of the represented domain")
        for i, point in enumerate(self.points):
            adjacent = self.signs[max(0, i - 1) : i + 1]
            boundary = i in {0, len(self.points) - 1} or "gap" in adjacent
            if (point.kind == "endpoint") != boundary or adjacent == ["gap", "gap"]:
                raise ValueError("Use endpoint at domain boundaries only")
        return self

    def continuous_segments(self) -> Iterator[tuple[int, int]]:
        """Yield inclusive point indices for each connected part of the graph."""
        first = 0
        for i, sign in enumerate(self.signs):
            if sign == "gap":
                if first < i:
                    yield first, i
                first = i + 1
            elif self.points[i + 1].kind == "break":
                yield first, i + 1
                first = i + 1
        if first < len(self.signs):
            yield first, len(self.signs)


def render_variation_table(table: VariationTable) -> str:
    """Use the Math template's TikZ libraries, including for one-sided limits."""
    xs = [2.02 + i * 2.5 for i in range(len(table.points))]
    width = xs[-1] + 0.69
    label_x = 0.63
    margin_x = 1.25
    lines = [
        r"\begin{tikzpicture}[x=1cm,y=1cm,>=Stealth,line cap=round,",
        r"  every node/.style={inner sep=2pt}]",
        rf"\fill[black!4] (0,3.08) rectangle ({width:.2f},3.80);",
        rf"\fill[black!4] (0,0) rectangle ({margin_x:.2f},3.80);",
    ]
    for i, sign in enumerate(table.signs):
        if sign == "gap":
            lines.append(
                rf"\fill[pattern=north east lines,pattern color=black!28] "
                rf"({xs[i]:.2f},0) rectangle ({xs[i + 1]:.2f},3.08);"
            )
        else:
            middle = (xs[i] + xs[i + 1]) / 2
            lines.append(rf"\node at ({middle:.2f},2.73) {{\({sign}\)}};")
    lines.extend(
        [
            rf"\draw[line width=0.55pt] (0,0) rectangle ({width:.2f},3.80);",
            rf"\draw[line width=0.40pt] ({margin_x:.2f},0) -- ({margin_x:.2f},3.80);",
            rf"\draw[line width=0.40pt] (0,3.08) -- ({width:.2f},3.08);",
            rf"\draw[line width=0.40pt] (0,2.38) -- ({width:.2f},2.38);",
            rf"\node at ({label_x:.2f},3.44) {{$x$}};",
            rf"\node at ({label_x:.2f},2.73) {{$f'(x)$}};",
            rf"\node at ({label_x:.2f},1.19) {{$f(x)$}};",
        ]
    )
    for x, point in zip(xs, table.points, strict=True):
        lines.append(rf"\node at ({x:.2f},3.44) {{\({point.x}\)}};")
        if point.kind == "stationary":
            lines.append(rf"\node at ({x:.2f},2.73) {{$0$}};")
        elif point.kind == "critical":
            lines.append(rf"\draw[dashed,line width=0.45pt] ({x:.2f},2.38) -- ({x:.2f},3.08);")
        elif point.kind == "break":
            for side in (x - 0.045, x + 0.045):
                lines.append(rf"\draw[line width=0.45pt] ({side:.2f},0) -- ({side:.2f},3.08);")

    for start, last in table.continuous_segments():
        ranks = [0]
        for sign in table.signs[start:last]:
            ranks.append(ranks[-1] + _HEIGHT[sign])
        low, high = min(ranks), max(ranks)
        nodes = []
        for i, rank in enumerate(ranks, start):
            level = 1.19 if low == high else 0.46 + (rank - low) * 1.46 / (high - low)
            point = table.points[i]
            x, placement, label = xs[i], "", point.value
            if point.kind == "break" and i == start:
                x, placement, label = x + 0.12, "[anchor=west]", point.right_limit
            elif point.kind == "break":
                x, placement, label = x - 0.12, "[anchor=east]", point.left_limit
            elif "gap" in table.signs[max(0, i - 1) : i + 1]:
                placement = "[fill=white]"
            name = f"v{start}p{i}"
            lines.append(rf"\node{placement} ({name}) at ({x:.2f},{level:.2f}) {{\({label}\)}};")
            nodes.append(name)
        for left, right in zip(nodes[:-1], nodes[1:], strict=True):
            lines.append(
                rf"\draw[->,line width=0.65pt,shorten <=1pt,shorten >=2pt] "
                rf"({left}.east) -- ({right}.west);"
            )
    return "\n".join([*lines, r"\end{tikzpicture}"])


class IllustrationCandidate(Model):
    question_id: str
    latex: Text | None = None
    variation_table: VariationTable | None = None

    @model_validator(mode="after")
    def one_representation(self):
        if (self.latex is None) == (self.variation_table is None):
            raise ValueError("Return exactly one of latex or variation_table")
        if self.latex is not None:
            validate_drawing_code(self.latex)
        return self


class IllustrationCandidates(Model):
    drawings: list[IllustrationCandidate] = Field(max_length=22)

    @model_validator(mode="after")
    def bind_requests(self, info: ValidationInfo):
        data = info.context or {}
        expected = {request["question_id"] for request in data["requests"]}
        targets = set(data["variation_table_question_ids"])
        ids = {drawing.question_id for drawing in self.drawings}
        if len(ids) != len(self.drawings) or ids != expected:
            raise ValueError("Return exactly one illustration for each requested question ID")
        structured = {d.question_id for d in self.drawings if d.variation_table is not None}
        if structured != targets:
            raise ValueError("Use variation_table exactly for variation_table_question_ids")
        return self

    def rendered(self) -> Illustrations:
        return Illustrations(
            drawings=[
                Drawing(
                    question_id=d.question_id,
                    latex=render_variation_table(d.variation_table)
                    if d.variation_table
                    else d.latex,
                )
                for d in self.drawings
            ]
        )
