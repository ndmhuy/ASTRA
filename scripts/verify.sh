#!/usr/bin/env bash
# Run from any directory; no downloads or paid/model calls.
set -euo pipefail
cd "$(dirname "$0")/.."
rag_python="${RAG_PYTHON:-python}"
exec "$rag_python" scripts/verify.py
