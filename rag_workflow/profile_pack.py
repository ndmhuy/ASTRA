"""Load, verify, cache-invalidate, and export research topic-pack releases (Toán THPT)."""

import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile
from typing import Any

from .models import CONFIG, CorpusDocument, Gap
from .query_parser import normalize

PART_KIND_TO_PART = {
    "multiple_choice": "P1",
    "mcq": "P1",
    "true_false": "P2",
    "tf": "P2",
    "short_answer": "P3",
    "sa": "P3",
}

_RELEASE_CACHE: dict[tuple[str, str], dict[str, Any]] = {}

_GENERIC_LINK_UNIGRAMS = frozenset(
    {
        "toan",
        "bai",
        "cau",
        "phan",
        "muc",
        "do",
        "tim",
        "tinh",
        "cho",
        "biet",
        "xac",
        "dinh",
        "gia",
        "tri",
        "cua",
        "trong",
        "tren",
        "voi",
        "mot",
        "hai",
        "ba",
        "bon",
        "cac",
        "va",
        "hoac",
        "khi",
        "theo",
        "tu",
        "den",
        "ung",
        "dung",
        "co",
        "ban",
        "thuc",
        "te",
        "tien",
        "cong",
        "quy",
        "tac",
        "nghia",
        "chat",
        "dang",
        "so",
        "ham",
        "phuong",
        "trinh",
        "he",
        "giai",
        "quyet",
        "van",
        "de",
        "lien",
        "quan",
        "su",
        "bieu",
        "dien",
        "mo",
        "ta",
        "nhan",
        "duoc",
        "nhung",
        "nhieu",
        "buoc",
        "bang",
        "tuong",
        "doi",
        "giua",
        "hinh",
        "hoc",
        "cach",
        "khai",
        "niem",
        "phep",
        "bien",
        "lap",
        "viet",
        "xet",
        "dieu",
        "kien",
        "tong",
        "hieu",
        "thuong",
        "don",
        "gian",
        "chi",
        "tiet",
        "sanh",
        "uoc",
        "luong",
        "kiem",
        "tra",
        "hoat",
        "trai",
        "nghiem",
        "tap",
        "cuoi",
        "nam",
        "on",
        "trung",
        "tam",
        "phang",
        "diem",
        "duong",
        "mat",
        "khong",
        "gian",
        "goc",
        "dai",
        "canh",
        "loai",
        "truong",
        "hop",
        "chinh",
        "sau",
        "day",
        "nay",
        "nhau",
        "nhu",
        "nho",
        "lon",
        "nhat",
        "bac",
        "cap",
    }
)

_GENERIC_LINK_BIGRAMS = frozenset(
    {
        "bai toan",
        "cong thuc",
        "gia tri",
        "phuong trinh",
        "phuong phap",
        "ung dung",
        "thuc tien",
        "thuc te",
        "mot so",
        "van de",
        "lien quan",
        "giai quyet",
        "cua ham",
        "cua mot",
        "cac phep",
        "phep toan",
        "quy tac",
        "dinh nghia",
        "tinh chat",
        "co ban",
        "ham so",
        "trong mat",
        "trong khong",
        "giai bai",
        "de giai",
        "xac dinh",
        "tinh gia",
        "bien thien",
        "dieu kien",
    }
)


def _link_tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", normalize(text))


def _link_bigrams(tokens: list[str]) -> set[str]:
    return {f"{tokens[i]} {tokens[i + 1]}" for i in range(len(tokens) - 1)}


