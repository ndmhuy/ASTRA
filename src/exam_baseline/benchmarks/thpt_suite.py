"""Scientific OFAT THPT Math Benchmark Runner (4 architectures x Gemini 2.5/3.1/3.8).

Runs controlled single-factor experiments across:
- Architecture: naive_chat, single_shot_rag, astra_seq, astra_par
- Model & reasoning_effort: gemini-2.5-flash-lite, gemini-3.1-flash-lite, gemini-3.8-flash
- Hero Comparison: weak model + ASTRA vs strong model + naive baseline

Supports Free-Tier resilience via JSONL checkpointing (`--resume`), retry-wait
separation (`api_compute_seconds` vs `rate_limit_wait_seconds`), and offline
`--mode replay` for plumbing verification without network calls.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import shutil
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from time import perf_counter
from typing import Literal

import httpx
from pydantic import Field

from exam_baseline.benchmarks.thpt_replay import ReplayThptProvider
from exam_baseline.config import Settings
from exam_baseline.core.contracts import CompletionRequest, LLMProvider, ProviderError
from exam_baseline.core.models import Model
from exam_baseline.pipeline.rendering.compiler import compile_document, find_compiler
from exam_baseline.providers.chat_completions import ChatCompletionsProvider
from exam_baseline.thpt import template as thpt_template
from exam_baseline.thpt.agents import ComposerAgent, IllustratorAgent
from exam_baseline.thpt.metrics import DEFAULT_USD_TO_VND, summarize_calls
from exam_baseline.thpt.models import RagPassage, Request
from exam_baseline.thpt.orchestrator import Orchestrator, save
from exam_baseline.thpt.planner import plan_request_from_prompt
from exam_baseline.thpt.rag import DEFAULT_CORPUS_REF, default_request, retrieve_request
from exam_baseline.thpt.rendering import render
from exam_baseline.thpt.runtime import ContractError, RecordingProvider

Architecture = Literal["naive_chat", "single_shot_rag", "astra_seq", "astra_par"]
ExperimentId = Literal["E1_architecture", "E2_model_reasoning", "E3_hero_comparison"]
ReasoningEffort = Literal["none", "minimal", "low", "medium", "high", "xhigh"]
CompileMode = Literal["auto", "require", "skip"]

SCORED_UNITS_PER_EXAM = 34  # 12 P1 + (4 x 4) P2 statements + 6 P3

NAIVE_SYSTEM_PROMPT = """Bạn là giáo viên Toán THPT tại Việt Nam.
Hãy soạn một đề thi thử Toán THPT đầy đủ gồm đúng 22 câu theo cấu trúc mới:
- PHẦN I: 12 câu trắc nghiệm nhiều phương án lựa chọn (Câu 1..12, mỗi câu đúng 4 phương án A/B/C/D).
- PHẦN II: 4 câu trắc nghiệm đúng sai (Câu 1..4, mỗi câu có 4 ý a, b, c, d).
- PHẦN III: 6 câu trắc nghiệm trả lời ngắn (Câu 1..6, đáp án là một số cụ thể).

