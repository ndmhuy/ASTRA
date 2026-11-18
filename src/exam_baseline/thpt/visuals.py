"""Deterministic checks for references that need an Illustrator artifact."""

import re

REFERENCE = re.compile(
    r"(?:hình\s+(?:vẽ|bên|dưới|sau)|(?:đồ thị|bảng biến thiên|bảng số liệu|bảng tần số)"
    r"\s+(?:như|ở|sau|dưới|bên|cho)|\bbảng\s+(?:như\s+)?(?:sau|dưới đây|bên dưới))",
    re.IGNORECASE,
)
RAW_TABLE = re.compile(r"\\(?:begin|end)\s*\{(?:array|tabular\*?|longtable)\}|\\hline\b")


def validate_table_source(stem: str) -> None:
    if RAW_TABLE.search(stem):
        raise ValueError(
            "raw_table: remove the LaTeX table from the stem. Put all headers, units, "
            "and cells in illustration_request for TikZ, or give all data in plain prose."
        )


def visual_issues(stem: str, illustration_request: str | None) -> list[str]:
    issues = []
    prose = re.sub(r"\$[^$]*\$", "MATH", stem)
    if any(line.count("|") >= 3 for line in prose.splitlines()):
        issues.append("pseudo_table: replace pipe-delimited rows with an Illustrator request")
    if REFERENCE.search(stem) and not (illustration_request or "").strip():
        issues.append("missing_illustration_request: referenced figure/table needs native TikZ")
    return issues
