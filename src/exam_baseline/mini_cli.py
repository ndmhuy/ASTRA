"""Compatibility launcher; implementation: exam_baseline.draft.cli."""

from .draft.cli import main

__all__ = ["main"]

if __name__ == "__main__":
    raise SystemExit(main())
