"""Run with: python -m rag_workflow.cli --query ... --corpus ..."""

import argparse
import json
import sys
from pathlib import Path
from .models import CONFIG, Gap, RetrievalResponse
from .workflow import run
from .existing_corpus import load_existing_corpus, search_existing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--corpus", type=Path, help="Approved JSONL passage pack")
    inputs.add_argument(
        "--existing", action="store_true", help="Search the existing local corpus snapshot"
    )
    parser.add_argument("--corpus-ref", default="origin/staging/rag")
    parser.add_argument("--collection", choices=("curriculum", "exam"), default="curriculum")
    parser.add_argument("--mode", choices=tuple(CONFIG["modes"]), default=CONFIG["default_mode"])
    parser.add_argument("--top-k", type=int, default=CONFIG["default_top_k"])
    parser.add_argument("--edition", help="Exact edition identifier when multiple editions exist")
    args = parser.parse_args()
    payload = {
        "query_text": args.query,
        "top_k": args.top_k,
        "edition": args.edition,
        "mode": args.mode,
    }
    try:
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
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(response.to_dict(), ensure_ascii=False, indent=2))
    return 0 if response.status == "success" else 2


if __name__ == "__main__":
    raise SystemExit(main())
