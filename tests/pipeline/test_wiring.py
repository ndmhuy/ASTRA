"""Role replacement does not require rewriting the workflow or transport layer."""

import asyncio

from exam_baseline.pipeline.agents import IllustratorAgent, PipelineAgents
from exam_baseline.pipeline.bootstrap import replay_providers
from exam_baseline.pipeline.contracts import IllustrationBook
from exam_baseline.pipeline.orchestration.orchestrator import Orchestrator
from tests.pipeline.helpers import TEXT, payload


def test_a_deterministic_illustrator_can_be_injected_without_provider_calls(tmp_path):
    class EmptyIllustrator(IllustratorAgent):
        async def run(self, draft, provider, schema_repairs=1):
            assert not draft.visuals
            return IllustrationBook(
                exam_id=draft.exam_id, draft_id=draft.draft_id, revision=draft.revision, drawings=[]
            )

    agents = PipelineAgents(illustrator=EmptyIllustrator())
    result = asyncio.run(
        Orchestrator(replay_providers(TEXT), agents=agents).run(payload(), tmp_path / "run")
    )
    assert result.final_latex and result.human_review_required
    assert [call.stage for call in result.calls] == ["composer", "solver", "reviewer"]