def _has_phrase(phrase: str, haystack: str) -> bool:
    if len(phrase) < 4:
        return False
    return bool(re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", haystack))


def _is_core_curriculum_lesson(row: dict[str, Any]) -> bool:
    if row.get("kind") == "chương":
        return False
    uid = str(row.get("unit_id") or "")
    if uid.endswith(("-btcc", "-cuoi-nam")) or "-hd" in uid:
        return False
    return True


def _link_curriculum_units(
    display_topic: str,
    topic_key: str,
    raw_topics: list[str],
    grades: list[int],
    curriculum_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Link a Topic Pack to verified curriculum lessons using domain phrases and bigrams."""
    stop_unigrams = set(CONFIG["stop_words"]) | _GENERIC_LINK_UNIGRAMS
    disp_norm = normalize(display_topic)
    pack_norm = normalize(" ".join([display_topic, topic_key.replace("-", " "), *raw_topics]))

    disp_toks = _link_tokens(disp_norm)
    pack_toks = _link_tokens(pack_norm)
    disp_bi = _link_bigrams(disp_toks) - _GENERIC_LINK_BIGRAMS
    pack_bi = _link_bigrams(pack_toks) - _GENERIC_LINK_BIGRAMS
    disp_uni = {w for w in disp_toks if (len(w) >= 3 or w == "mu") and w not in stop_unigrams}
    pack_uni = {w for w in pack_toks if (len(w) >= 3 or w == "mu") and w not in stop_unigrams}

    scored: list[tuple[float, float, dict[str, Any]]] = []
    fallback: list[tuple[float, dict[str, Any]]] = []
    for crow in curriculum_rows:
        if not _is_core_curriculum_lesson(crow):
            continue
        c_title = re.sub(r"^(?:bai|chuong)\s+\d+\s*[.:]\s*", "", normalize(crow["title"])).strip()
        c_chap = re.sub(
            r"^(?:chuong)\s+(?:\d+|[ivx]+)\s*[.:]\s*",
            "",
            normalize(str(crow.get("chapter_title") or "")),
        ).strip()
        c_kw_norms = [normalize(k).strip() for k in crow.get("keywords_vi") or [] if str(k).strip()]
        c_core_norm = f"{c_title} {' '.join(c_kw_norms)}".strip()
        c_out_norm = normalize(" ".join(str(x) for x in crow.get("outcomes_vi") or []))

        title_toks = _link_tokens(c_title)
        chap_toks = _link_tokens(c_chap)
        core_toks = _link_tokens(c_core_norm)
        title_bi = _link_bigrams(title_toks) - _GENERIC_LINK_BIGRAMS
        chap_bi = _link_bigrams(chap_toks) - _GENERIC_LINK_BIGRAMS
        core_bi = _link_bigrams(core_toks) - _GENERIC_LINK_BIGRAMS
        title_uni = {w for w in title_toks if (len(w) >= 3 or w == "mu") and w not in stop_unigrams}
        core_uni = {w for w in core_toks if (len(w) >= 3 or w == "mu") and w not in stop_unigrams}

        phrase_score = 0.0
        if _has_phrase(c_title, disp_norm) or _has_phrase(disp_norm, c_title):
            phrase_score += 12.0
        elif _has_phrase(c_title, pack_norm):
            phrase_score += 7.0
        if c_chap and (_has_phrase(c_chap, disp_norm) or _has_phrase(disp_norm, c_chap)):
            phrase_score += 6.0
        kw_disp_hits = sum(1 for kw in c_kw_norms if _has_phrase(kw, disp_norm))
        kw_pack_hits = sum(1 for kw in c_kw_norms if _has_phrase(kw, pack_norm))
        phrase_score += min(12.0, 5.0 * kw_disp_hits) + min(8.0, 2.5 * kw_pack_hits)

        bi_score = (
            5.0 * len(disp_bi & title_bi)
            + 3.0 * len(disp_bi & core_bi)
            + 4.0 * len(disp_bi & chap_bi)
            + 1.5 * len(pack_bi & core_bi)
        )
        uni_score = (
            3.0 * len(disp_uni & title_uni)
            + 1.5 * len(disp_uni & core_uni)
            + 0.75 * len(pack_uni & core_uni)
        )
        domain_score = phrase_score + bi_score + uni_score

        out_bi = _link_bigrams(_link_tokens(c_out_norm)) - _GENERIC_LINK_BIGRAMS
        out_uni = {
            w for w in _link_tokens(c_out_norm) if (len(w) >= 3 or w == "mu") and w not in stop_unigrams
        }
        out_bonus = min(3.0, 0.75 * len(pack_bi & out_bi) + 0.3 * len(disp_uni & out_uni))
        if not grades or crow["grade"] in grades:
            grade_bonus = 2.5
        elif grades == [12] and crow["grade"] == 10:
            grade_bonus = -3.0
        else:
            grade_bonus = -0.5

        if domain_score >= 3.5:
            scored.append((domain_score + out_bonus + grade_bonus, domain_score, crow))
        else:
            fb_score = (
                2.0 * len(disp_bi & out_bi)
                + 1.0 * len(pack_bi & out_bi)
                + 0.5 * len(pack_uni & out_uni)
            )
            if fb_score >= 1.5:
                fallback.append((fb_score + grade_bonus, crow))

    if scored:
        scored.sort(key=lambda item: (-item[0], -item[1], item[2]["grade"], item[2]["unit_id"]))
        top_domain = scored[0][1]
        cutoff = max(3.5, min(14.0, top_domain * 0.35))
        filtered = [item for item in scored if item[1] >= cutoff]
        return [item[2] for item in filtered[:6]]

    fallback.sort(key=lambda item: (-item[0], item[1]["grade"], item[1]["unit_id"]))
    return [item[1] for item in fallback[:3]]


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _verify_sha256(data: bytes, expected_hex: str) -> tuple[bool, str]:
    """Verify SHA-256, tolerating Windows CRLF conversion if exact LF bytes match."""
    actual = _sha256_bytes(data)
    if actual == expected_hex:
        return True, actual
    lf_data = data.replace(b"\r\n", b"\n")
    lf_sha = _sha256_bytes(lf_data)
    if lf_sha == expected_hex:
        return True, lf_sha
    return False, actual


def _load_raw_files_from_git(subject: str, ref: str, repo: Path) -> tuple[str, dict[str, bytes]]:
    def git(*args: str) -> bytes:
        res = subprocess.run(
            ["git", "-c", "core.autocrlf=false", "-C", str(repo), *args],
            capture_output=True,
        )
        if res.returncode != 0:
            err = res.stderr.decode("utf-8", errors="replace").strip()
            raise Gap("corpus_unavailable", f"Git snapshot error ({ref}): {err}")
        return res.stdout

    sha = (
        git("rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}")
        .decode("utf-8")
        .strip()
    )
    archive_paths = [
        "rag/data",
        f"corpus/profiles/{subject}",
        f"corpus/audit/outputs/matrix-mapping/{subject}.json",
        "corpus/audit/outputs/defaults-snapshot.json",
    ]
    raw_tar = git("archive", "--format=tar", sha, *archive_paths)
    files: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(raw_tar)) as archive:
        for member in archive.getmembers():
            if member.isfile():
                extracted = archive.extractfile(member)
                if extracted is not None:
                    files[member.name] = extracted.read()
    return sha, files


def _load_raw_files_from_dir(subject: str, pack_dir: Path) -> tuple[str, dict[str, bytes]]:
    pack_dir = Path(pack_dir).resolve()
    if not pack_dir.is_dir():
        raise Gap("corpus_unavailable", f"Release pack directory does not exist: {pack_dir}")
    files: dict[str, bytes] = {}
    for p in sorted(pack_dir.rglob("*")):
        if p.is_file():
            rel = p.relative_to(pack_dir).as_posix()
            files[rel] = p.read_bytes()
    manifest_raw = files.get("manifest.json")
    if manifest_raw:
        try:
            manifest = json.loads(manifest_raw.decode("utf-8"))
            snap = str(manifest.get("corpus_snapshot") or "local-pack")
        except (ValueError, KeyError):
            snap = "local-pack"
    else:
        snap = "local-pack"
    return snap, files


def _parse_curriculum_rows(
    files: dict[str, bytes], subject: str, snapshot_sha: str
) -> tuple[list[dict[str, Any]], list[CorpusDocument], str]:
    curriculum_rows: list[dict[str, Any]] = []
    corpus_docs: list[CorpusDocument] = []
    hasher = hashlib.sha256()

    prefix = f"rag/data/{subject}-"
    matching_names = sorted(
        name for name in files if name.startswith(prefix) and name.endswith(".jsonl")
    )
    if not matching_names:
        raise Gap("corpus_unavailable", f"No curriculum JSONL files found for subject {subject!r}.")

    for name in matching_names:
        raw_bytes = files[name].replace(b"\r\n", b"\n")
        hasher.update(
            name.encode("utf-8") + b"\0" + _sha256_bytes(raw_bytes).encode("ascii") + b"\n"
        )
        text_content = raw_bytes.decode("utf-8-sig")
        rows = [json.loads(line) for line in text_content.splitlines() if line.strip()]
        by_id = {row["unit_id"]: row for row in rows}
        for row in rows:
            chapter = None
            chapter_title = None
            current, visited = row, set()
            while current:
                if current["unit_id"] in visited:
                    break
                visited.add(current["unit_id"])
                match = re.search(r"-c(\d+)$", current["unit_id"])
                if match and current.get("kind") == "chương":
                    chapter = int(match[1])
                    chapter_title = current.get("title_vi")
                    break
                parent = current.get("parent_id")
                current = by_id.get(parent) if parent else None
            lesson_match = re.search(r"-b(\d+)$", row["unit_id"])
            lesson = int(lesson_match[1]) if lesson_match else None
            phase = row.get("typical_phase") or {}
            semester = (
                phase.get("semester") if phase.get("provenance") not in (None, "assumed") else None
            )
            locator = f"{name}#{row['unit_id']}"
            doc_text = row["title_vi"]
            if row.get("keywords_vi"):
                doc_text += "\n" + ", ".join(row["keywords_vi"])
            if row.get("outcomes_vi"):
                doc_text += "\n" + json.dumps(row["outcomes_vi"], ensure_ascii=False)
            enriched = {
                "unit_id": row["unit_id"],
                "subject": subject,
                "grade": int(row["grade"]),
                "chapter": chapter,
                "chapter_title": chapter_title,
                "lesson": lesson,
                "semester": semester,
                "kind": row.get("kind"),
                "title": row["title_vi"],
                "keywords_vi": list(row.get("keywords_vi") or []),
                "outcomes_vi": row.get("outcomes_vi") or [],
                "source_id": row["unit_id"],
                "source_locator": locator,
                "source_version": snapshot_sha,
                "approval_status": row.get("status", "draft"),
                "evidence_class": "curriculum",
                "book": row.get("book") or {},
            }
            curriculum_rows.append(enriched)
            corpus_docs.append(
                CorpusDocument(
                    document_id=row["unit_id"],
                    subject=subject,
                    grade=int(row["grade"]),
                    chapter=chapter,
                    lesson=lesson,
                    semester=semester,
                    title=row["title_vi"],
                    content=doc_text,
                    content_kind="curriculum",
                    source_locator=locator,
                    source_version=snapshot_sha,
                    approval_status=row.get("status", "draft"),
                    evidence_class="third_party",
                    provenance=row,
                )
            )
    return curriculum_rows, corpus_docs, hasher.hexdigest()


def _extract_common_mistakes(
    patterns_by_class: dict[str, list[dict[str, Any]]],
    observations: list[dict[str, Any]],
    examples: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Aggregate distractor mechanisms and common mistakes with provenance."""
    mistakes: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for ev_class, pat_list in (patterns_by_class or {}).items():
        for pat in pat_list:
            mapped_part = PART_KIND_TO_PART.get(pat.get("part_kind", ""), pat.get("part_kind"))
            wo = pat.get("wrong_options")
            if wo and isinstance(wo, str) and wo.strip():
                key = ("pattern", wo.strip())
                if key not in seen:
                    seen.add(key)
                    mistakes.append(
                        {
                            "source_type": "pattern_wrong_options",
                            "part": mapped_part,
                            "topic": pat.get("topic"),
                            "mistake_kind": "Cơ chế nhiễu theo dạng bài",
                            "detail": wo.strip(),
                            "evidence_class": ev_class,
                            "refs": list(pat.get("refs") or []),
                        }
                    )
            elif mapped_part == "P3" and pat.get("difficulty_source"):
                ds = str(pat["difficulty_source"]).strip()
                key = ("p3_pattern_trap", ds)
                if ds and key not in seen:
                    seen.add(key)
                    mistakes.append(
                        {
                            "source_type": "p3_pattern_difficulty_trap",
                            "part": "P3",
                            "topic": pat.get("topic"),
                            "mistake_kind": "Bẫy mô hình hóa & điều kiện P3",
                            "detail": ds,
                            "evidence_class": ev_class,
                            "refs": list(pat.get("refs") or []),
                        }
                    )

    for obs in observations:
        wo = obs.get("wrong_options")
        if wo and isinstance(wo, str) and wo.strip():
            key = ("obs_summary", wo.strip())
            if key not in seen:
                seen.add(key)
                mistakes.append(
                    {
                        "source_type": "observation_wrong_options",
                        "part": obs.get("part"),
                        "topic": obs.get("topic"),
                        "mistake_kind": "Lỗi sai quan sát từ câu nguồn",
                        "detail": wo.strip(),
                        "evidence_class": obs.get("evidence_class"),
                        "refs": [obs.get("ref")] if obs.get("ref") else [],
                    }
                )
        elif obs.get("part") == "P3" and obs.get("difficulty_source"):
            ds = str(obs["difficulty_source"]).strip()
            key = ("p3_obs_trap", ds)
            if ds and key not in seen:
                seen.add(key)
                mistakes.append(
                    {
                        "source_type": "p3_observation_difficulty_trap",
                        "part": "P3",
                        "topic": obs.get("topic"),
                        "mistake_kind": "Điểm dễ sai khi giải tự luận ngắn P3",
                        "detail": ds,
                        "evidence_class": obs.get("evidence_class"),
                        "refs": [obs.get("ref")] if obs.get("ref") else [],
                    }
                )
        for detail in obs.get("wrong_option_details") or []:
            mk = str(detail.get("mistake_kind") or "Phương án nhiễu").strip()
            rs = str(detail.get("reason") or "").strip()
            if rs:
                key = (mk, rs)
                if key not in seen:
                    seen.add(key)
                    mistakes.append(
                        {
                            "source_type": "observation_distractor_detail",
                            "part": obs.get("part"),
                            "topic": obs.get("topic"),
                            "option_label": detail.get("label"),
                            "mistake_kind": mk,
                            "detail": rs,
                            "evidence_class": obs.get("evidence_class"),
                            "refs": [obs.get("ref")] if obs.get("ref") else [],
                        }
                    )

    for ex in examples:
        sample = ex.get("sample") or {}
        target = ex.get("target") or {}
        for dist in sample.get("distractors") or []:
            mk = str(dist.get("mistake") or "Lỗi sai mẫu").strip()
            why = str(dist.get("why_plausible") or "").strip()
            combined = f"{mk} ({why})" if why else mk
            key = ("example_distractor", combined)
            if key not in seen:
                seen.add(key)
                mistakes.append(
                    {
                        "source_type": "synthetic_example_distractor",
                        "part": target.get("part"),
                        "level": target.get("level"),
                        "topic": target.get("topic"),
                        "option_label": dist.get("label"),
                        "mistake_kind": mk,
                        "detail": why or mk,
                        "evidence_class": "synthetic",
                        "example_id": sample.get("id") or target.get("id"),
                    }
                )
    return mistakes


def load_profile_release(
    subject: str = "toan",
    ref: str = "origin/staging/rag",
    repo: Path | None = None,
    pack_dir: Path | None = None,
    force_rebuild: bool = False,
) -> dict[str, Any]:
    """Load and cryptographically verify the subject profile bundle, topic packs, and curriculum.

    Automatically invalidates the cached release whenever the corpus snapshot, bundle hash,
    topic pack hashes, or config hash change.
    """
    repo_root = Path(repo) if repo else Path(__file__).resolve().parents[1]
    if pack_dir is not None:
        snapshot_sha, files = _load_raw_files_from_dir(subject, Path(pack_dir))
        source_mode = f"pack_dir:{Path(pack_dir).resolve().as_posix()}"
    else:
        snapshot_sha, files = _load_raw_files_from_git(subject, ref, repo_root)
        source_mode = f"git:{ref}"

    profile_prefix = f"corpus/profiles/{subject}"
    bundle_path = f"{profile_prefix}/profile.bundle.json"
    if bundle_path not in files:
        raise Gap("corpus_unavailable", f"Missing {bundle_path} in {source_mode}.")

    bundle_bytes = files[bundle_path].replace(b"\r\n", b"\n")
    bundle_sha256 = _sha256_bytes(bundle_bytes)
    bundle = json.loads(bundle_bytes.decode("utf-8"))
    if bundle.get("schema_version") != CONFIG["profile_schema_version"]:
        raise Gap(
            "unsupported_schema",
            f"Unsupported profile bundle schema: {bundle.get('schema_version')!r}.",
        )

    completion_path = f"{profile_prefix}/completion.json"
    completion_bytes = files.get(completion_path, b"{}").replace(b"\r\n", b"\n")
    completion_sha256 = _sha256_bytes(completion_bytes)
    completion = json.loads(completion_bytes.decode("utf-8"))

    levels_path = f"{profile_prefix}/levels.json"
    levels_bytes = files.get(levels_path, b"{}").replace(b"\r\n", b"\n")
    levels_sha256 = _sha256_bytes(levels_bytes)
    levels_doc = json.loads(levels_bytes.decode("utf-8"))

    verification_path = f"{profile_prefix}/verification.json"
    verification_bytes = files.get(verification_path, b"{}").replace(b"\r\n", b"\n")
    verification_doc = json.loads(verification_bytes.decode("utf-8"))

    curriculum_rows, curriculum_docs, curriculum_sha256 = _parse_curriculum_rows(
        files, subject, snapshot_sha
    )

    # Verify every topic pack SHA-256 before computing the release fingerprint.
    topic_hasher = hashlib.sha256()
    raw_topic_packs: list[tuple[dict[str, Any], dict[str, Any], str]] = []
    for entry in bundle.get("topic_packs", []):
        rel_tp_path = f"{profile_prefix}/{entry['path']}"
        if rel_tp_path not in files:
            raise Gap("malformed_document", f"Missing topic pack file: {rel_tp_path}")
        tp_bytes = files[rel_tp_path]
        ok, verified_sha = _verify_sha256(tp_bytes, entry["sha256"])
        if not ok:
            raise Gap(
                "malformed_document",
                f"SHA-256 mismatch for {rel_tp_path}: expected {entry['sha256']}, got {verified_sha}",
            )
        topic_hasher.update(f"{entry['path']}:{verified_sha}\n".encode("ascii"))
        tp_obj = json.loads(tp_bytes.decode("utf-8"))
        if tp_obj.get("schema_version") != CONFIG["topic_pack_schema_version"]:
            raise Gap(
                "unsupported_schema",
                f"Unsupported topic pack schema in {rel_tp_path}: {tp_obj.get('schema_version')!r}",
            )
        raw_topic_packs.append((entry, tp_obj, verified_sha))

    config_sha256 = _sha256_bytes(
        json.dumps(CONFIG, sort_keys=True, ensure_ascii=False).encode("utf-8")
    )
    fingerprint_payload = json.dumps(
        {
            "snapshot_sha": snapshot_sha,
            "subject": subject,
            "bundle_sha256": bundle_sha256,
            "completion_sha256": completion_sha256,
            "levels_sha256": levels_sha256,
            "curriculum_sha256": curriculum_sha256,
            "topics_tree_sha256": topic_hasher.hexdigest(),
            "config_sha256": config_sha256,
        },
        sort_keys=True,
    ).encode("utf-8")
    release_fingerprint = _sha256_bytes(fingerprint_payload)

    cache_key = (source_mode, subject)
    cached = _RELEASE_CACHE.get(cache_key)
    if not force_rebuild and cached and cached["release_fingerprint"] == release_fingerprint:
        cached["cache_hit"] = True
        return cached

    # Map source_evidence by paper_id (12-char hash prefix or path stem) for provenance enrichment.
    source_by_class: dict[str, list[dict[str, Any]]] = {
        "official": [],
        "provincial_third_party": [],
    }
    for src in bundle.get("source_evidence", []):
        cls = src.get("class", "provincial_third_party")
        source_by_class.setdefault(cls, []).append(src)

    mapping_path = f"corpus/audit/outputs/matrix-mapping/{subject}.json"
    topic_mapping_entries = []
    if mapping_path in files:
        topic_mapping_entries = json.loads(files[mapping_path].decode("utf-8")).get(
            "topic_mapping", []
        )

    defaults_path = "corpus/audit/outputs/defaults-snapshot.json"
    defaults_snapshot = {}
    if defaults_path in files:
        defaults_snapshot = json.loads(files[defaults_path].decode("utf-8"))

    # Assemble rich topic packs with joined observations, examples, mistakes, and curriculum links.
    topic_packs_by_id: dict[str, dict[str, Any]] = {}
    topic_key_to_id: dict[str, str] = {}
    norm_name_to_id: dict[str, str] = {}

    for entry, tp_obj, verified_sha in raw_topic_packs:
        tp_id = PurePosixPath(entry["path"]).stem
        topic_meta = tp_obj["topic"]
        topic_key = entry["topic_key"]
        display_topic = topic_meta.get("display_topic") or entry["topic"]
        locator = f"{profile_prefix}/{entry['path']}#{tp_id}"

        grades = sorted(int(g) for g in (topic_meta.get("grades") or []) if str(g).isdigit())
        level_by_ref = {
            la["ref"]: la for la in (tp_obj.get("level_assignments") or []) if "ref" in la
        }

        joined_observations: list[dict[str, Any]] = []
        for obs in tp_obj.get("construction_observations") or []:
            ref_id = obs.get("ref")
            la = level_by_ref.get(ref_id, {})
            assigned_level = la.get("level")
            uncertainties = []
            if obs.get("evidence_uncertainty"):
                uncertainties.append(str(obs["evidence_uncertainty"]))
            if la.get("uncertainty"):
                uncertainties.append(str(la["uncertainty"]))
            joined_observations.append(
                {
                    "ref": ref_id,
                    "paper_id": obs.get("paper_id"),
                    "year": obs.get("year"),
                    "part": obs.get("part"),
                    "idx": obs.get("idx"),
                    "sub": obs.get("sub"),
                    "printed_idx": obs.get("printed_idx"),
                    "group_key": f"{obs.get('paper_id')}|{obs.get('part')}|{obs.get('idx')}",
                    "topic": obs.get("topic"),
                    "grade": obs.get("grade"),
                    "level": assigned_level,
                    "level_status": "assigned"
                    if assigned_level in ("NB", "TH", "VD")
                    else "unknown",
                    "level_confidence": la.get("confidence"),
                    "level_justification": la.get("justification"),
                    "decisive_demand": la.get("decisive_demand"),
                    "discrimination": obs.get("discrimination"),
                    "given": obs.get("given"),
                    "task": obs.get("task"),
                    "reasoning": list(obs.get("reasoning") or []),
                    "steps": obs.get("steps"),
                    "combines": list(obs.get("combines") or []),
                    "cue_use": obs.get("cue_use"),
                    "difficulty_source": obs.get("difficulty_source"),
                    "wrong_options": obs.get("wrong_options"),
                    "wrong_option_details": list(obs.get("wrong_option_details") or []),
                    "evidence_class": obs.get("evidence_class", "provincial_third_party"),
                    "evidence_uncertainty": obs.get("evidence_uncertainty"),
                    "level_uncertainty": la.get("uncertainty"),
                    "uncertainties": uncertainties,
                    "source_id": f"{tp_id}:{ref_id}",
                    "source_locator": f"{locator}:{ref_id}",
                    "source_version": snapshot_sha,
                    "approval_status": "agent-reviewed, not teacher-confirmed",
                    "teacher_approved": False,
                }
            )

        unready_ids = set(tp_obj.get("unready_example_ids") or [])
        missing_ids = set(tp_obj.get("missing_example_ids") or [])
        ready_examples: list[dict[str, Any]] = []
        all_examples: list[dict[str, Any]] = []

        for ex in tp_obj.get("examples") or []:
            target = ex.get("target") or {}
            sample = ex.get("sample") or {}
            ex_id = sample.get("id") or target.get("id")
            is_ready = (
                ex_id not in unready_ids
                and ex_id not in missing_ids
                and ex.get("key_agreement") is True
                and ex.get("level_agreement") is True
                and ex.get("status") == "model_checks_passed_pending_teacher_review"
            )
            formatted_ex = {
                "example_id": ex_id,
                "part": target.get("part"),
                "level": target.get("level"),
                "qtype": target.get("qtype"),
                "topic": target.get("topic") or display_topic,
                "stem": sample.get("stem", ""),
                "options": list(sample.get("options") or []),
                "statements": list(sample.get("statements") or []),
                "answers": list(sample.get("answers") or []),
                "solution": sample.get("solution", ""),
                "distractors": list(sample.get("distractors") or []),
                "level_reason": sample.get("level_reason"),
                "prerequisites": list(sample.get("prerequisites") or []),
                "variation_guidance": sample.get("variation_guidance"),
                "uncertainties": list(sample.get("uncertainties") or []),
                "support_refs": list(target.get("support_refs") or []),
                "official_anchor_available": bool(target.get("official_anchor_available")),
                "origin": ex.get("origin", "synthetic_not_corpus_evidence"),
                "evidence_class": "synthetic",
                "model": ex.get("model"),
                "key_agreement": bool(ex.get("key_agreement")),
                "level_agreement": bool(ex.get("level_agreement")),
                "approval_status": ex.get("status", "model_checks_passed_pending_teacher_review"),
                "teacher_approved": bool(tp_obj.get("teacher_approved", False)),
                "ready_for_context": is_ready,
                "source_id": f"{tp_id}:example:{ex_id}",
                "source_locator": f"{locator}:example:{ex_id}",
                "source_version": snapshot_sha,
                "source_rows_sha256": ex.get("source_rows_sha256"),
            }
            all_examples.append(formatted_ex)
            if is_ready:
                ready_examples.append(formatted_ex)

        patterns_by_class_raw = topic_meta.get("patterns_by_class") or {}
        normalized_patterns: list[dict[str, Any]] = []
        for ev_class in ("official", "provincial_third_party"):
            for idx_p, pat in enumerate(patterns_by_class_raw.get(ev_class) or [], 1):
                p_kind = pat.get("part_kind", "")
                mapped_part = PART_KIND_TO_PART.get(p_kind, p_kind)
                normalized_patterns.append(
                    {
                        "pattern_id": f"{tp_id}:{ev_class}:p{idx_p}",
                        "part": mapped_part,
                        "part_kind": p_kind,
                        "topic": pat.get("topic") or display_topic,
                        "grade": pat.get("grade"),
                        "construction": pat.get("construction", ""),
                        "wrong_options": pat.get("wrong_options"),
                        "difficulty_source": pat.get("difficulty_source"),
                        "discrimination": pat.get("discrimination"),
                        "typical_steps": pat.get("typical_steps"),
                        "refs": list(pat.get("refs") or []),
                        "topic_support_refs": list(pat.get("topic_support_refs") or []),
                        "paper_count": pat.get("paper_count", 0),
                        "row_count": pat.get("row_count", 0),
                        "evidence_class": ev_class,
                        "source_id": f"{tp_id}:pattern:{ev_class}:{idx_p}",
                        "source_locator": f"{locator}:pattern:{ev_class}:{idx_p}",
                        "source_version": snapshot_sha,
                        "approval_status": "agent-reviewed, not teacher-confirmed",
                        "teacher_approved": False,
                    }
                )

        common_mistakes = _extract_common_mistakes(
            patterns_by_class_raw, joined_observations, ready_examples
        )

        # Link curriculum units by domain phrases, Vietnamese bigrams and grades.
        top_curriculum = _link_curriculum_units(
            display_topic,
            topic_key,
            list(topic_meta.get("raw_topics") or []),
            grades,
            curriculum_rows,
        )

        parts_present = sorted({obs["part"] for obs in joined_observations if obs.get("part")})
        levels_present = sorted(
            {obs["level"] for obs in joined_observations if obs.get("level") in ("NB", "TH", "VD")}
        )
        unknown_level_count = sum(obs["level_status"] == "unknown" for obs in joined_observations)

        pack_record = {
            "topic_pack_id": tp_id,
            "schema_version": tp_obj["schema_version"],
            "subject": subject,
            "topic_key": topic_key,
            "display_topic": display_topic,
            "raw_topics": list(topic_meta.get("raw_topics") or []),
            "grades": grades,
            "parts_present": parts_present,
            "levels_present": levels_present,
            "unknown_level_count": unknown_level_count,
            "classes": topic_meta.get("classes") or {},
            "patterns": normalized_patterns,
            "patterns_by_class": patterns_by_class_raw,
            "construction_observations": joined_observations,
            "level_assignments": list(tp_obj.get("level_assignments") or []),
            "examples": ready_examples,
            "all_examples": all_examples,
            "unready_example_ids": sorted(unready_ids),
            "missing_example_ids": sorted(missing_ids),
            "common_mistakes": common_mistakes,
            "curriculum_units": top_curriculum,
            "component_details": topic_meta.get("component_details") or {},
            "support_refs": list(topic_meta.get("support_refs") or []),
            "provenance": {
                "source_id": f"profile:{subject}:{tp_id}",
                "source_locator": locator,
                "source_version": snapshot_sha,
                "content_sha256": verified_sha,
                "bundle_sha256": bundle_sha256,
                "completion_sha256": completion_sha256,
                "origin": tp_obj.get("origin"),
                "approval_status": "agent-reviewed, not teacher-confirmed",
                "teacher_approved": bool(tp_obj.get("teacher_approved", False)),
                "runtime_compatibility_verified": bool(
                    bundle.get("runtime_compatibility_verified", False)
                ),
                "evidence_classes": {
                    "official_observations": sum(
                        o["evidence_class"] == "official" for o in joined_observations
                    ),
                    "provincial_observations": sum(
                        o["evidence_class"] == "provincial_third_party" for o in joined_observations
                    ),
                    "synthetic_ready_examples": len(ready_examples),
                },
                "clear_example_count": entry.get("clear_example_count", len(ready_examples)),
                "pending_cell_count": entry.get("pending_cell_count", 0),
            },
        }
        topic_packs_by_id[tp_id] = pack_record
        topic_key_to_id[topic_key] = tp_id
        norm_name_to_id[normalize(topic_key)] = tp_id
        norm_name_to_id[normalize(display_topic)] = tp_id

    release_info = {
        "subject": subject,
        "source_mode": source_mode,
        "corpus_snapshot": snapshot_sha,
        "release_fingerprint": release_fingerprint,
        "bundle_sha256": bundle_sha256,
        "completion_sha256": completion_sha256,
        "levels_sha256": levels_sha256,
        "curriculum_sha256": curriculum_sha256,
        "config_sha256": config_sha256,
        "profile_schema_version": bundle.get("schema_version"),
        "bundle_status": bundle.get("status"),
        "teacher_approved": bool(bundle.get("teacher_approved", False)),
        "runtime_compatibility_verified": bool(bundle.get("runtime_compatibility_verified", False)),
        "topic_pack_count": len(topic_packs_by_id),
        "curriculum_unit_count": len(curriculum_rows),
        "total_observations": sum(
            len(tp["construction_observations"]) for tp in topic_packs_by_id.values()
        ),
        "total_ready_examples": sum(len(tp["examples"]) for tp in topic_packs_by_id.values()),
        "unknown_level_rows": completion.get("unknown_level_rows", 0),
        "source_QA_clear": bool(completion.get("source_QA_clear", False)),
    }

    release_data = {
        "release_fingerprint": release_fingerprint,
        "cache_hit": False,
        "release_info": release_info,
        "bundle": bundle,
        "completion": completion,
        "levels_doc": levels_doc,
        "verification": verification_doc,
        "topic_packs_by_id": topic_packs_by_id,
        "topic_key_to_id": topic_key_to_id,
        "norm_name_to_id": norm_name_to_id,
        "topic_mapping_entries": topic_mapping_entries,
        "defaults_snapshot": defaults_snapshot,
        "curriculum_rows": curriculum_rows,
        "curriculum_docs": curriculum_docs,
        "source_by_class": source_by_class,
        "_raw_files": files,
    }
    _RELEASE_CACHE[cache_key] = release_data
    return release_data


def get_topic_pack(
    release: dict[str, Any],
    identifier: str,
    part: str | None = None,
    level: str | None = None,
    include_unready_examples: bool = False,
) -> dict[str, Any]:
    """Fetch a complete, untruncated Topic Pack by ID, locator, or topic name (P0)."""
    if not isinstance(identifier, str) or not identifier.strip():
        raise Gap("invalid_request", "Topic pack identifier must be a nonempty string.")
    cleaned = identifier.strip()
    by_id = release["topic_packs_by_id"]

    # 1. Direct ID or locator match (e.g. "5fed66930d74" or "profile:toan:5fed66930d74" or "...#5fed66930d74")
    candidate_id = cleaned
    if "#" in candidate_id:
        candidate_id = candidate_id.rsplit("#", 1)[-1]
    elif ":" in candidate_id:
        candidate_id = candidate_id.rsplit(":", 1)[-1]
    if candidate_id.endswith(".json"):
        candidate_id = PurePosixPath(candidate_id).stem

    pack = by_id.get(candidate_id)
    if pack is None:
        # 2. Exact topic_key or normalized topic name match
        tp_id = release["topic_key_to_id"].get(cleaned) or release["norm_name_to_id"].get(
            normalize(cleaned)
        )
        if tp_id:
            pack = by_id[tp_id]

    if pack is None:
        raise Gap("topic_not_found", f"No topic pack found for identifier: {identifier!r}.")

    result = dict(pack)
    examples = list(pack["all_examples"] if include_unready_examples else pack["examples"])
    observations = list(pack["construction_observations"])
    patterns = list(pack["patterns"])

    if part is not None:
        observations = [o for o in observations if o.get("part") == part]
        patterns = [p for p in patterns if p.get("part") == part]
        examples = [e for e in examples if e.get("part") == part]

    if level is not None:
        observations = [o for o in observations if o.get("level") == level]
        examples = [e for e in examples if e.get("level") == level]

    result["patterns"] = patterns
    result["construction_observations"] = observations
    result["examples"] = examples
    result.pop("all_examples", None)
    return result


def export_release_pack(
    out_dir: Path,
    subject: str = "toan",
    ref: str = "origin/staging/rag",
    repo: Path | None = None,
) -> dict[str, Any]:
    """Export a fixed, self-contained Windows release folder with SHA-256 manifest verification."""
    release = load_profile_release(subject=subject, ref=ref, repo=repo)
    target_root = Path(out_dir).resolve()
    target_root.mkdir(parents=True, exist_ok=True)

    raw_files: dict[str, bytes] = release["_raw_files"]
    file_hashes: dict[str, str] = {}
    for rel_path, content in sorted(raw_files.items()):
        lf_bytes = content.replace(b"\r\n", b"\n")
        dest = target_root / Path(rel_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(lf_bytes)
        file_hashes[rel_path] = _sha256_bytes(lf_bytes)

    manifest = {
        "schema_version": CONFIG["schema_version"],
        "subject": subject,
        "corpus_snapshot": release["release_info"]["corpus_snapshot"],
        "release_fingerprint": release["release_fingerprint"],
        "bundle_sha256": release["release_info"]["bundle_sha256"],
        "completion_sha256": release["release_info"]["completion_sha256"],
        "curriculum_sha256": release["release_info"]["curriculum_sha256"],
        "topic_pack_count": release["release_info"]["topic_pack_count"],
        "curriculum_unit_count": release["release_info"]["curriculum_unit_count"],
        "file_count": len(file_hashes),
        "files_sha256": file_hashes,
    }
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    (target_root / "manifest.json").write_bytes(manifest_bytes)

    # Immediately verify reload from the exported directory.
    reloaded = load_profile_release(subject=subject, pack_dir=target_root, force_rebuild=True)
    if reloaded["release_fingerprint"] != release["release_fingerprint"]:
        raise Gap(
            "malformed_document",
            "Exported release pack fingerprint did not match source release fingerprint.",
        )
    return {
        "out_dir": str(target_root),
        "release_fingerprint": reloaded["release_fingerprint"],
        "corpus_snapshot": reloaded["release_info"]["corpus_snapshot"],
        "file_count": len(file_hashes),
        "topic_pack_count": reloaded["release_info"]["topic_pack_count"],
    }
