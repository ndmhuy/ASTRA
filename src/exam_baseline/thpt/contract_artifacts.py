"""Publish paired, validated THPT 2026 artifacts from an existing UI job."""

import json
import re
from functools import cache
from hashlib import sha256
from importlib.resources import files
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock

import pypdfium2 as pdfium
import rfc8785
from jsonschema import Draft202012Validator

from exam_baseline.pipeline.rendering.compiler import compile_document
from exam_baseline.pipeline.rendering.syntax import validate_drawing_code
from exam_baseline.thpt.fonts import apply_font_profile

_PDFIUM_LOCK = Lock()

STUDENT = "student-paper.json"
TEACHER = "teacher-key.json"
SUBJECTS = frozenset({"english", "history", "geography", "chemistry", "biology"})
_MATH = re.compile(r"(\$\$[^$]+\$\$|\$[^$\n]+\$|\\\(.+?\\\)|\\\[.+?\\\])", re.S)
_BLANK = re.compile(r"(\(\d+\)\s*_{3,}|\n)")
_PREAMBLE_END = "\\begin{document}"
_FIGURE_PREAMBLE = rb"""\documentclass[12pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[T5]{fontenc}
\usepackage{amsmath,amssymb,tikz,pgfplots}
\usetikzlibrary{arrows.meta,positioning,patterns}
\pgfplotsset{compat=1.18}
"""


@cache
def schema() -> dict:
    return json.loads(
        files("exam_baseline.resources")
        .joinpath("contracts/ASTRA_THPT_2026_Contract.json")
        .read_text(encoding="utf-8-sig")
    )


def profile(format_id: str) -> dict | None:
    subject = format_id.removeprefix("thpt-")
    return schema()["x-profiles"][subject] if subject in SUBJECTS else None


def content_hash(paper: dict) -> str:
    return sha256(
        rfc8785.dumps({key: value for key, value in paper.items() if key != "contentHash"})
    ).hexdigest()


def rich(text: str, *, blanks: bool = False) -> list[dict]:
    runs = []
    for i, part in enumerate(_MATH.split(text)):
        if i % 2:
            trim = 1 if part.startswith("$") and not part.startswith("$$") else 2
            runs.append({"type": "math", "latex": part[trim:-trim].strip()})
        else:
            for segment in _BLANK.split(part):
                if not segment:
                    continue
                if segment == "\n":
                    runs.append({"type": "line_break"})
                elif blanks and _BLANK.fullmatch(segment):
                    runs.append({"type": "blank", "label": segment[1 : segment.index(")")]})
                else:
                    segment = re.sub(r"\\([%&#_{}])", r"\1", segment)
                    runs.extend(
                        {"type": "text", "text": segment[j : j + 5000]}
                        for j in range(0, len(segment), 5000)
                    )
    return runs


def blocks(text: str, *, blanks: bool = False) -> list[dict]:
    return [
        {"type": "paragraph", "runs": rich(paragraph, blanks=blanks)}
        for line in re.split(r"\n\s*\n", text)
        if (paragraph := line.strip())
    ]


def _key(question: dict, item_type: str, qid: str) -> dict:
    entry = {"questionId": qid, "type": item_type}
    explanation = blocks(question["solution"])
    if item_type == "true_false":
        statements = question["statements"]
        entry["answers"] = {
            letter: statement["answer"]
            for letter, statement in zip("abcd", statements, strict=True)
        }
        for letter, statement in zip("abcd", statements, strict=True):
            explanation.extend(blocks(f"{letter}) {statement['solution']}"))
    else:
        entry["answer"] = question["answer"]
    if explanation:
        entry["explanation"] = explanation
    return entry


