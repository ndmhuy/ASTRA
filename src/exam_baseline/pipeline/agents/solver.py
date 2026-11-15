"""Solver role; model transport and workflow control stay separate."""

from exam_baseline.core.contracts import LLMProvider
from exam_baseline.pipeline.agents.base import structured_stage
from exam_baseline.pipeline.agents.prompts import SOLVER_SYSTEM
from exam_baseline.pipeline.agents.responses import ResponseContract
from exam_baseline.pipeline.agents.validation import validate_solutions
from exam_baseline.pipeline.contracts import SolutionBook


class SolverAgent:
    async def run(
        self, student: dict, provider: LLMProvider, schema_repairs: int = 1
    ) -> SolutionBook:
        return await structured_stage(
            provider,
            "solver",
            student,
            ResponseContract(SolutionBook),
            (),
            schema_repairs,
            lambda book: validate_solutions(book, student),
            system=SOLVER_SYSTEM,
        )