Xuất đề thi hoàn chỉnh dạng LaTeX hợp lệ trong \\documentclass...\\begin{document}...\\end{document}
để biên dịch trực tiếp ra PDF cho học sinh (KHÔNG ghi đáp án hay lời giải bên trong thân đề thi).
Sau thẻ \\end{document}, cung cấp bảng đáp án và lời giải tóm tắt cho từng câu để giáo viên chấm."""

_LATEX_DOC_RE = re.compile(r"(\\documentclass[\s\S]*?\\end\{document\})")
_LEAK_RE = re.compile(
    r"(?:^|\n)\s*(?:\\noindent\s*)?(?:\\textbf\{)?(?:Đáp\s*án|Lời\s*giải|Hướng\s*dẫn\s*giải)\s*[:.]",
    flags=re.IGNORECASE,
)
_QUESTION_MARKER_RE = re.compile(
    r"(?:^|\n)\s*(?:\\noindent\s*)?(?:\\textbf\{)?Câu\s+\d+\s*[:.]",
)


class ThptBenchmarkCase(Model):
    id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=200)
    prompt: str = Field(min_length=10, max_length=2000)
    focus_topics: list[str] = Field(default_factory=list)
    request_path: str | None = None


class ThptRunSpec(Model):
    id: str = Field(min_length=1, max_length=80)
    experiment: ExperimentId
    label: str = Field(min_length=1, max_length=140)
    architecture: Architecture
    model: str = Field(min_length=1, max_length=100)
    reasoning_effort: ReasoningEffort | None = None
    temperature: float | None = Field(default=0.0, ge=0.0, le=2.0)
    seed: int | None = 42
    repeats: int = Field(default=1, ge=1, le=10)


class ThptSuiteManifest(Model):
    schema_version: Literal["thpt-benchmark-v1"] = "thpt-benchmark-v1"
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=1000)
    usd_to_vnd_rate: float = Field(default=DEFAULT_USD_TO_VND, gt=0)
    cost_target_vnd: float = Field(default=2_000.0, gt=0)
    cases: list[ThptBenchmarkCase] = Field(min_length=1)
    runs: list[ThptRunSpec] = Field(min_length=1)


def extract_latex_document(text: str) -> str | None:
    match = _LATEX_DOC_RE.search(text)
    return match.group(1).strip() if match else None


def inspect_latex_template(
    latex_text: str | None,
    *,
    tex_path: Path | None,
    compile_mode: CompileMode,
    compiler: str | Path | None = None,
    latex_timeout: float = 180.0,
    latex_cache_dir: Path | None = None,
) -> dict:
    """Deterministically inspect template structure, leakage, and optional PDF compilation."""
    if not latex_text or not latex_text.strip():
        return {
            "has_latex_document": False,
            "locked_template_preserved": False,
            "question_count_detected": 0,
            "has_all_three_parts": False,
            "zero_answer_leakage": False,
            "template_structure_ok": False,
            "pdf_compile_status": "not_run",
            "template_pass": False,
        }

    has_doc = (
        r"\documentclass" in latex_text
        and r"\begin{document}" in latex_text
        and r"\end{document}" in latex_text
    )
    body = latex_text
    if r"\begin{document}" in body:
        body = body.split(r"\begin{document}", 1)[1]
    if r"\end{document}" in body:
        body = body.split(r"\end{document}", 1)[0]

    q_count = len(_QUESTION_MARKER_RE.findall(body))
    upper_body = body.upper()
    has_p1 = "PHẦN I" in upper_body or "LECTURING-PART: P1" in upper_body
    has_p2 = "PHẦN II" in upper_body or "LECTURING-PART: P2" in upper_body
    has_p3 = "PHẦN III" in upper_body or "LECTURING-PART: P3" in upper_body
    has_three_parts = has_p1 and has_p2 and has_p3
    zero_leakage = _LEAK_RE.search(body) is None
    locked_preserved = "% LECTURING-PART: P1" in latex_text and "% LECTURING-PART: P3" in latex_text
    structure_ok = has_doc and has_three_parts and q_count == 22 and zero_leakage

    pdf_status = "skipped"
    if compile_mode != "skip" and tex_path is not None and tex_path.is_file():
        resolved_compiler = find_compiler(compiler)
        if resolved_compiler is None:
            if compile_mode == "require":
                pdf_status = "failed_no_compiler"
            else:
                pdf_status = "skipped_no_compiler"
        else:
            try:
                compile_document(
                    tex_path,
                    compiler=resolved_compiler,
                    timeout=latex_timeout,
                    cache_directory=latex_cache_dir,
                )
                pdf_status = "passed"
            except ValueError as exc:
                pdf_status = f"failed:{exc}"

    compile_ok = (
        pdf_status == "passed"
        if compile_mode == "require"
        else (not pdf_status.startswith("failed"))
    )
    return {
        "has_latex_document": has_doc,
        "locked_template_preserved": locked_preserved,
        "question_count_detected": q_count,
        "has_all_three_parts": has_three_parts,
        "zero_answer_leakage": zero_leakage,
        "template_structure_ok": structure_ok,
        "pdf_compile_status": pdf_status,
        "template_pass": bool(structure_ok and compile_ok),
    }


def summarize_rag_citations(request: Request | None) -> dict:
    if request is None or not request.rag_evidence:
        return {
            "rag_slots_with_evidence": 0,
            "rag_citation_locator_valid": 0,
            "rag_unique_sources": 0,
        }
    valid = 0
    sources: set[str] = set()
    for passage in request.rag_evidence.values():
        sources.update(passage.source_ids)
        if passage.source_ids and passage.source_locator.strip() and passage.source_version.strip():
            valid += 1
    return {
        "rag_slots_with_evidence": len(request.rag_evidence),
        "rag_citation_locator_valid": valid,
        "rag_unique_sources": len(sources),
    }


def attach_replay_rag_evidence(request: Request, case: ThptBenchmarkCase) -> Request:
    """Attach deterministic offline RAG passages so replay tests citation checks cleanly."""
    evidence = {}
    for slot in request.slots:
        unit = slot.curriculum_unit_ids[0] if slot.curriculum_unit_ids else f"unit-{slot.part}"
        source_id = f"replay-sgk-{slot.part.lower()}"
        evidence[slot.id] = RagPassage(
            text=(
                f"=== [UNTRUSTED_RAG_EVIDENCE | question_id={slot.id} | source={source_id}] ===\n"
                f"Chủ đề: {slot.topic}. Mục tiêu: {slot.objective}. Ngữ cảnh: {case.title}."
            ),
            source_ids=[source_id],
            source_locator=f"sgk-toan-12/{slot.part.lower()}/{slot.id.lower()}.md#L1-L20",
            source_version="replay-fixture-v1",
            curriculum_unit_ids=[unit],
            warnings=[],
        )
    return request.model_copy(update={"rag_evidence": evidence})


def prepare_case_request(
    case: ThptBenchmarkCase,
    *,
    mode: Literal["replay", "live"],
    cache_dir: Path,
    rag_corpus_ref: str = DEFAULT_CORPUS_REF,
    rag_pack_dir: Path | None = None,
) -> Request:
    """Build or load the exact frozen 22-slot RAG Request shared across OFAT architectures."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached_path = cache_dir / f"{case.id}_request.json"
    if cached_path.is_file():
        return Request.model_validate_json(cached_path.read_bytes())

    if mode == "replay":
        base = (
            Request.model_validate_json(Path(case.request_path).read_bytes())
            if case.request_path
            else default_request()
        )
        reqs = list(base.requirements)
        marker = f"Yêu cầu giáo viên ({case.id}): {case.prompt}"
        if marker not in reqs:
            reqs.append(marker)
        prepared = attach_replay_rag_evidence(base.model_copy(update={"requirements": reqs}), case)
    else:
        if case.request_path:
            base = Request.model_validate_json(Path(case.request_path).read_bytes())
        else:
            base = plan_request_from_prompt(
                case.prompt,
                corpus_ref=rag_corpus_ref,
                pack_dir=rag_pack_dir,
            )
        prepared = retrieve_request(
            base,
            corpus_ref=rag_corpus_ref,
            pack_dir=rag_pack_dir,
            variant_key=f"benchmark-{case.id}",
        )
    save(cached_path, prepared.model_dump())
    return prepared


