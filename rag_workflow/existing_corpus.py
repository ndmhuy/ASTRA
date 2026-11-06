"""Read the private staging snapshot locally without copying source data into Git."""
import csv
from dataclasses import asdict, dataclass
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile

from .models import CONFIG, Gap, RetrievalRequest, RetrievalResponse
from .query_parser import parse
from .search_index import PassageIndex

ALIASES = {"dli": "dia-li", "lsu": "lich-su", "ngv": "ngu-van", "tanh": "tieng-anh"}


@dataclass(frozen=True)
class CorpusDocument:
    document_id: str
    subject: str
    grade: int | None
    chapter: int | None
    lesson: int | None
    semester: int | None
    title: str
    content: str
    content_kind: str
    source_locator: str
    source_version: str
    approval_status: str
    evidence_class: str
    provenance: dict
    edition: str = "existing-corpus"
    schema_version: str = "1.0"

    @property
    def content_sha256(self):
        return hashlib.sha256(self.content.encode("utf-8")).hexdigest()


def load_existing_corpus(ref="origin/staging/rag", repo=None):
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
    raw = git("archive", "--format=tar", sha, "rag/data", "corpus/registry/papers.csv", "corpus/transcriptions")
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        names = set(archive.getnames())

        def read(name):
            if name not in names:
                return ""
            return archive.extractfile(name).read().decode("utf-8-sig")

        documents = []
        for name in sorted(names):
            if not name.startswith("rag/data/") or not name.endswith(".jsonl"):
                continue
            rows = [json.loads(line) for line in read(name).splitlines() if line.strip()]
            by_id = {row["unit_id"]: row for row in rows}
            if len(by_id) != len(rows):
                raise ValueError(f"Duplicate curriculum ids in {name}")
            for row in rows:
                subject = ALIASES.get(name.split("/")[-1].rsplit("-", 1)[0], name.split("/")[-1].rsplit("-", 1)[0])
                if subject not in CONFIG["subjects"]:
                    raise ValueError(f"Unsupported curriculum subject in {name}")
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
                text = row["title_vi"]
                if row.get("keywords_vi"):
                    text += "\n" + ", ".join(row["keywords_vi"])
                if row.get("outcomes_vi"):
                    text += "\n" + json.dumps(row["outcomes_vi"], ensure_ascii=False)
                documents.append(CorpusDocument(
                    row["unit_id"], subject, row["grade"], chapter,
                    int(lesson_match[1]) if lesson_match else None,
                    (row.get("typical_phase") or {}).get("semester"), row["title_vi"], text,
                    "curriculum", f"{name}#{row['unit_id']}", sha, row["status"], "third_party", row))

        registry = list(csv.DictReader(io.StringIO(read("corpus/registry/papers.csv"))))
        excluded = 0
        for row in registry:
            path = "corpus/" + row["path"]
            if (row["usable_as_content_evidence"].lower() != "true"
                    or row["class"] not in ("official", "provincial_third_party")):
                excluded += 1
                continue
            if not path.startswith("corpus/transcriptions/") or not path.endswith("/de.md") or path not in names:
                raise ValueError(f"Invalid or missing registry transcription: {path}")
            parent = str(PurePosixPath(path).parent)
            provenance = dict(registry=row, status_note=read(parent + "/STATUS.md"))
            source = read(parent + "/source.json")
            if source:
                provenance["source"] = json.loads(source)
            documents.append(CorpusDocument(
                "paper-" + hashlib.sha256(path.encode()).hexdigest()[:20], row["subject"],
                None, None, None, None, str(PurePosixPath(path).parent).removeprefix("corpus/transcriptions/"),
                read(path), "exam", path, sha, "ocr-draft", "third_party", provenance))
    ids = [d.document_id for d in documents]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate corpus document ids")
    return documents, {"snapshot": sha, "ref": ref, "curriculum_rows": sum(d.content_kind == "curriculum" for d in documents),
                       "exam_papers": sum(d.content_kind == "exam" for d in documents), "excluded_papers": excluded,
                       "registry_papers": len(registry), "mode": "internal prototype; approval unchanged"}


def search_existing(payload, documents, snapshot):
    response = RetrievalResponse(corpus_sha256=snapshot)
    try:
        request_data = dict(payload)
        kind = request_data.pop("collection", "curriculum")
        if kind not in ("curriculum", "exam"):
            raise Gap("invalid_request", "Choose curriculum or exam search.")
        try:
            request = RetrievalRequest(**request_data)
        except TypeError as exc:
            raise Gap("invalid_request", "Unknown or missing request fields.") from exc
        scope = parse(request, require_grade=kind != "exam")
        response.resolved_scope = scope
        if kind == "exam" and (scope.grade is not None or scope.range_type != "topic"):
            raise Gap("unmapped_exam_scope", "Exam passages have no verified grade/chapter mappings. Search by subject and topic without a grade; use Curriculum for exact lesson ranges.")
        eligible = [d for d in documents if d.content_kind == kind and d.subject == scope.subject]
        if scope.grade is not None:
            eligible = [d for d in eligible if d.grade == scope.grade]
        if scope.range_type != "topic":
            eligible = [d for d in eligible if getattr(d, scope.range_type) is not None
                        and scope.start <= getattr(d, scope.range_type) <= scope.end]
        if scope.edition:
            eligible = [d for d in eligible if d.edition == scope.edition]
        if not eligible:
            raise Gap("no_documents_in_scope", "No existing corpus documents match this scope.")
        seen = set()
        for score, document, passage, matched in PassageIndex(eligible).ranked(scope.keywords):
            if document.content_sha256 in seen:
                continue
            seen.add(document.content_sha256)
            hit = asdict(document)
            hit.pop("content")
            hit.update(content_sha256=document.content_sha256, source_id=document.document_id,
                       excerpt=passage.text[:CONFIG["excerpt_chars"]], excerpt_start=passage.start,
                       excerpt_end=min(passage.end, passage.start + CONFIG["excerpt_chars"]),
                       passage_id=f"{document.document_id}:{passage.start}-{passage.end}",
                       passage_start=passage.start, passage_end=passage.end,
                       relevance_score=round(score, 6), matched_terms=matched,
                       ranking_method=CONFIG["ranking_version"], usage="internal prototype; not teacher-approved")
            response.documents.append(hit)
            if len(response.documents) == request.top_k:
                break
        if not response.documents:
            raise Gap("no_relevant_match", "No matching topic terms in this collection.")
        response.status = "success"
    except Gap as exc:
        response.gaps.append({"code": exc.code, "message": str(exc)})
    return response
