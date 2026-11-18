import asyncio
import json

import pytest

from exam_baseline.core.contracts import Completion, ProviderError
from exam_baseline.pipeline.rendering.syntax import prose, validate_drawing_code
from exam_baseline.thpt.agents import ComposerAgent, ReviewerAgent
from exam_baseline.thpt.runtime import ContractError, RecordingProvider
from tests.thpt.test_generation import question, request


class Responses:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.requests = []
        self.instructions = []

    async def complete(self, prompt):
        self.requests.append(json.loads(prompt.user))
        self.instructions.append(prompt.system)
        value = next(self.responses)
        if isinstance(value, Exception):
            raise value
        return Completion(text=value, model="fixture")


def test_complete_fenced_json_is_accepted_without_extra_call(tmp_path):
    raw = json.dumps({"questions": [question(request().slots[0]).model_dump()]})
    provider = Responses(["```json\n" + raw + "\n```"])
    calls = []
    traced = RecordingProvider(provider, "composer", 1, calls, tmp_path)
    result, _ = asyncio.run(ComposerAgent().run(traced, {}))
    assert result.questions[0].id == "P1-1"
    assert len(calls) == 1 and calls[0]["normalized_json_fence"]


def test_invalid_json_gets_one_correction_with_raw_diagnostics(tmp_path):
    raw = json.dumps({"questions": [question(request().slots[0]).model_dump()]})
    provider = Responses(['{"questions": [', raw])
    calls = []
    traced = RecordingProvider(provider, "composer", 1, calls, tmp_path)
    asyncio.run(ComposerAgent().run(traced, {}))
    assert [c["status"] for c in calls] == ["invalid_contract", "validated"]
    assert "contract_feedback" in provider.requests[1]
    assert (tmp_path / "call_01_composer_r1.txt").read_text() == '{"questions": ['


@pytest.mark.parametrize("agent,attempts", [(ComposerAgent(), 2), (ReviewerAgent(), 1)])
def test_schema_correction_is_bounded_and_reviewer_runs_once(agent, attempts, tmp_path):
    provider = Responses(["invalid"] * attempts)
    calls = []
    with pytest.raises(ContractError) as error:
        asyncio.run(agent.run(RecordingProvider(provider, agent.role, 1, calls, tmp_path), {}))
    assert len(calls) == attempts
    assert error.value.stage == agent.role
    assert error.value.fields[0]["type"] == "json_invalid"


def test_provider_failure_is_recorded_even_without_completion(tmp_path):
    provider = Responses([ProviderError("provider_unavailable", "HTTP 503", http_status=503)])
    calls = []
    with pytest.raises(ProviderError):
        asyncio.run(
            ComposerAgent().run(RecordingProvider(provider, "composer", 1, calls, tmp_path), {})
        )
    assert len(calls) == 1
    assert calls[0]["http_status"] == 503


def test_short_answer_schema_requires_answer_and_exact_question_count():
    contract = ComposerAgent().contract({"part": "P3"})
    schema = contract.model_json_schema()
    assert "answer" in schema["$defs"]["ShortAnswerQuestion"]["required"]
    assert schema["properties"]["questions"]["minItems"] == 6
    data = {"questions": [question(s).model_dump() for s in request().slots if s.part == "P3"]}
    contract.model_validate(data)
    data["questions"][0].pop("answer")
    with pytest.raises(ValueError):
        contract.model_validate(data)


@pytest.mark.parametrize("wrong_id", [False, True])
def test_targeted_composer_retry_preserves_valid_questions_and_checks_id(wrong_id, tmp_path):
    slots = [slot for slot in request().slots if slot.part == "P3"]
    questions = [question(slot).model_dump() for slot in slots]
    questions[1]["answer"] = "1178,1"
    replacement = {
        **questions[1],
        "stem": "Tính $1{,}2+0{,}3$.",
        "solution": "$1{,}2+0{,}3=1{,}5$.",
        "answer": "1,5",
        "id": "P3-1" if wrong_id else "P3-2",
    }
    provider = Responses(
        [
            json.dumps({"questions": questions}),
            json.dumps({"questions": [replacement]}),
        ]
    )
    calls = []
    invocation = ComposerAgent().run(
        RecordingProvider(provider, "composer", 1, calls, tmp_path),
        {"part": "P3", "slots": [slot.model_dump() for slot in slots]},
    )
    if wrong_id:
        with pytest.raises(ContractError) as exc:
            asyncio.run(invocation)
        assert exc.value.fields[0]["type"] == "repair_binding"
        assert calls[-1]["status"] == "invalid_contract"
    else:
        result, _ = asyncio.run(invocation)
        assert [item.model_dump() for item in result.questions] == [
            questions[0],
            replacement,
            *questions[2:],
        ]
    assert len(calls) == 2
    retry = provider.requests[1]
    assert [slot["id"] for slot in retry["slots"]] == ["P3-2"]
    assert retry["output_schema"]["properties"]["questions"]["maxItems"] == 1
    assert retry["contract_feedback"]["previous_questions"] == [questions[1]]
    assert "one question per" in provider.instructions[1]
    assert "six numeric short answers" not in provider.instructions[1]


def test_variation_arrows_are_valid_math():
    assert prose(r"$+\infty \searrow 0 \nearrow +\infty$") == (
        r"$+\infty \searrow 0 \nearrow +\infty$"
    )


def test_native_tikz_plot_variable_is_allowed_only_in_drawings():
    validate_drawing_code(r"\begin{tikzpicture}\draw plot (\x,{\x*\x});\end{tikzpicture}")
    with pytest.raises(ValueError):
        prose(r"$\x$")


def test_transient_error_retries_once_and_records_both_attempts(tmp_path):
    provider = Responses(
        [
            ProviderError("provider_unavailable", "HTTP 503", http_status=503),
            json.dumps({"questions": [question(request().slots[0]).model_dump()]}),
        ]
    )
    calls = []
    traced = RecordingProvider(provider, "composer", 1, calls, tmp_path, retries=1)
    asyncio.run(ComposerAgent().run(traced, {}))
    assert [c["status"] for c in calls] == ["failed", "validated"]
