"""Read the private staging snapshot locally without copying source data into Git."""

import csv
from dataclasses import replace
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile

from .models import CONFIG, CorpusDocument, Gap, RetrievalRequest, RetrievalResponse
from .query_parser import parse
from .results import collection_fingerprint, ranked_results

ALIASES = {"dli": "dia-li", "lsu": "lich-su", "ngv": "ngu-van", "tanh": "tieng-anh"}


def load_existing_corpus(ref="origin/staging/rag", repo=None):
    """Validate the snapshot boundary and report actionable source errors."""
    try:
        return _load_snapshot(ref, repo)
    except Gap:
        raise
    except OSError as exc:
        raise Gap("corpus_unavailable", f"Cannot read corpus snapshot: {exc}") from exc
    except (ValueError, KeyError, TypeError, AttributeError, tarfile.TarError) as exc:
        raise Gap("malformed_document", f"Invalid corpus snapshot: {exc}") from exc


def _load_snapshot(ref, repo):
    """Only index curriculum records and registry-listed usable paper text.

    Keys, profiles, model calls and audit files never enter the searchable view.
    Source metadata remains unchanged; internal search does not grant approval.
    """
    repo = Path(repo) if repo else Path(__file__).resolve().parents[1]

    def git(*args):
        result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
        if result.returncode:
            raise Gap("corpus_unavailable", result.stderr.decode("utf-8", errors="replace").strip())
        return result.stdout

    sha = git("rev-parse", "--verify", "--end-of-options", ref + "^{commit}").decode().strip()
    raw = git(
        "archive",
        "--format=tar",
        sha,
        "rag/data",
        "corpus/registry/papers.csv",
        "corpus/transcriptions",
    )
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        names = set(archive.getnames())

        def read(name):
            if name not in names:
                return ""
            member = archive.getmember(name)
            if not member.isfile():
                raise ValueError(f"Expected a regular source file: {name}")
            return archive.extractfile(member).read().decode("utf-8-sig")

        documents = []
        for name in sorted(names):
            if not name.startswith("rag/data/") or not name.endswith(".jsonl"):
                continue
            rows = [json.loads(line) for line in read(name).splitlines() if line.strip()]
            by_id = {row["unit_id"]: row for row in rows}
            if len(by_id) != len(rows):
                raise ValueError(f"Duplicate curriculum ids in {name}")
            for row in rows:
                source_subject = PurePosixPath(name).stem.rsplit("-", 1)[0]
                subject = ALIASES.get(source_subject, source_subject)
                if subject not in CONFIG["subjects"]:
                    raise ValueError(f"Unsupported curriculum subject in {name}")
                book = row.get("book")
                if book and book.get("series") not in CONFIG["corpus_series_aliases"]:
                    raise ValueError(f"Unsupported textbook series in {name}")
                # Resolve chapter through the explicit parent graph, never row position.
                chapter = None
                current, visited = row, set()
                while current:
                    if current["unit_id"] in visited:
                        raise ValueError(f"Curriculum parent cycle in {name}")
                    visited.add(current["unit_id"])
                    match = re.search(r"-c(\d+)$", current["unit_id"])
                    if match and current.get("kind") == "chương":
                        chapter = int(match[1])
                        break
                    parent = current.get("parent_id")
                    if parent and parent not in by_id:
                        raise ValueError(f"Missing curriculum parent in {name}")
                    current = by_id.get(parent)
                lesson_match = re.search(r"-b(\d+)$", row["unit_id"])
                phase = row.get("typical_phase") or {}
                semester = (
                    phase.get("semester")
                    if phase.get("provenance") not in (None, "assumed")
                    else None
                )
                text = row["title_vi"]
                if row.get("keywords_vi"):
                    text += "\n" + ", ".join(row["keywords_vi"])
                if row.get("outcomes_vi"):
                    text += "\n" + json.dumps(row["outcomes_vi"], ensure_ascii=False)
                documents.append(
                    CorpusDocument(
                        document_id=row["unit_id"],
                        subject=subject,
                        grade=row["grade"],
                        chapter=chapter,
                        lesson=int(lesson_match[1]) if lesson_match else None,
                        semester=semester,
                        title=row["title_vi"],
                        content=text,
                        content_kind="curriculum",
                        source_locator=f"{name}#{row['unit_id']}",
                        source_version=sha,
                        approval_status=row["status"],
                        evidence_class="third_party",
                        provenance=row,
                    )
                )

        reader = csv.DictReader(io.StringIO(read("corpus/registry/papers.csv")))
        required = {"subject", "class", "path", "usable_as_content_evidence"}
        if not required.issubset(reader.fieldnames or ()):
            raise ValueError("Paper registry is missing required columns.")
        registry = list(reader)
        excluded = 0
        for row in registry:
            path = "corpus/" + row["path"]
            if row["usable_as_content_evidence"].lower() != "true" or row["class"] not in (
                "official",
                "provincial_third_party",
            ):
                excluded += 1
                continue
            if (
                not path.startswith("corpus/transcriptions/")
                or not path.endswith("/de.md")
                or path not in names
            ):
                raise ValueError(f"Invalid or missing registry transcription: {path}")
            parent = str(PurePosixPath(path).parent)
            provenance = dict(registry=row, status_note=read(parent + "/STATUS.md"))
            source = read(parent + "/source.json")
            if source:
                provenance["source"] = json.loads(source)
            documents.append(
                CorpusDocument(
                    document_id="paper-" + hashlib.sha256(path.encode()).hexdigest()[:20],
                    subject=row["subject"],
                    grade=None,
                    chapter=None,
                    lesson=None,
                    semester=None,
                    title=str(PurePosixPath(path).parent).removeprefix("corpus/transcriptions/"),
                    content=read(path),
                    content_kind="exam",
                    source_locator=path,
                    source_version=sha,
                    approval_status="ocr-draft",
                    evidence_class="third_party",
                    provenance=provenance,
                )
            )
    ids = [d.document_id for d in documents]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate corpus document ids")
    corpus_hash = collection_fingerprint(documents)
    return documents, {
        "snapshot": sha,
        "corpus_sha256": corpus_hash,
        "ref": ref,
        "curriculum_rows": sum(d.content_kind == "curriculum" for d in documents),
        "exam_papers": sum(d.content_kind == "exam" for d in documents),
        "excluded_papers": excluded,
        "registry_papers": len(registry),
        "mode": "internal prototype; approval unchanged",
    }


