#!/usr/bin/env python3
"""Normalize curriculum_map_data JSONL rows into a compact catalog.

Only copies curriculum labels and provenance already present in source rows.
No subject-specific curriculum content or lesson mappings are synthesized.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


STRUCTURAL_KINDS = {"chương", "chủ đề", "phần"}


def load_catalog(source_dir: Path) -> dict[str, Any]:
    files = sorted(source_dir.glob("*.jsonl"))
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    file_grade_pairs: set[tuple[str, int]] = set()
    sources = []
    gaps = []

    for path in files:
        raw = path.read_bytes()
        rows = []
        for line_number, line in enumerate(raw.decode("utf-8").splitlines(), 1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_source_path"] = path.name
            row["_line"] = line_number
            rows.append(row)
        sources.append({
            "path": str(path),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "records": len(rows),
        })
        match = re.search(r"-(10|11|12)$", path.stem)
        if not match:
            gaps.append({"path": str(path), "reason": "Filename does not end in a recognized grade suffix."})
            continue
        if rows:
            file_grade_pairs.add((re.sub(r"-(10|11|12)$", "", path.stem), int(match.group(1))))
            for row in rows:
                if not all(key in row for key in ("subject", "grade", "kind", "title_vi", "source")):
                    gaps.append({"path": str(path), "line": row["_line"], "reason": "Required catalog field missing."})
                    continue
                slug = re.sub(r"-(10|11|12)$", "", path.stem)
                grouped[slug].append(row)
        else:
            slug = re.sub(r"-(10|11|12)$", "", path.stem)
            file_grade_pairs.add((slug, int(match.group(1))))
            gaps.append({
                "path": str(path), "subject_slug": slug,
                "grade": int(match.group(1)),
                "reason": "Source JSONL is empty; no chapter or lesson rows to normalize.",
            })

    subjects: dict[str, list[dict[str, Any]]] = {}
    for slug, rows in sorted(grouped.items()):
        by_id = {row.get("unit_id"): row for row in rows if row.get("unit_id")}
        parent_ids = {row.get("parent_id") for row in rows if row.get("parent_id")}
        entries = []
        for row in sorted(rows, key=lambda item: (item.get("grade", 0), item.get("order", 0), item.get("_line", 0))):
            kind = row.get("kind")
            is_parent = row.get("unit_id") in parent_ids or kind in STRUCTURAL_KINDS
            parent = by_id.get(row.get("parent_id"))
            chapter = row.get("title_vi") if is_parent else (parent.get("title_vi") if parent else None)
            lesson = None if is_parent else row.get("title_vi")
            entries.append({
                "grade": row.get("grade"),
                "chapter": chapter,
                "lesson": lesson,
                "kind": kind,
                "unit_id": row.get("unit_id"),
                "parent_id": row.get("parent_id"),
                "provenance": {
                    "path": row["_source_path"],
                    "line": row["_line"],
                    "document": row.get("source", {}).get("document"),
                    "page": row.get("source", {}).get("page"),
                    "source_type": row.get("source_type"),
                    "status": row.get("status"),
                },
            })
        subjects[slug] = entries

    grades_by_slug = {
        slug: sorted({entry["grade"] for entry in entries if isinstance(entry.get("grade"), int)})
        for slug, entries in subjects.items()
    }
    # Report missing grade files within the catalog's 10–12 coverage window.
    for slug in sorted(subjects):
        for grade in (10, 11, 12):
            if (slug, grade) not in file_grade_pairs:
                gaps.append({
                    "subject_slug": slug,
                    "grade": grade,
                    "reason": "No source JSONL file for this subject and grade in the 10–12 catalog window.",
                })
    return {
        "schema": "curriculum-catalog-v1",
        "normalization": "Copied title_vi and grade from source rows; chapter links use parent_id or an explicitly structural kind. No curriculum facts inferred.",
        "source_directory": str(source_dir),
        "source_files": sources,
        "subjects": subjects,
        "grades_by_subject": grades_by_slug,
        "gaps": gaps,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = load_catalog(args.source_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
