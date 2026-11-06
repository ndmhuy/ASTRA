"""Compatibility launcher; implementation: exam_baseline.pipeline.cli."""

from .pipeline.cli import main

__all__ = ["main"]

if __name__ == "__main__":
    raise SystemExit(main())
