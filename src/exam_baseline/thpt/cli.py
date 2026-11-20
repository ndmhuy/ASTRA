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
from exam_baseline.thpt.planner import plan_request_from_prompt
from exam_baseline.thpt.rag import (
    DEFAULT_CORPUS_REF,
    RagHandoffError,
    default_request,
    retrieve_request,
)
from exam_baseline.thpt.runtime import ContractError


def _load_prompt_text(args) -> str | None:
    if getattr(args, "prompt", None):
        return args.prompt
    if getattr(args, "prompt_file", None):
        return args.prompt_file.read_text(encoding="utf-8")
    return None


async def run(args, request_model=Request, workflow_type=Orchestrator):
    prompt_text = _load_prompt_text(args)
    use_rag = bool(getattr(args, "rag", False) or prompt_text)
    if args.resume and use_rag and prompt_text:
        request = Request.model_validate_json((args.output / "_internal/request.json").read_bytes())
        if not request.rag_evidence:
            raise ValueError("Resume with --prompt requires an original RAG-enabled run")
    elif prompt_text:
        request = plan_request_from_prompt(
            prompt_text,
            corpus_ref=args.rag_corpus_ref,
            pack_dir=args.rag_pack_dir,
        )
    elif args.request:
        request = request_model.model_validate_json(args.request.read_bytes())
    else:
        request = default_request()
    if args.composer_concurrency is not None:
        request.composer_concurrency = args.composer_concurrency
    if getattr(args, "solver_concurrency", None) is not None:
        request.solver_concurrency = args.solver_concurrency
    if use_rag and not (args.resume and prompt_text):
        if args.resume:
            saved = Request.model_validate_json(
                (args.output / "_internal/request.json").read_bytes()
            )
            if not saved.rag_evidence:
                raise ValueError("Resume with --rag requires an original RAG-enabled run")
            request.rag_evidence = saved.rag_evidence
        else:
            request = retrieve_request(
                request, corpus_ref=args.rag_corpus_ref, pack_dir=args.rag_pack_dir
            )
    if getattr(args, "plan_only", False):
        args.output.mkdir(parents=True, exist_ok=False)
        (args.output / "planned_request.json").write_text(
            json.dumps(request.model_dump(exclude={"rag_evidence"}), ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )
        audit = {
            "status": "planned",
            "slot_count": len(request.slots),
            "requirements": request.requirements,
            "slots": [slot.model_dump() for slot in request.slots],
            "rag_evidence": {
                qid: passage.model_dump(exclude={"text"})
                for qid, passage in request.rag_evidence.items()
            },
        }
        (args.output / "rag_audit.json").write_text(
            json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return audit
    settings = Settings()
    if settings.provider != "chat_completions":
        raise ValueError("Configure EXAM_PROVIDER=chat_completions in .env")
    # Enforce the actual per-stage schema at the API boundary, not only in the prompt.
    settings = settings.model_copy(update={"response_format": "json_schema"})
    async with httpx.AsyncClient(follow_redirects=False) as client:
        provider = ChatCompletionsProvider(settings, client)
        return await workflow_type(
            dict.fromkeys(("composer", "illustrator", "solver", "reviewer"), provider)
        ).run(request, args.output, resume=args.resume)


def main(workflow_type=Orchestrator, request_model=Request, description=__doc__):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--request", type=Path, required=request_model is not Request)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resume", action="store_true", help="Continue an interrupted run")
    parser.add_argument(
        "--composer-concurrency",
        type=int,
        choices=(1, 2, 3),
        default=None,
        help="Parallel Composer sections; 1 preserves sequential execution",
    )
    if "solver_concurrency" in request_model.model_fields:
        parser.add_argument("--solver-concurrency", type=int, choices=(1, 2, 3), default=None)
    if request_model is Request:
        parser.add_argument(
            "--rag", action="store_true", help="Retrieve context for each THPT slot"
        )
        parser.add_argument(
            "--prompt",
            help="Vietnamese exam prompt; plans a RAG-verified 22-slot THPT matrix automatically",
        )
        parser.add_argument(
            "--prompt-file",
            type=Path,
            help="UTF-8 file containing the Vietnamese exam prompt",
        )
        parser.add_argument(
            "--plan-only",
            action="store_true",
            help="Write planned_request.json and rag_audit.json without calling an LLM provider",
        )
        parser.add_argument("--rag-corpus-ref", default=DEFAULT_CORPUS_REF)
        parser.add_argument("--rag-pack-dir", type=Path)
    args = parser.parse_args()
    if request_model is Request:
        sources = sum(bool(x) for x in (args.request, args.prompt, args.prompt_file))
        if sources > 1:
            parser.error("use only one of --request, --prompt, or --prompt-file")
        if sources == 0 and not args.rag:
            parser.error("--request, --prompt, --prompt-file, or --rag is required")
        if args.plan_only and not (args.rag or args.prompt or args.prompt_file):
            parser.error("--plan-only requires --rag, --prompt, or --prompt-file")
    if args.output.exists() and not args.resume:
        parser.error("output directory already exists")
    try:
        result = asyncio.run(run(args, request_model, workflow_type))
    except RagHandoffError as exc:
        print(json.dumps({"error": "retrieval_gap", "gaps": exc.gaps}, ensure_ascii=False))
        return 1
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