async def run_naive_chat(
    case: ThptBenchmarkCase,
    provider: LLMProvider,
    output: Path,
) -> dict:
    """Architecture 1: naive_chat ('ngu chat') — single prompt, no RAG, no template, no solver."""
    output.mkdir(parents=True, exist_ok=False)
    internal = output / "_internal"
    internal.mkdir()
    calls: list[dict] = []
    recorder = RecordingProvider(
        provider, "naive_chat", 1, calls, internal / "responses", retries=1
    )
    started = perf_counter()
    completion = await recorder.complete(
        CompletionRequest(
            system=NAIVE_SYSTEM_PROMPT,
            user=case.prompt,
            output_schema={},
        )
    )
    elapsed = round(perf_counter() - started, 3)
    (output / "raw_response.txt").write_text(completion.text, encoding="utf-8")
    extracted = extract_latex_document(completion.text)
    tex_path = None
    if extracted:
        tex_path = output / "de_thi.tex"
        tex_path.write_text(extracted, encoding="utf-8")
    report = {
        "execution_status": "completed",
        "architecture": "naive_chat",
        "final_latex": str(tex_path) if tex_path else None,
        "elapsed_seconds": elapsed,
        "calls": calls,
        "metrics": summarize_calls(calls),
        "revision": 1,
        "reviewer_feedback_sent": False,
        "review_issues": [],
        "solver_agreement": None,
    }
    save(internal / "result.json", report)
    return report