def search_existing(payload, documents, snapshot, corpus_sha256=None):
    response = RetrievalResponse(corpus_snapshot=snapshot)
    response.corpus_sha256 = corpus_sha256 or collection_fingerprint(documents)
    try:
        if not isinstance(payload, dict):
            raise Gap("invalid_request", "Request must be a JSON object.")
        request_data = dict(payload)
        kind = request_data.pop("collection", "curriculum")
        if kind not in ("curriculum", "exam"):
            raise Gap("invalid_request", "Choose curriculum or exam search.")
        if request_data.get("mode") is None:
            request_data.pop("mode", None)
        try:
            request = RetrievalRequest(**request_data)
        except TypeError as exc:
            raise Gap("invalid_request", "Unknown or missing request fields.") from exc
        response.mode = request.mode
        response.ranking_method = CONFIG.get("ranking_versions", {}).get(
            request.mode, CONFIG["ranking_version"]
        )
        scope = parse(request, require_grade=kind != "exam")
        if kind == "exam":
            scope = replace(scope, series=None)
        response.resolved_scope = scope
        if kind == "exam" and (scope.grade is not None or scope.range_type != "topic"):
            raise Gap(
                "unmapped_exam_scope",
                "Exam passages have no verified grade/chapter mappings. Search by subject and topic without a grade; use Curriculum for exact lesson ranges.",
            )
        eligible = [d for d in documents if d.content_kind == kind and d.subject == scope.subject]
        if scope.grade is not None:
            eligible = [d for d in eligible if d.grade == scope.grade]
        if scope.range_type != "topic":
            eligible = [
                d
                for d in eligible
                if getattr(d, scope.range_type) is not None
                and scope.start <= getattr(d, scope.range_type) <= scope.end
            ]
        if scope.edition:
            eligible = [d for d in eligible if d.edition == scope.edition]
        if not eligible:
            raise Gap("no_documents_in_scope", "No existing corpus documents match this scope.")
        response.documents = ranked_results(
            eligible,
            scope.keywords,
            request.top_k,
            mode=request.mode,
            accented=scope.accented_keywords,
        )
        response.status = "success"
    except Gap as exc:
        response.gaps.append({"code": exc.code, "message": str(exc)})
    return response
