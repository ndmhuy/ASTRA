#!/usr/bin/env bash
# Run from any directory; no downloads or paid/model calls.
set -euo pipefail
cd "$(dirname "$0")/.."
rag_python="${RAG_PYTHON:-python}"
"$rag_python" -m compileall -q rag_workflow tests scripts
"$rag_python" -m ruff check --select E9,F rag_workflow tests scripts
"$rag_python" -m unittest discover -s tests -v
