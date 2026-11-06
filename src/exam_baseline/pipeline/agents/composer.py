"""Composer role; model transport and workflow control stay separate."""

from pathlib import Path

from exam_baseline.core.contracts import LLMProvider
from exam_baseline.draft.composer import create_draft
from exam_baseline.draft.models import ExamDraft, MiniRequest, StageResult


class ComposerAgent:
    async def run(
        self,
        payload: MiniRequest,
        provider: LLMProvider,
        root: Path,
        revision: int,
        feedback: dict | None = None,
    ) -> ExamDraft | StageResult:
        return await create_draft(
            payload,
            provider,
            root,
            revision=revision,
            repair_feedback=feedback,
            render_figures=False,
        )
