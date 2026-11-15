"""Reviewer role; model transport and workflow control stay separate."""

from exam_baseline.core.contracts import LLMProvider
from exam_baseline.pipeline.agents.base import structured_stage
from exam_baseline.pipeline.agents.prompts import REVIEWER_SYSTEM
from exam_baseline.pipeline.agents.responses import ResponseContract
from exam_baseline.pipeline.agents.validation import validate_review
from exam_baseline.pipeline.contracts import ReviewReport, SolutionBook


class ReviewerAgent:
    async def run(
        self, packet: dict, provider: LLMProvider, student: dict, book: SolutionBook
    ) -> ReviewReport:
        # Physical call count is one, including malformed responses: no Reviewer retry.
        return await structured_stage(
            provider,
            "reviewer",
            packet,
            ResponseContract(ReviewReport),
            (),
            0,
            lambda report: validate_review(report, student, book),
            system=REVIEWER_SYSTEM,
        )
