"""Composition and resource ownership shared by REST and offline CLI execution."""

from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager

import httpx

from exam_baseline.baseline.agent import SingleExamAgent
from exam_baseline.baseline.context import JsonContextLoader
from exam_baseline.baseline.evaluation import Evaluator, JsonEvaluationRecorder
from exam_baseline.baseline.prompting import PromptBuilder
from exam_baseline.baseline.service import GenerationService
from exam_baseline.config import Settings
from exam_baseline.core.contracts import LLMProvider
from exam_baseline.core.validation import ExamValidator
from exam_baseline.providers.chat_completions import ChatCompletionsProvider
from exam_baseline.providers.mock import MockProvider


def build_service(settings: Settings, provider: LLMProvider) -> GenerationService:
    return GenerationService(
        agent=SingleExamAgent(
            provider, PromptBuilder(settings.prompt_version), settings.max_prompt_chars
        ),
        loader=JsonContextLoader(),
        validator=ExamValidator(),
        evaluator=Evaluator(settings),
        recorder=JsonEvaluationRecorder(settings.evaluation_jsonl),
    )


@asynccontextmanager
async def service_scope(
    settings: Settings,
    provider: LLMProvider | None = None,
) -> AsyncIterator[GenerationService]:
    async with AsyncExitStack() as resources:
        if provider is None:
            if settings.provider == "mock":
                provider = MockProvider(model=settings.model)
            else:
                client = await resources.enter_async_context(
                    httpx.AsyncClient(follow_redirects=False)
                )
                provider = ChatCompletionsProvider(settings, client)
        yield build_service(settings, provider)
