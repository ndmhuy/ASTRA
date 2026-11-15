"""Private answer artifact locations for Composer draft handoffs."""

from pathlib import Path


def private_artifact_path(output_dir: Path, draft_id: str) -> Path:
    return output_dir.parent / "teacher_private" / f"{draft_id}.json"
