from dataclasses import dataclass, field
from typing import ClassVar

from exam_baseline.pipeline.contracts import AGENT_ROLES

from .composer import ComposerAgent
from .illustrator import IllustratorAgent
from .reviewer import ReviewerAgent
from .solver import SolverAgent

__all__ = ["ComposerAgent", "IllustratorAgent", "SolverAgent", "ReviewerAgent", "PipelineAgents"]


@dataclass(frozen=True)
class PipelineAgents:
    composer: ComposerAgent = field(default_factory=ComposerAgent)
    illustrator: IllustratorAgent = field(default_factory=IllustratorAgent)
    solver: SolverAgent = field(default_factory=SolverAgent)
    reviewer: ReviewerAgent = field(default_factory=ReviewerAgent)
    roles: ClassVar[tuple[str, ...]] = AGENT_ROLES
