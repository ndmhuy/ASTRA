"""Generate a THPT mathematics paper using the locked user template."""

import argparse
import asyncio
import json
from pathlib import Path

import httpx
from pydantic import ValidationError

from exam_baseline.config import Settings
from exam_baseline.core.contracts import ProviderError
from exam_baseline.providers.chat_completions import ChatCompletionsProvider
from exam_baseline.thpt.models import Request
from exam_baseline.thpt.orchestrator import Orchestrator
from exam_baseline.thpt.runtime import ContractError


async def run(args):
    request = Request.model_validate_json(args.request.read_bytes())
    settings = Settings()
    if settings.provider != "chat_completions":
        raise ValueError("Configure EXAM_PROVIDER=chat_completions in .env")
    # Enforce the actual per-stage schema at the API boundary, not only in the prompt.
    settings = settings.model_copy(update={"response_format": "json_schema"})
    async with httpx.AsyncClient(follow_redirects=False) as client:
        provider = ChatCompletionsProvider(settings, client)
        return await Orchestrator(
            dict.fromkeys(("composer", "illustrator", "solver", "reviewer"), provider)
        ).run(request, args.output, resume=args.resume)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resume", action="store_true", help="Continue an interrupted run")
    args = parser.parse_args()
    if args.output.exists() and not args.resume:
        parser.error("output directory already exists")
    try:
        result = asyncio.run(run(args))
    except ContractError as exc:
        print(
            json.dumps(
                {
                    "error": "invalid_contract",
                    "stage": exc.stage,
                    "fields": exc.fields,
                    "report": str(args.output / "_internal/result.json"),
                }
            )
        )
        return 1
    except ValidationError as exc:
        print(
            json.dumps(
                {
                    "error": "invalid_contract",
                    "fields": [
                        {"location": e["loc"], "type": e["type"]}
                        for e in exc.errors(include_input=False, include_url=False)
                    ],
                }
            )
        )
        return 1
    except ProviderError as exc:
        print(json.dumps({"error": exc.code, "message": str(exc)}))
        return 1
    except (ValueError, OSError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