async def run_single_shot_rag(
    request: Request,
    providers: dict[str, LLMProvider],
    output: Path,
) -> dict:
    """Architecture 2: single_shot_rag ('ngu work') — RAG + locked template + Composer only."""
    output.mkdir(parents=True, exist_ok=False)
    internal = output / "_internal"
    internal.mkdir()
    save(internal / "request.json", request.model_dump())
    calls: list[dict] = []
    started = perf_counter()
    thpt_template.original()
    references = thpt_template.reference_parts()
    composer = ComposerAgent()
    questions = []
    for part in ("P1", "P2", "P3"):
        recorder = RecordingProvider(
            providers["composer"], "composer", 1, calls, internal / "responses", retries=1
        )
        data = composer.data(request, part, references[part], feedback=None)
        section, _ = await composer.run(recorder, data)
        expected = [slot.id for slot in request.slots if slot.part == part]
        if [q.id for q in section.questions] != expected:
            raise ValueError("Composer question IDs/count/order differ from matrix")
        questions.extend(section.questions)

    illustrator = IllustratorAgent()
    ill_recorder = RecordingProvider(
        providers["illustrator"], "illustrator", 1, calls, internal / "responses", retries=1
    )
    drawings, _ = await illustrator.run(
        ill_recorder,
        {
            "requests": [
                {"question_id": q.id, "stem": q.stem, "description": q.illustration_request}
                for q in questions
                if q.illustration_request
            ]
        },
    )
    source = render(questions, drawings, font_profile=request.font_profile)
    tex_path = output / "de_thi.tex"
    tex_path.write_bytes(source)
    save(
        output / "dap_an_va_loi_giai.json",
        {
            "status": "pending_human_review",
            "revision": 1,
            "composer": [q.model_dump() for q in questions],
            "independent_solver": None,
        },
    )
    elapsed = round(perf_counter() - started, 3)
    report = {
        "execution_status": "completed",
        "architecture": "single_shot_rag",
        "final_latex": str(tex_path),
        "elapsed_seconds": elapsed,
        "calls": calls,
        "metrics": summarize_calls(calls),
        "revision": 1,
        "reviewer_feedback_sent": False,
        "review_issues": [],
        "solver_agreement": None,
    }
    save(internal / "result.json", report)
    return report


def _build_live_settings(base: Settings, spec: ThptRunSpec) -> Settings:
    if base.provider != "chat_completions":
        raise ValueError("Live benchmark requires EXAM_PROVIDER=chat_completions in .env")
    updated = base.model_copy(
        update={
            "model": spec.model,
            "reasoning_effort": spec.reasoning_effort,
            "temperature": spec.temperature,
            "seed": spec.seed,
        }
    )
    if spec.architecture == "naive_chat":
        return updated.model_copy(
            update={
                "response_format": "text",
                "structured_output_strict": False,
                "schema_as_tool": False,
            }
        )
    return updated.for_agent_generation()


def _attempt_key(run_id: str, case_id: str, repeat: int) -> str:
    return f"{run_id}__{case_id}__r{repeat}"


def _attempt_dir(suite_output: Path, attempt_key: str) -> Path:
    """Compact opaque attempt folder preventing Windows MAX_PATH overflows and blind leaks."""
    digest = sha256(attempt_key.encode("utf-8")).hexdigest()[:10]
    return suite_output / "r" / digest


def _load_existing_attempts(jsonl_path: Path) -> dict[str, dict]:
    records: dict[str, dict] = {}
    if not jsonl_path.is_file():
        return records
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        records[item["attempt_key"]] = item
    return records


def _append_attempt(jsonl_path: Path, record: dict) -> None:
    with jsonl_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


