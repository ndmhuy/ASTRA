#!/usr/bin/env bash
# Run from any directory; no downloads or paid/model calls.
set -euo pipefail
cd "$(dirname "$0")/.."
python -m compileall -q rag_workflow tests
python -m unittest discover -s tests -v
git diff --check
