"""Deterministic checks for references that need an Illustrator artifact."""

import re

REFERENCE = re.compile(
    r"(?:hình\s+(?:vẽ|bên|dưới|sau)|(?:đồ thị|bảng biến thiên|bảng số liệu|bảng tần số)"
    r"\s+(?:như|ở|sau|dưới|bên|cho))",
    re.IGNORECASE,
)


def visual_issues(stem: str, illustration_request: str | None) -> list[str]:
    issues = []
    prose = re.sub(r"\$[^$]*\$", "MATH", stem)
    if any(line.count("|") >= 3 for line in prose.splitlines()):
        issues.append("pseudo_table: replace pipe-delimited rows with an Illustrator request")
    if REFERENCE.search(stem) and not (illustration_request or "").strip():
        issues.append("missing_illustration_request: referenced figure/table needs native TikZ")
    return issues