async def execute_attempt(
    spec: ThptRunSpec,
    case: ThptBenchmarkCase,
    repeat: int,
    *,
    mode: Literal["replay", "live"],
    suite_output: Path,
    case_request: Request,
    usd_to_vnd_rate: float,
    compile_mode: CompileMode,
    base_settings: Settings | None = None,
    replay_factory=None,
) -> dict:
    """Execute one (run, case, repeat) attempt and return its normalized benchmark record."""
    attempt_key = _attempt_key(spec.id, case.id, repeat)
    attempt_dir = _attempt_dir(suite_output, attempt_key)
    if attempt_dir.exists():
        shutil.rmtree(attempt_dir)
    attempt_dir.parent.mkdir(parents=True, exist_ok=True)

    run_request = case_request.model_copy(
        update={"composer_concurrency": 3 if spec.architecture == "astra_par" else 1}
    )

    started = perf_counter()
    report: dict | None = None
    error_code: str | None = None
    error_message: str | None = None

    try:
        if mode == "replay":
            if replay_factory is not None:
                providers = replay_factory(spec, case, run_request)
            else:
                trigger_rev = spec.architecture in {"astra_seq", "astra_par"} and (
                    spec.model == "gemini-2.5-flash-lite"
                )
                naive_complete = spec.model == "gemini-3.8-flash"
                naive_leak = spec.model != "gemini-3.8-flash"
                providers = {
                    role: ReplayThptProvider(
                        role=role,
                        model=spec.model,
                        request=run_request,
                        trigger_revision=trigger_rev,
                        naive_complete=naive_complete,
                        naive_leak=naive_leak,
                    )
                    for role in ("naive_chat", "composer", "illustrator", "solver", "reviewer")
                }
            report = await _dispatch_architecture(
                spec.architecture, case, run_request, providers, attempt_dir
            )
        else:
            settings = _build_live_settings(base_settings or Settings(), spec)
            async with httpx.AsyncClient(follow_redirects=False) as client:
                provider = ChatCompletionsProvider(settings, client)
                providers = dict.fromkeys(
                    ("naive_chat", "composer", "illustrator", "solver", "reviewer"), provider
                )
                report = await _dispatch_architecture(
                    spec.architecture, case, run_request, providers, attempt_dir
                )
    except ProviderError as exc:
        error_code = exc.code
        error_message = str(exc)
    except ContractError as exc:
        error_code = f"invalid_contract:{exc.stage}"
        error_message = str(exc)
    except Exception as exc:  # noqa: BLE001 — record terminal attempt failure in denominator
        error_code = type(exc).__name__
        error_message = str(exc)

    wall_seconds = round(perf_counter() - started, 3)

    # Load partial _internal/result.json if execution failed midway so costs stay counted.
    internal_result = attempt_dir / "_internal" / "result.json"
    if report is None and internal_result.is_file():
        report = json.loads(internal_result.read_text(encoding="utf-8"))

    calls = (report or {}).get("calls", [])
    metrics = summarize_calls(calls, usd_to_vnd_rate=usd_to_vnd_rate)

    tex_path = attempt_dir / "de_thi.tex"
    latex_text = tex_path.read_text(encoding="utf-8") if tex_path.is_file() else None
    compiler = base_settings.latex_compiler if base_settings else None
    latex_cache = base_settings.latex_cache_dir if base_settings else None
    latex_timeout = base_settings.latex_timeout_seconds if base_settings else 180.0
    template_eval = inspect_latex_template(
        latex_text,
        tex_path=tex_path if tex_path.is_file() else None,
        compile_mode=compile_mode,
        compiler=compiler,
        latex_timeout=latex_timeout,
        latex_cache_dir=latex_cache,
    )

    completed = error_code is None and (report or {}).get("execution_status") == "completed"
    if not completed:
        template_eval["template_pass"] = False

    citations = summarize_rag_citations(None if spec.architecture == "naive_chat" else run_request)
    agreement = (report or {}).get("solver_agreement")
    review_issues = (report or {}).get("review_issues") or []
    reviewer_ran = spec.architecture in {"astra_seq", "astra_par"} and any(
        c.get("role") == "reviewer" for c in calls
    )

    rel_dir = attempt_dir.relative_to(suite_output).as_posix()
    return {
        "attempt_key": _attempt_key(spec.id, case.id, repeat),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "run_id": spec.id,
        "experiment": spec.experiment,
        "label": spec.label,
        "architecture": spec.architecture,
        "model": spec.model,
        "reasoning_effort": spec.reasoning_effort,
        "case_id": case.id,
        "case_title": case.title,
        "repeat": repeat,
        "status": "completed" if completed else "failed",
        "error_code": error_code,
        "error_message": error_message,
        "output_dir": rel_dir,
        # Priority 1: Template
        **template_eval,
        # Priority 2: Math (human grading fills exact x/34; solver agreement is diagnostic proxy)
        "scored_units_total": SCORED_UNITS_PER_EXAM,
        "solver_agreed_questions": agreement["agreed_count"] if agreement else None,
        "solver_mismatched_questions": agreement["mismatched_count"] if agreement else None,
        "solver_unparsed_questions": agreement["unparsed_count"] if agreement else None,
        # Priority 3: Citations (auto locator check; human grounding fills exact ratio)
        **citations,
        # Priority 4: Validator (end-to-end catch & revision telemetry)
        "reviewer_ran": reviewer_ran,
        "reviewer_issues_count": len(review_issues),
        "reviewer_feedback_sent": bool((report or {}).get("reviewer_feedback_sent", False)),
        "revision_count": (report or {}).get("revision", 1 if completed else 0),
        # Priority 5: Compliance (auto slot coverage; human audit fills prompt/reference adherence)
        "slot_coverage_ratio": round(min(template_eval["question_count_detected"], 22) / 22, 4),
        "requirements_count": len(run_request.requirements),
        # Priority 6: Cost
        "input_tokens": metrics["input_tokens"],
        "output_tokens": metrics["output_tokens"],
        "cost_usd": metrics["standard_price_estimate_usd"],
        "cost_vnd": metrics["standard_price_estimate_vnd"],
        "cost_coverage": metrics["cost_coverage"],
        "estimate_complete": metrics["estimate_complete"],
        "by_stage": metrics["by_stage"],
        # Priority 7: Latency
        "wall_seconds": wall_seconds,
        "api_compute_seconds": metrics["api_seconds_sum"],
        "rate_limit_wait_seconds": metrics["retry_wait_seconds"],
        "call_count": len(calls),
    }


