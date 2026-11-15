"""Deterministic retrieval benchmark and automated gold-label verifier."""

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

from .demo import demo_documents
from .document_loader import load_documents
from .existing_corpus import load_existing_corpus
from .matrix_retriever import default_toan_thpt_matrix, retrieve_exam_context
from .models import CONFIG, Gap
from .profile_pack import load_profile_release
from .results import collection_fingerprint
from .search_index import split_passages
from .workflow import run_documents

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXISTING_GOLD = ROOT / "eval" / "gold_queries.jsonl"
DEFAULT_DEMO_GOLD = ROOT / "tests" / "fixtures" / "eval_gold_demo.jsonl"
DEFAULT_TOAN_ACCEPTANCE = ROOT / "eval" / "toan_thpt_acceptance.json"


def load_gold_queries(path: Path) -> list[dict]:
    if not path.is_file():
        raise Gap("eval_unavailable", f"Gold benchmark file not found: {path}")
    raw = path.read_text(encoding="utf-8")
    rows = []
    seen_ids = set()
    for line_no, line in enumerate(raw.splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Malformed JSON in gold file at line {line_no}: {exc}") from exc
        if not isinstance(row, dict) or "id" not in row or "query_text" not in row:
            raise ValueError(f"Gold row at line {line_no} is missing required fields.")
        if row["id"] in seen_ids:
            raise ValueError(f"Duplicate gold query id: {row['id']}")
        seen_ids.add(row["id"])
        if row.get("expected_status") not in ("success", "gap"):
            raise ValueError(f"Invalid expected_status in gold row {row['id']}")
        if row.get("split", "dev") not in ("dev", "heldout"):
            raise ValueError(f"Invalid split in gold row {row['id']}")
        if row["expected_status"] == "gap" and not row.get("expected_gap"):
            raise ValueError(f"Gap gold row {row['id']} is missing expected_gap.")
        if row["expected_status"] == "success" and not row.get("relevant"):
            raise ValueError(f"Success gold row {row['id']} is missing relevant targets.")
        rows.append(row)
    if not rows:
        raise ValueError("Gold benchmark file contains no queries.")
    return rows


def verify_gold_queries(rows: list[dict], documents) -> dict:
    """Programmatically verify every gold target against the loaded corpus."""
    by_locator = {d.source_locator: d for d in documents}
    by_id = {d.document_id: d for d in documents}
    checked_targets = 0
    checked_passages = 0
    for row in rows:
        if row["expected_status"] != "success":
            continue
        for target in row["relevant"]:
            doc = by_locator.get(target) or by_id.get(target)
            if doc is None:
                raise ValueError(f"Gold row {row['id']} references unknown corpus target: {target}")
            checked_targets += 1
        for p_target in row.get("relevant_passages", ()):
            loc = p_target.get("locator")
            label = p_target.get("label")
            doc = by_locator.get(loc) or by_id.get(loc)
            if doc is None:
                raise ValueError(f"Gold row {row['id']} references unknown passage source: {loc}")
            structured = getattr(doc, "content_kind", None) == "exam"
            labels = {
                p.label for p in split_passages(doc.content, structured=structured) if p.label
            }
            if label and label not in labels:
                raise ValueError(
                    f"Gold row {row['id']} expects passage label {label!r} not found in {loc}"
                )
            checked_passages += 1
    return {
        "status": "verified",
        "verified_by": "auto-corpus-check-v1",
        "total_queries": len(rows),
        "success_queries": sum(r["expected_status"] == "success" for r in rows),
        "gap_queries": sum(r["expected_status"] == "gap" for r in rows),
        "verified_targets": checked_targets,
        "verified_passages": checked_passages,
    }


def _aggregate_subset(items: list[dict]) -> dict:
    success_rows = [r for r in items if r["expected_status"] == "success"]
    gap_rows = [r for r in items if r["expected_status"] == "gap"]
    passage_rows = [r for r in success_rows if r["passage_hit"] is not None]
    n_succ = len(success_rows)
    n_gap = len(gap_rows)
    n_pass = len(passage_rows)
    return {
        "queries": len(items),
        "success_queries": n_succ,
        "gap_queries": n_gap,
        "hit_at_k": round(sum(r["hit"] for r in success_rows) / n_succ, 4) if n_succ else 0.0,
        "recall_at_k": round(sum(r["recall"] for r in success_rows) / n_succ, 4) if n_succ else 0.0,
        "mrr": round(sum(r["rr"] for r in success_rows) / n_succ, 4) if n_succ else 0.0,
        "passage_hit_at_k": (
            round(sum(r["passage_hit"] for r in passage_rows) / n_pass, 4) if n_pass else None
        ),
        "gap_accuracy": round(sum(r["gap_correct"] for r in gap_rows) / n_gap, 4) if n_gap else 1.0,
        "false_gap_rate": (
            round(sum(r["actual_status"] == "gap" for r in success_rows) / n_succ, 4)
            if n_succ
            else 0.0
        ),
        "avg_elapsed_ms": (
            round(sum(r["elapsed_ms"] for r in items) / len(items), 2) if items else 0.0
        ),
    }


def evaluate_mode(
    rows: list[dict],
    documents,
    corpus_sha256: str,
    corpus_info=None,
    mode: str = "hybrid",
    k: int = 5,
) -> dict:
    per_query = []
    top_k = max(k, CONFIG["default_top_k"])
    for row in rows:
        payload = {
            "query_text": row["query_text"],
            "top_k": top_k,
            "mode": mode,
            "edition": row.get("edition"),
        }
        if corpus_info is not None and row.get("collection") in ("all", "curriculum", "exam"):
            payload["collection"] = row["collection"]
        started = time.perf_counter()
        resp = run_documents(payload, documents, corpus_sha256, corpus_info)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        docs = resp.documents[:k]
        found_keys = []
        for d in docs:
            found_keys.append(d["source_locator"])
            found_keys.append(d["document_id"])
        found_set = set(found_keys)

        rel = set(row.get("relevant", ()))
        hit = bool(rel & found_set) if rel else False
        recall = len(rel & found_set) / len(rel) if rel else 0.0
        first_rank = None
        for rank, d in enumerate(docs, 1):
            if d["source_locator"] in rel or d["document_id"] in rel:
                first_rank = rank
                break
        rr = (1.0 / first_rank) if first_rank else 0.0

        p_targets = row.get("relevant_passages")
        passage_hit = None
        if p_targets:
            target_pairs = {(pt.get("locator"), pt.get("label")) for pt in p_targets}
            passage_hit = any(
                (d["source_locator"], d.get("passage_label")) in target_pairs
                or (d["document_id"], d.get("passage_label")) in target_pairs
                for d in docs
            )

        actual_gap = resp.gaps[0]["code"] if resp.gaps else None
        gap_correct = (
            resp.status == "gap" and actual_gap == row.get("expected_gap")
            if row["expected_status"] == "gap"
            else False
        )
        top_doc = docs[0] if docs else None
        per_query.append(
            {
                "id": row["id"],
                "split": row.get("split", "dev"),
                "collection": row.get("collection", "pack"),
                "category": row.get("category", "general"),
                "query_text": row["query_text"],
                "expected_status": row["expected_status"],
                "expected_gap": row.get("expected_gap"),
                "actual_status": resp.status,
                "actual_gap": actual_gap,
                "hit": hit,
                "recall": round(recall, 4),
                "rr": round(rr, 4),
                "passage_hit": passage_hit,
                "gap_correct": gap_correct,
                "top_locator": top_doc["source_locator"] if top_doc else None,
                "top_title": top_doc["title"] if top_doc else None,
                "top_label": top_doc.get("passage_label") if top_doc else None,
                "top_score": top_doc["relevance_score"] if top_doc else None,
                "elapsed_ms": elapsed_ms,
            }
        )

    collections = sorted({r["collection"] for r in per_query})
    splits = sorted({r["split"] for r in per_query})
    return {
        "mode": mode,
        "ranking_method": CONFIG.get("ranking_versions", {}).get(mode, CONFIG["ranking_version"]),
        "overall": _aggregate_subset(per_query),
        "by_collection": {
            c: _aggregate_subset([r for r in per_query if r["collection"] == c])
            for c in collections
        },
        "by_split": {
            s: _aggregate_subset([r for r in per_query if r["split"] == s]) for s in splits
        },
        "details": per_query,
    }


def evaluate_all_modes(
    rows: list[dict],
    documents,
    corpus_sha256: str,
    corpus_info=None,
    modes=None,
    k: int = 5,
    split: str = "all",
) -> dict:
    verification = verify_gold_queries(rows, documents)
    active_rows = rows if split == "all" else [r for r in rows if r.get("split", "dev") == split]
    active_modes = list(modes or CONFIG["modes"])
    mode_results = {}
    for m in active_modes:
        mode_results[m] = evaluate_mode(
            active_rows, documents, corpus_sha256, corpus_info=corpus_info, mode=m, k=k
        )
    # Build per-query cross-mode comparison table for the UI and reports.
    query_comparison = []
    for idx, row in enumerate(active_rows):
        entry = {
            "id": row["id"],
            "split": row.get("split", "dev"),
            "collection": row.get("collection", "pack"),
            "category": row.get("category", "general"),
            "query_text": row["query_text"],
            "expected_status": row["expected_status"],
            "modes": {},
        }
        for m in active_modes:
            d = mode_results[m]["details"][idx]
            entry["modes"][m] = {
                "status": d["actual_status"],
                "hit": d["hit"],
                "rr": d["rr"],
                "passage_hit": d["passage_hit"],
                "gap_correct": d["gap_correct"],
                "top_title": d["top_title"],
                "top_label": d["top_label"],
                "top_score": d["top_score"],
            }
        query_comparison.append(entry)

    gold_hash = hashlib.sha256(
        json.dumps(rows, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": CONFIG["schema_version"],
        "k": k,
        "split": split,
        "verification": verification,
        "gold_sha256": gold_hash,
        "corpus_snapshot": corpus_info["snapshot"] if corpus_info else None,
        "corpus_sha256": corpus_sha256,
        "config_sha256": hashlib.sha256(
            json.dumps(CONFIG, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest(),
        "modes": {
            m: {
                "ranking_method": res["ranking_method"],
                "overall": res["overall"],
                "by_collection": res["by_collection"],
                "by_split": res["by_split"],
            }
            for m, res in mode_results.items()
        },
        "queries": query_comparison,
    }


def evaluate_toan_acceptance(
    acceptance_path: Path = DEFAULT_TOAN_ACCEPTANCE,
    ref: str = "origin/staging/rag",
    pack_dir: Path | None = None,
) -> dict:
    """Run the Toán THPT MAS-handoff acceptance test suite and 22-question sample matrix check."""
    if not acceptance_path.is_file():
        raise Gap("eval_unavailable", f"Acceptance suite file not found: {acceptance_path}")
    suite = json.loads(acceptance_path.read_text(encoding="utf-8-sig"))
    release = load_profile_release(subject="toan", ref=ref, pack_dir=pack_dir)

    case_results = []
    passed_count = 0

    for case in suite.get("cases", []):
        started = time.perf_counter()
        payload = {
            "matrix_id": case["case_id"],
            "subject": suite.get("subject", "toan"),
            "vdc_policy": case.get("vdc_policy", CONFIG["default_vdc_policy"]),
            "questions": [case["question"]],
        }
        res = retrieve_exam_context(payload, release=release)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        ctx = res.question_contexts[0] if res.question_contexts else {}
        exp = case["expected"]

        checks: dict[str, bool] = {}
        checks["status_match"] = ctx.get("status") == exp["status"]

        if "expected_topic_pack_ids" in exp:
            got_tp_ids = {p["topic_pack_id"] for p in (ctx.get("matched_topic_packs") or [])}
            checks["topic_pack_match"] = bool(set(exp["expected_topic_pack_ids"]) & got_tp_ids)

        if "expected_curriculum_ids" in exp:
            got_curr_ids = {c["unit_id"] for c in (ctx.get("curriculum_knowledge") or [])}
            checks["curriculum_match"] = bool(set(exp["expected_curriculum_ids"]) & got_curr_ids)

        if "effective_level" in exp:
            checks["effective_level_match"] = (
                ctx.get("resolved_level", {}).get("effective") == exp["effective_level"]
            )

        if exp.get("p2_all_statements_covered"):
            p2_cov = ctx.get("p2_statement_coverage") or {}
            checks["p2_statements_covered"] = bool(p2_cov) and all(
                v.get("covered") is True for v in p2_cov.values()
            )

        if "min_patterns" in exp:
            checks["min_patterns"] = (
                len(ctx.get("construction_patterns") or []) >= exp["min_patterns"]
            )

        if "min_observations" in exp:
            checks["min_observations"] = (
                len(ctx.get("construction_observations") or []) >= exp["min_observations"]
            )

        if "min_examples" in exp:
            checks["min_examples"] = len(ctx.get("examples") or []) >= exp["min_examples"]

        if "min_mistakes" in exp:
            checks["min_mistakes"] = len(ctx.get("common_mistakes") or []) >= exp["min_mistakes"]

        if "min_reference_chars" in exp:
            checks["min_reference_chars"] = (
                len(ctx.get("reference_material_text") or "") >= exp["min_reference_chars"]
            )

        if "expected_warning_code" in exp:
            w_codes = {w["code"] for w in (ctx.get("warnings") or [])}
            checks["warning_code_match"] = exp["expected_warning_code"] in w_codes

        if "expected_gap_code" in exp:
            g_codes = {g["code"] for g in (ctx.get("gaps") or [])}
            checks["gap_code_match"] = exp["expected_gap_code"] in g_codes

        case_passed = all(checks.values())
        if case_passed:
            passed_count += 1

        case_results.append(
            {
                "case_id": case["case_id"],
                "description": case["description"],
                "passed": case_passed,
                "checks": checks,
                "actual_status": ctx.get("status"),
                "matched_topic_packs": [
                    f"{p['topic_pack_id']}:{p['display_topic']}"
                    for p in (ctx.get("matched_topic_packs") or [])
                ],
                "observation_count": len(ctx.get("construction_observations") or []),
                "example_count": len(ctx.get("examples") or []),
                "mistake_count": len(ctx.get("common_mistakes") or []),
                "reference_chars": len(ctx.get("reference_material_text") or ""),
                "gaps": ctx.get("gaps") or [],
                "warnings": ctx.get("warnings") or [],
                "elapsed_ms": elapsed_ms,
            }
        )

    # Also verify full 22-question sample matrix end-to-end.
    matrix_started = time.perf_counter()
    sample_res = retrieve_exam_context(default_toan_thpt_matrix(), release=release)
    matrix_elapsed_ms = round((time.perf_counter() - matrix_started) * 1000, 2)
    min_ref_len = min(
        (len(qc.get("reference_material_text", "")) for qc in sample_res.question_contexts),
        default=0,
    )
    matrix_passed = (
        sample_res.status == "success"
        and sample_res.summary.get("total_questions") == 22
        and sample_res.summary.get("ready_questions") == 22
        and sample_res.summary.get("gap_questions") == 0
        and len(sample_res.mas_intake_rag) == 22
        and min_ref_len > 150
    )

    overall_passed = passed_count == len(case_results) and matrix_passed
    return {
        "schema_version": CONFIG["schema_version"],
        "suite_id": suite.get("suite_id", "toan-thpt-mas-acceptance-v1"),
        "status": "passed" if overall_passed else "failed",
        "release_info": release["release_info"],
        "summary": {
            "total_cases": len(case_results),
            "passed_cases": passed_count,
            "pass_rate": round(passed_count / len(case_results), 4) if case_results else 0.0,
            "sample_matrix_22q_passed": matrix_passed,
            "sample_matrix_min_reference_chars": min_ref_len,
            "sample_matrix_elapsed_ms": matrix_elapsed_ms,
        },
        "cases": case_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", type=Path, help="Gold benchmark JSONL file")
    parser.add_argument(
        "--acceptance",
        action="store_true",
        help="Run the Toán THPT MAS-handoff acceptance suite",
    )
    parser.add_argument("--pack-dir", type=Path, help="Exported release pack directory")
    inputs = parser.add_mutually_exclusive_group()
    inputs.add_argument("--existing", action="store_true", help="Evaluate against existing corpus")
    inputs.add_argument("--corpus", type=Path, help="Evaluate against an approved JSONL pack")
    inputs.add_argument("--demo", action="store_true", help="Evaluate against the 12 demo notes")
    parser.add_argument("--corpus-ref", default="origin/staging/rag")
    parser.add_argument(
        "--mode",
        choices=(*CONFIG["modes"], "all"),
        default="all",
        help="Retrieval mode to evaluate",
    )
    parser.add_argument("--split", choices=("all", "dev", "heldout"), default="all")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--out", type=Path, help="Optional output JSON path")
    args = parser.parse_args()

    try:
        if args.acceptance:
            acc_path = args.gold or DEFAULT_TOAN_ACCEPTANCE
            report = evaluate_toan_acceptance(
                acceptance_path=acc_path, ref=args.corpus_ref, pack_dir=args.pack_dir
            )
            if args.out:
                args.out.parent.mkdir(parents=True, exist_ok=True)
                args.out.write_text(
                    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
                )
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8")
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0 if report["status"] == "passed" else 2

        info = None
        if args.corpus:
            documents, corpus_hash = load_documents(args.corpus)
            gold_path = args.gold or DEFAULT_DEMO_GOLD
        elif args.demo:
            documents = demo_documents()
            corpus_hash = collection_fingerprint(documents)
            gold_path = args.gold or DEFAULT_DEMO_GOLD
        else:
            documents, info = load_existing_corpus(args.corpus_ref)
            corpus_hash = info["corpus_sha256"]
            gold_path = args.gold or DEFAULT_EXISTING_GOLD

        rows = load_gold_queries(gold_path)
        modes = CONFIG["modes"] if args.mode == "all" else [args.mode]
        report = evaluate_all_modes(
            rows,
            documents,
            corpus_hash,
            corpus_info=info,
            modes=modes,
            k=args.k,
            split=args.split,
        )
    except (Gap, ValueError, OSError) as exc:
        print(
            json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr
        )
        return 2

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
