"""Shared structured model calls; prompts and content contracts are injected."""

import json
from collections.abc import Callable

from pydantic import ValidationError

from exam_baseline.core.contracts import CompletionRequest, ImageInput, LLMProvider
from exam_baseline.pipeline.agents.responses import ResponseContract, ResponseT
from exam_baseline.pipeline.errors import StageContractError


async def structured_stage(
    provider: LLMProvider,
    stage: str,
    data: dict,
    contract: ResponseContract[ResponseT],
    images: tuple[ImageInput, ...],
    schema_repairs: int,
    validate: Callable[[ResponseT], None],
    *,
    system: str,
) -> ResponseT:
    """Schema correction is visible, bounded, and always uses the original scoped view."""
    feedback = None
    output_schema = contract.schema(data)
    for _ in range(schema_repairs + 1):
        completion = await provider.complete(
            CompletionRequest(
                system=system,
                user=json.dumps(
                    {
                        "input": data,
                        "output_schema": output_schema,
                        "contract_feedback": feedback,
                    },
                    ensure_ascii=False,
                ),
                output_schema=output_schema,
                images=images,
            )
        )
        try:
            result = contract.parse(completion.text, data)
            validate(result)
            return result
        except (ValidationError, ValueError) as exc:
            if hasattr(provider, "result") and provider.result.calls:
                provider.result.calls[-1].error_code = "invalid_stage_contract"
            if isinstance(exc, ValidationError):
                feedback = [
                    {"location": list(e["loc"]), "type": e["type"], "message": e["msg"]}
                    for e in exc.errors(include_input=False, include_url=False)
                ]
            else:
                feedback = str(exc)
    raise StageContractError(stage, f"{stage} output failed contract checks: {feedback}")