async def _dispatch_architecture(
    architecture: Architecture,
    case: ThptBenchmarkCase,
    request: Request,
    providers: dict[str, LLMProvider],
    output: Path,
) -> dict:
    if architecture == "naive_chat":
        return await run_naive_chat(case, providers["naive_chat"], output)
    if architecture == "single_shot_rag":
        return await run_single_shot_rag(request, providers, output)
    if architecture in {"astra_seq", "astra_par"}:
        return await Orchestrator(providers).run(request, output)
    raise ValueError(f"Unsupported architecture: {architecture}")


async def run_suite(
    manifest_path: Path,
    output: Path,
    *,
    mode: Literal["replay", "live"] = "replay",
    resume: bool = False,
    retry_failed: bool = False,
    compile_mode: CompileMode = "auto",
    experiment_filter: str | None = None,
    run_id_filter: set[str] | None = None,
    inter_attempt_sleep: float = 0.0,
    rag_corpus_ref: str = DEFAULT_CORPUS_REF,
    rag_pack_dir: Path | None = None,
    base_settings: Settings | None = None,
    replay_factory=None,
) -> dict:
    """Execute the THPT benchmark manifest with JSONL checkpointing and resumability."""
    manifest = ThptSuiteManifest.model_validate_json(manifest_path.read_bytes())
    if output.exists() and not resume:
        raise ValueError("output directory already exists; pass --resume to continue")
    output.mkdir(parents=True, exist_ok=True)
    save(output / "manifest_snapshot.json", manifest.model_dump())

    jsonl_path = output / "attempts.jsonl"
    existing = _load_existing_attempts(jsonl_path) if resume else {}

    selected_runs = [
        run
        for run in manifest.runs
        if (experiment_filter is None or run.experiment == experiment_filter)
        and (run_id_filter is None or run.id in run_id_filter)
    ]
    if not selected_runs:
        raise ValueError("No runs matched the requested filter")

    prepared_dir = output / "_prepared"
    case_requests = {
        case.id: prepare_case_request(
            case,
            mode=mode,
            cache_dir=prepared_dir,
            rag_corpus_ref=rag_corpus_ref,
            rag_pack_dir=rag_pack_dir,
        )
        for case in manifest.cases
    }

    executed_now = 0
    skipped = 0
    for spec in selected_runs:
        for case in manifest.cases:
            for repeat in range(1, spec.repeats + 1):
                key = _attempt_key(spec.id, case.id, repeat)
                prev = existing.get(key)
                if prev is not None and (prev["status"] == "completed" or not retry_failed):
                    skipped += 1
                    continue
                if executed_now > 0 and inter_attempt_sleep > 0:
                    await asyncio.sleep(inter_attempt_sleep)
                record = await execute_attempt(
                    spec,
                    case,
                    repeat,
                    mode=mode,
                    suite_output=output,
                    case_request=case_requests[case.id],
                    usd_to_vnd_rate=manifest.usd_to_vnd_rate,
                    compile_mode=compile_mode,
                    base_settings=base_settings,
                    replay_factory=replay_factory,
                )
                _append_attempt(jsonl_path, record)
                existing[key] = record
                executed_now += 1

    latest = list(existing.values())
    summary = {
        "schema_version": manifest.schema_version,
        "suite_name": manifest.name,
        "mode": mode,
        "total_recorded_attempts": len(latest),
        "executed_in_this_invocation": executed_now,
        "skipped_on_resume": skipped,
        "completed_attempts": sum(1 for a in latest if a["status"] == "completed"),
        "failed_attempts": sum(1 for a in latest if a["status"] != "completed"),
        "attempts_jsonl": str(jsonl_path),
        "note": (
            "Replay verifies orchestration, resume, and scoring plumbing ONLY; "
            "it is NOT a measurement of real model quality."
            if mode == "replay"
            else "Live metrics include all attempted calls and failed runs in the denominator. "
            "Human blind grading is required for exact Math/Citation/Compliance accuracy."
        ),
    }
    save(output / "suite_summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("examples/benchmarks/thpt_gemini_suite.json"),
        help="Path to the THPT OFAT benchmark manifest JSON.",
    )
    parser.add_argument("--output", type=Path, required=True, help="Output directory for run data.")
    parser.add_argument("--mode", choices=("replay", "live"), default="replay")
    parser.add_argument(
        "--resume", action="store_true", help="Resume from existing attempts.jsonl."
    )
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="When resuming, re-run attempts whose latest recorded status is failed.",
    )
    parser.add_argument(
        "--compile",
        dest="compile_mode",
        choices=("auto", "require", "skip"),
        default="auto",
        help="Local XeLaTeX/Tectonic compilation mode for template verification.",
    )
    parser.add_argument(
        "--experiment",
        choices=("E1_architecture", "E2_model_reasoning", "E3_hero_comparison"),
        default=None,
        help="Run only one OFAT experiment block from the manifest.",
    )
    parser.add_argument(
        "--run-id",
        action="append",
        default=None,
        help="Run only specific run ID(s) from the manifest (repeatable).",
    )
    parser.add_argument(
        "--inter-attempt-sleep",
        type=float,
        default=0.0,
        help="Optional pause (seconds) between attempts to respect Free Tier RPM.",
    )
    parser.add_argument("--rag-corpus-ref", default=DEFAULT_CORPUS_REF)
    parser.add_argument("--rag-pack-dir", type=Path, default=None)
    args = parser.parse_args()

    result = asyncio.run(
        run_suite(
            args.manifest,
            args.output,
            mode=args.mode,
            resume=args.resume,
            retry_failed=args.retry_failed,
            compile_mode=args.compile_mode,
            experiment_filter=args.experiment,
            run_id_filter=set(args.run_id) if args.run_id else None,
            inter_attempt_sleep=args.inter_attempt_sleep,
            rag_corpus_ref=args.rag_corpus_ref,
            rag_pack_dir=args.rag_pack_dir,
        )
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
