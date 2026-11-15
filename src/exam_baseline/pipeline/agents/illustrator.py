"""Illustrator role; model transport and workflow control stay separate."""

from exam_baseline.core.contracts import LLMProvider
from exam_baseline.draft.models import ExamDraft
from exam_baseline.pipeline.agents.base import structured_stage
from exam_baseline.pipeline.agents.prompts import ILLUSTRATOR_SYSTEM
from exam_baseline.pipeline.agents.responses import IllustrationResponse
from exam_baseline.pipeline.contracts import IllustrationBook
from exam_baseline.pipeline.views import illustration_view, validate_illustrations


class IllustratorAgent:
    async def run(
        self, draft: ExamDraft, provider: LLMProvider, schema_repairs: int = 1
    ) -> IllustrationBook:
        return await structured_stage(
            provider,
            "illustrator",
            illustration_view(draft),
            IllustrationResponse(IllustrationBook),
            (),
            schema_repairs,
            lambda book: validate_illustrations(book, draft),
            system=ILLUSTRATOR_SYSTEM,
        )
