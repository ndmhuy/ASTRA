"""Run with: python -m rag_workflow.cli --query ... --corpus ... or --sample-matrix / --topic-pack ..."""

import argparse
import json
import sys
from pathlib import Path
from .existing_corpus import load_existing_corpus, search_existing
from .matrix_retriever import default_toan_thpt_matrix, retrieve_exam_context
from .models import CONFIG, Gap, RetrievalResponse, normalize_level, normalize_part
from .profile_pack import export_release_pack, get_topic_pack, load_profile_release
from .workflow import run


def _write_json(data: dict, out_path: Path | None = None) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", help="Knowledge or topic query string")
    parser.add_argument("--topic-pack", help="Fetch full topic pack by ID or topic name")
    parser.add_argument("--matrix", type=Path, help="Path to exam matrix request JSON file")
    parser.add_argument(
        "--sample-matrix",
        action="store_true",
        help="Run retrieval for the default 22-question Toán THPT sample matrix",
    )
    parser.add_argument(
        "--export-pack",
        type=Path,
        help="Export a portable Toán THPT release pack directory with SHA-256 manifest",
    )
    inputs = parser.add_mutually_exclusive_group()
    inputs.add_argument("--corpus", type=Path, help="Approved JSONL passage pack")
    inputs.add_argument(
        "--existing", action="store_true", help="Search the existing local corpus snapshot"
    )
    inputs.add_argument(
        "--pack-dir", type=Path, help="Load profile & curriculum from an exported release folder"
    )
    parser.add_argument("--corpus-ref", default="origin/staging/rag")
    parser.add_argument("--subject", default="toan")
    parser.add_argument("--part", help="Optional part filter for --topic-pack (P1, P2, P3)")
    parser.add_argument("--level", help="Optional level filter for --topic-pack (NB, TH, VD)")
    parser.add_argument(
        "--vdc-policy",
        choices=tuple(CONFIG["vdc_policies"]),
        default=CONFIG["default_vdc_policy"],
    )
    parser.add_argument("--collection", choices=("all", "curriculum", "exam"), default="all")
    parser.add_argument("--mode", choices=tuple(CONFIG["modes"]), default=CONFIG["default_mode"])
    parser.add_argument("--top-k", type=int, default=CONFIG["default_top_k"])
    parser.add_argument("--edition", help="Exact edition identifier when multiple editions exist")
    parser.add_argument("--out", type=Path, help="Optional output file path for JSON response")
    args = parser.parse_args()

    try:
        if args.export_pack:
            exported = export_release_pack(
                args.export_pack, subject=args.subject, ref=args.corpus_ref
            )
            _write_json({"status": "success", "exported_release": exported}, args.out)
            return 0

        if args.topic_pack:
            rel = load_profile_release(
                subject=args.subject, ref=args.corpus_ref, pack_dir=args.pack_dir
            )
            part_filter = normalize_part(args.part) if args.part else None
            lvl_filter = normalize_level(args.level) if args.level else None
            pack = get_topic_pack(rel, args.topic_pack, part=part_filter, level=lvl_filter)
            _write_json(
                {
                    "status": "success",
                    "release_info": rel["release_info"],
                    "topic_pack": pack,
                },
                args.out,
            )
            return 0

        if args.matrix or args.sample_matrix:
            if args.matrix:
                matrix_payload = json.loads(args.matrix.read_text(encoding="utf-8-sig"))
            else:
                matrix_payload = default_toan_thpt_matrix()
            if args.vdc_policy:
                matrix_payload["vdc_policy"] = args.vdc_policy
            matrix_res = retrieve_exam_context(
                matrix_payload, ref=args.corpus_ref, pack_dir=args.pack_dir
            )
            _write_json(matrix_res.to_dict(), args.out)
            return 0 if matrix_res.status == "success" else 2

        if not args.query:
            parser.error(
                "Specify --query (with --corpus or --existing), --topic-pack, --matrix, --sample-matrix, or --export-pack."
            )
        if not (args.corpus or args.existing):
            parser.error("--query requires either --corpus or --existing.")

        payload = {
            "query_text": args.query,
            "top_k": args.top_k,
            "edition": args.edition,
            "mode": args.mode,
        }
        if args.existing:
            documents, info = load_existing_corpus(args.corpus_ref)
            response = search_existing(
                dict(payload, collection=args.collection),
                documents,
                info["snapshot"],
                info["corpus_sha256"],
            )
        else:
            response = run(payload, args.corpus)
    except Gap as exc:
        response = RetrievalResponse(gaps=[{"code": exc.code, "message": str(exc)}])
    _write_json(response.to_dict(), args.out)
    return 0 if response.status == "success" else 2


if __name__ == "__main__":
    raise SystemExit(main())
