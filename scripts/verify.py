"""Portable verification: python scripts/verify.py (install requirements-dev.txt)."""

from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ("rag_workflow", "tests", "scripts")


def main():
    commands = [
        [sys.executable, "-m", "compileall", "-q", *SOURCES],
        [sys.executable, "-m", "ruff", "check", *SOURCES],
        [sys.executable, "-m", "ruff", "format", "--check", *SOURCES],
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
    ]
    if shutil.which("node"):
        commands.append(["node", "--check", "rag_workflow/web/app.js"])
    else:
        print("Node not found: skipping optional JavaScript syntax check.", flush=True)
    for command in commands:
        print("Running: " + " ".join(command), flush=True)
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode:
            return result.returncode
    print("Verification passed. Browser checks are separate; see docs/rag-workflow.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