def build_bundle(
    job: dict,
    spec: dict,
    group_specs,
    state_by_id: dict,
    figures: dict,
    section_instructions: dict[str, str],
) -> tuple[dict, dict]:
    subject = job["request"]["formatId"].removeprefix("thpt-")
    passages_by_group = {p["id"]: p for p in job.get("rawPassages", [])}
    passages = []
    for group, first, last, kind, instruction in group_specs:
        passage = passages_by_group.get(group)
        if passage is None and kind != "ordering":
            raise ValueError(f"Missing passage for English group {group}")
        passages.append(
            {
                "id": group.lower(),
                "sectionId": "P1",
                "questionRange": [first, last],
                "kind": kind,
                "instructions": rich(instruction),
                "blocks": blocks(passage["text"], blanks=kind == "cloze") if passage else [],
            }
        )

    questions = {q["id"]: q for q in job["rawQuestions"]}
    sections, entries = [], []
    for rule in spec["sections"]:
        section_id, item_type = rule["id"], rule["type"]
        section = {"id": section_id, "items": []}
        if section_id in section_instructions:
            section["instructions"] = rich(section_instructions[section_id])
        if rule.get("title"):
            section["title"] = rule["title"]
        for number in range(1, rule["count"] + 1):
            raw = questions[f"{section_id}-{number}"]
            qid = raw["id"].lower()
            group_ids = [
                p["id"]
                for p in passages
                if p["sectionId"] == section_id
                and p["questionRange"][0] <= number <= p["questionRange"][1]
            ]
            is_cloze = any(p["kind"] == "cloze" and p["id"] in group_ids for p in passages)
            placeholder = is_cloze and re.fullmatch(
                r"(?i)blank\s*\(\d+\)[.?!]?", raw["stem"].strip()
            )
            stem = [] if placeholder else blocks(raw["stem"])
            if asset := figures.get(qid):
                stem.append(
                    {
                        "type": "figure",
                        "assetId": asset["id"],
                        "alt": f"Minh họa câu {number} phần {section_id}.",
                    }
                )
            item = {
                "id": qid,
                "number": number,
                "type": item_type,
                "stem": stem,
                "passageIds": group_ids,
                "sourceIds": ["astra_original"],
                "verificationStatus": state_by_id[qid],
            }
            if item_type == "mcq":
                item["choices"] = {label: rich(raw["choices"][label]) for label in "ABCD"}
            elif item_type == "true_false":
                item["statements"] = {
                    letter: rich(statement["text"])
                    for letter, statement in zip("abcd", raw["statements"], strict=True)
                }
            else:
                # The existing live Composer only generates numeric short answers.
                item["responseKind"] = "numeric"
            section["items"].append(item)
            entries.append(_key(raw, item_type, qid))
        sections.append(section)

    binding = {"examId": f"exam-{job['jobId']}", "revision": job["revision"]}
    paper = {
        **binding,
        "schemaVersion": "astra-thpt-paper-v1",
        "examType": "THPT_STANDARD",
        "formatId": spec["formatId"],
        "formatVersion": spec["formatVersion"],
        "subject": subject,
        "grade": 12,
        "title": f"Đề {spec['displayName']} THPT",
        "durationMinutes": spec["durationMinutes"],
        "totalScore": 10,
        "sections": sections,
        "passages": passages,
        "assets": list(figures.values()),
        "sources": [
            {
                "id": "astra_original",
                "title": "Nội dung do ASTRA biên soạn",
                "locator": spec["formatId"],
            }
        ],
    }
    binding["contentHash"] = paper["contentHash"] = content_hash(paper)
    key = {**binding, "schemaVersion": "astra-thpt-teacher-key-v1", "entries": entries}
    return paper, key


@cache
def validators():
    contract = schema()
    return (
        Draft202012Validator(contract),
        Draft202012Validator({"$defs": contract["$defs"], "$ref": "#/$defs/teacherKey"}),
    )


def snapshot_path(directory: Path, revision: int, digest: str) -> Path:
    return directory / "_internal" / f"c{revision}-{digest[:16]}"


def write_bundle(directory: Path, paper: dict, key: dict) -> None:
    for validator, item in zip(validators(), (paper, key), strict=True):
        validator.validate(item)
    snapshot = snapshot_path(directory, paper["revision"], paper["contentHash"])
    snapshot.mkdir(parents=True, exist_ok=True)
    # API downloads use revision-specific files while the root pair serves integrations.
    for destination in (snapshot, directory):
        for filename, item in ((TEACHER, key), (STUDENT, paper)):
            temporary = destination / f".{filename}.tmp"
            temporary.write_text(
                json.dumps(item, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            temporary.replace(destination / filename)


def render_assets(
    directory: Path,
    drawings: list[dict],
    *,
    font_profile,
    compiler,
    timeout,
    cache_directory: Path,
) -> dict:
    if not drawings:
        return {}
    assets_dir = directory / "assets"
    assets_dir.mkdir(exist_ok=True)
    preamble = apply_font_profile(_FIGURE_PREAMBLE, font_profile).decode("utf-8")
    selected = {}
    missing = []
    for drawing in drawings:
        question_id, latex = drawing["question_id"].lower(), drawing["latex"]
        validate_drawing_code(latex)
        name = f"figure-{question_id}-{sha256((preamble + latex).encode()).hexdigest()[:12]}"
        target = assets_dir / f"{name}.png"
        selected[question_id] = (name, target)
        if not target.is_file():
            missing.append((target, latex))
    if missing:
        with TemporaryDirectory(dir=directory) as temp:
            src = Path(temp) / "figures.tex"
            src.write_text(
                preamble
                + r"\usepackage[active,tightpage]{preview}"
                + "\n"
                + r"\setlength\PreviewBorder{6pt}"
                + "\n"
                + _PREAMBLE_END
                + "\n"
                + "\n".join(r"\begin{preview}" + latex + r"\end{preview}" for _, latex in missing)
                + "\n"
                + r"\end{document}",
                encoding="utf-8",
            )
            compile_document(
                src, compiler=compiler, timeout=timeout, cache_directory=cache_directory
            )
            # PDFium calls are serialized, independent TeX compiler processes can overlap.
            with _PDFIUM_LOCK:
                document = pdfium.PdfDocument(src.with_suffix(".pdf"))
                try:
                    if len(document) != len(missing):
                        raise ValueError("Figure compiler produced an unexpected number of pages")
                    for index, (target, _) in enumerate(missing):
                        page = document[index]
                        bitmap = page.render(scale=2.5)
                        try:
                            scratch = src.parent / target.name
                            bitmap.to_pil().save(scratch)
                            scratch.replace(target)
                        finally:
                            bitmap.close()
                            page.close()
                finally:
                    document.close()
    return {
        qid: {
            "id": name,
            "path": f"assets/{path.name}",
            "mimeType": "image/png",
            "sha256": sha256(path.read_bytes()).hexdigest(),
        }
        for qid, (name, path) in selected.items()
    }
