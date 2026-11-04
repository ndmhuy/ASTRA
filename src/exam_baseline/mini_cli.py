"""Create an unreviewed ASTRA mini draft from a request and provider or fixture."""

import argparse
import asyncio
import json
from pathlib import Path

import httpx

from .config import Settings
from .contracts import Completion
from .mini import MiniRequest, StageResult, create_draft, private_artifact_path
from .providers.chat_completions import ChatCompletionsProvider


class FixtureProvider:
    """Replay a Composer response; never describe this as a live generation."""

    name = "fixture"
    model = "fixture"
    parameters = {}

    def __init__(self, path: Path):
        self.path = path

    async def complete(self, request):
        return Completion(text=self.path.read_text(encoding="utf-8"), model=self.model)


async def run(args) -> int:
    payload = MiniRequest.model_validate_json(args.request.read_text(encoding="utf-8"))
    if args.fixture:
        result = await create_draft(payload, FixtureProvider(args.fixture), args.output)
    else:
        settings = Settings()
        if settings.provider != "chat_completions":
            raise ValueError("Live draft requires EXAM_PROVIDER=chat_completions")
        async with httpx.AsyncClient(follow_redirects=False) as client:
            result = await create_draft(
                payload, ChatCompletionsProvider(settings, client), args.output
            )
    if isinstance(result, StageResult):
        print(result.model_dump_json(indent=2))
        return 1
    print(
        json.dumps(
            {
                "draft": str(args.output / "exam_draft.json"),
                "student": str(args.output / "student_view.json"),
                "teacher_private": str(private_artifact_path(args.output, result.draft_id)),
                "composer": result.composer.status,
                "illustrator": result.illustrator.status,
            },
            ensure_ascii=False,
        )
    )
    return 0 if result.illustrator.status != "failed" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, help="Replay a Composer JSON fixture")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output directory already exists")
    return asyncio.run(run(args))


if __name__ == "__main__":
    raise SystemExit(main())
