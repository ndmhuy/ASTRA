"""Only deterministic Scripted providers; no network or real AI is invoked."""

import asyncio
import json

import pytest

from exam_baseline.core.checkpoints import CheckpointError, GenerationPaused, atomic_json
from exam_baseline.thpt.orchestrator import Orchestrator
from tests.thpt.test_generation import Scripted, request


def providers():
    return {
        role: Scripted(role, False) for role in ("composer", "illustrator", "solver", "reviewer")
    }


def test_pause_preserves_valid_section_and_resume_skips_that_call(tmp_path):
    pool = providers()
    paused = [False]
    output = tmp_path / "fixture"

    def commit(path, data):
        atomic_json(path, data)
        if path.parent.name == "checkpoints":
            paused[0] = True

    def control():
        if paused[0]:
            raise GenerationPaused

    payload = request().model_copy(update={"composer_concurrency": 1})
    with pytest.raises(GenerationPaused):
        asyncio.run(
            Orchestrator(pool, check_control=control, checkpoint_writer=commit).run(payload, output)
        )
    assert len(pool["composer"].calls) == 1
    assert (
        json.loads((output / "_internal/result.json").read_bytes())["execution_status"] == "paused"
    )
    result = asyncio.run(Orchestrator(pool).run(payload, output, resume=True))
    assert result["execution_status"] == "completed"
    assert len(pool["composer"].calls) == 3


def test_restart_before_first_result_and_config_or_output_tampering_fail_safely(tmp_path):
    pool = providers()
    payload = request().model_copy(update={"composer_concurrency": 1})
    output = tmp_path / "fixture"

    def stop_before_first_call():
        raise GenerationPaused

    with pytest.raises(GenerationPaused):
        asyncio.run(Orchestrator(pool, check_control=stop_before_first_call).run(payload, output))
    (output / "_internal/result.json").unlink()
    pool["composer"].model = "incompatible-fixture-model"
    with pytest.raises(CheckpointError, match="configuration"):
        asyncio.run(Orchestrator(pool).run(payload, output, resume=True))
    assert not pool["composer"].calls
    pool = providers()
    asyncio.run(Orchestrator(pool).run(payload, output, resume=True))
    (output / "dap_an_va_loi_giai.json").write_text("{}")
    counts = {role: len(provider.calls) for role, provider in pool.items()}
    with pytest.raises(CheckpointError, match="artifacts"):
        asyncio.run(Orchestrator(pool).run(payload, output, resume=True))
    assert counts == {role: len(provider.calls) for role, provider in pool.items()}
