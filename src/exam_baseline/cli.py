"""Compatibility launcher; implementation: exam_baseline.baseline.cli."""

from .baseline.cli import main

__all__ = ["main"]

if __name__ == "__main__":
    raise SystemExit(main())
