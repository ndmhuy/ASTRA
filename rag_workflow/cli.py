"""Run with: python -m rag_workflow.cli --query ... --corpus ..."""
import argparse
import json
import sys
from pathlib import Path
from .models import CONFIG
from .workflow import run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    parser.add_argument("--corpus", type=Path, required=True, help="Approved JSONL passage pack")
    parser.add_argument("--top-k", type=int, default=CONFIG["default_top_k"])
    parser.add_argument("--edition", help="Exact edition identifier when multiple editions exist")
    args = parser.parse_args()
    response = run({"query_text": args.query, "top_k": args.top_k, "edition": args.edition}, args.corpus)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(response.to_dict(), ensure_ascii=False, indent=2))
    return 0 if response.status == "success" else 2


if __name__ == "__main__":
    raise SystemExit(main())
