"""THPT policy: compose sections, illustrate, solve, review once, optional correction."""

import asyncio
import json
import re
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from pathlib import Path
from time import perf_counter
from typing import Literal

from exam_baseline.core.checkpoints import (
    CheckpointError,
    GenerationPaused,
    atomic_json,
    manifest,
    read_json,
    response_checkpoint,
    restore_response,
)
from exam_baseline.core.contracts import LLMProvider
from exam_baseline.thpt import template
from exam_baseline.thpt.agents import (
    ComposerAgent,
    IllustratorAgent,
    ReviewerAgent,
    SolverAgent,
)
from exam_baseline.thpt.metrics import summarize_calls
from exam_baseline.thpt.models import Request
from exam_baseline.thpt.rendering import render, student_view
from exam_baseline.thpt.runtime import ContractError, RecordingProvider


def save(path: Path, data):
    atomic_json(path, data)


_BOOL_TRUE = frozenset({"đúng", "dung", "đ", "d", "true", "t"})
_BOOL_FALSE = frozenset({"sai", "s", "false", "f"})


def _parse_p1_letter(answer: str) -> str | None:
    cleaned = answer.strip()
    if cleaned.upper() in {"A", "B", "C", "D"}:
        return cleaned.upper()
    match = re.fullmatch(
        r"(?:đáp\s*án|dap\s*an|chọn|chon)?\s*[:.]?\s*([ABCD])(?:[.):])?",
        cleaned,
        flags=re.IGNORECASE,
    )
    return match.group(1).upper() if match else None


def _parse_p2_booleans(answer: str) -> list[bool] | None:
    lowered = answer.casefold()
    labeled = re.findall(
        r"(?<![a-zà-ỹ])([a-d])\s*[):.\-=]\s*(đúng|dung|sai|true|false|đ|d|s|t|f)(?![a-zà-ỹ])",
        lowered,
    )
    if labeled:
        by_label = {label: token in _BOOL_TRUE for label, token in labeled}
        if set(by_label) == {"a", "b", "c", "d"}:
            return [by_label[k] for k in ("a", "b", "c", "d")]
    tokens = re.findall(r"(?<![a-zà-ỹ])(đúng|dung|sai|true|false|đ|s|t|f)(?![a-zà-ỹ])", lowered)
    if len(tokens) == 4:
        return [tok in _BOOL_TRUE for tok in tokens]
    return None


def _parse_p3_decimal(answer: str) -> Decimal | None:
    cleaned = answer.strip()
    match = re.fullmatch(r"(-?\d+(?:[.,]\d+)?)(?:\s*[^\d.,\s]{1,12})?", cleaned)
    if not match:
        return None
    try:
        return Decimal(match.group(1).replace(",", "."))
    except InvalidOperation:
        return None


AnswerCheck = Literal["matched", "mismatched", "needs_recheck"]


def compare_answer(question: dict, entry: dict | None) -> tuple[AnswerCheck, dict | None]:
    """Compare a question with its current independent solve, using its answer format."""
    if entry is None or entry["status"] != "solved":
        return "needs_recheck", None
    composer_key, solver_key = question.get("answer"), entry["answer"]
    if question.get("choices") and composer_key:
        actual = _parse_p1_letter(solver_key)
        if actual is None:
            return "needs_recheck", None
        expected = composer_key.strip().upper()
        solver_key = actual
    elif question.get("statements"):
        actual = _parse_p2_booleans(solver_key)
        expected = [statement["answer"] for statement in question["statements"]]
        if actual is None or len(actual) != len(expected):
            return "needs_recheck", None
        composer_key = "".join("Đ" if flag else "S" for flag in expected)
        solver_key = "".join("Đ" if flag else "S" for flag in actual)
    elif composer_key:
        actual = _parse_p3_decimal(solver_key)
        expected = _parse_p3_decimal(composer_key)
        if actual is None or expected is None:
            return "needs_recheck", None
        solver_key = solver_key.strip()
    else:
        return "needs_recheck", None
    if expected == actual:
        return "matched", None
    return "mismatched", {
        "question_id": question["id"],
        "composer": composer_key,
        "solver": solver_key,
    }


def compare_answers(questions, solutions) -> dict:
    """Deterministically compare Composer keys against Blind Solver answers."""
    by_id = {entry.question_id: entry.model_dump() for entry in solutions.entries}
    agreed = 0
    mismatched: list[dict] = []
    unparsed: list[str] = []
    for question in questions:
        check, mismatch = compare_answer(question.model_dump(), by_id.get(question.id))
        if check == "matched":
            agreed += 1
        elif mismatch is not None:
            mismatched.append(mismatch)
        else:
            unparsed.append(question.id)

    return {
        "agreed_count": agreed,
        "mismatched_count": len(mismatched),
        "unparsed_count": len(unparsed),
        "mismatched": mismatched,
        "unparsed": unparsed,
    }


class Orchestrator:
    request_model = Request
    template = template
    composer_type = ComposerAgent
    illustrator_type = IllustratorAgent
    solver_type = SolverAgent
    reviewer_type = ReviewerAgent
    max_revisions = 2

    def references(self, request):
        return self.template.reference_parts()

    def composer_data(self, composer, request, part, reference, feedback, previous_stems):
        return composer.data(request, part, reference, feedback)

    def parts(self, request):
        return ("P1", "P2", "P3")

    def validate_section(self, section, request, part):
        expected = [s.id for s in request.slots if s.part == part]
        if [q.id for q in section.questions] != expected:
            raise ValueError("Composer question IDs/count/order differ from matrix")

    def render_source(self, questions, drawings, request, sections):
        return render(questions, drawings, font_profile=request.font_profile)

    def extra_output(self, sections):
        return {}

    async def illustrate(self, call, questions, revision):
        return await call(
            self.illustrator_type(),
            dict(
                requests=[
                    dict(question_id=q.id, stem=q.stem, description=q.illustration_request)
                    for q in questions
                    if q.illustration_request
                ]
            ),
            revision,
        )

    async def solve(self, call, questions, drawings, revision, sections, request):
        return await call(
            self.solver_type(),
            dict(questions=student_view(questions), drawings=drawings.model_dump()),
            revision,
        )

    def review_data(self, request, questions, drawings, solutions, source, sections):
        data = dict(
            matrix=request.model_dump(exclude={"rag_evidence"}),
            questions=[q.model_dump() for q in questions],
            drawings=drawings.model_dump(),
            solver=solutions.model_dump(),
            student_latex=source.decode("utf-8"),
        )
        if isinstance(request, Request) and request.rag_evidence:
            data["rag_scope"] = {
                qid: {
                    "source_ids": passage.source_ids,
                    "curriculum_unit_ids": passage.curriculum_unit_ids,
                    "warnings": passage.warnings,
                }
                for qid, passage in request.rag_evidence.items()
            }
        return data

    def feedback_data(self, review, questions, sections):
        return dict(
            review=review.model_dump(), previous_questions=[q.model_dump() for q in questions]
        )

    def __init__(
        self,
        providers: dict[str, LLMProvider],
        *,
        on_progress=None,
        check_control=None,
        checkpoint_writer=None,
    ):
        self.providers = providers
        self.on_progress = on_progress
        self.check_control = check_control or (lambda: None)
        self.checkpoint_writer = checkpoint_writer or save

    async def run(
        self,
        request: Request,
        output: Path,
        *,
        resume: bool = False,
        checkpoint_sources: tuple[Path, ...] = (),
    ) -> dict:
        started = perf_counter()
        save = self.checkpoint_writer
        self.template.original()  # Verify before spending provider calls.
        references = self.references(request)
        internal = output / "_internal"
        calls = []
        previous_elapsed = 0.0
        expected_manifest = manifest(
            request.model_dump(),
            self.providers,
            f"{type(self).__module__}.{type(self).__qualname__}",
            self.template.TEMPLATE_SHA256,
        )
        if resume:
            previous = self.request_model.model_validate_json(
                (internal / "request.json").read_bytes()
            )
            if previous != request:
                raise ValueError("Resume requires the same input request")
            if read_json(internal / "checkpoint-manifest.json") != expected_manifest:
                raise CheckpointError(
                    "Generation configuration changed; checkpoint cannot be resumed"
                )
            report_path = internal / "result.json"
            previous_report = read_json(report_path) if report_path.is_file() else {}
            if previous_report.get("execution_status") == "completed":
                if (
                    not (output / "de_thi.tex").is_file()
                    or sha256((output / "de_thi.tex").read_bytes()).hexdigest()
                    != previous_report.get("latex_sha256")
                    or not (output / "dap_an_va_loi_giai.json").is_file()
                    or sha256((output / "dap_an_va_loi_giai.json").read_bytes()).hexdigest()
                    != previous_report.get("answers_sha256")
                ):
                    raise CheckpointError("Completed checkpoint artifacts changed")
                return previous_report
            calls = previous_report.get("calls", [])
            for previous_call in calls:
                if previous_call.get("status") in {"started", "response_received"}:
                    previous_call["status"] = "interrupted_uncertain"
            previous_elapsed = previous_report.get("elapsed_seconds", 0.0)
        else:
            output.mkdir(parents=True, exist_ok=False)
            internal.mkdir()
            save(internal / "request.json", request.model_dump())
            save(internal / "checkpoint-manifest.json", expected_manifest)
        checkpoints = internal / "checkpoints"
        checkpoints.mkdir(exist_ok=True)
        report = dict(
            execution_status="failed",
            human_review_required=True,
            template_sha256=self.template.TEMPLATE_SHA256,
            font_profile=request.font_profile,
            composer_concurrency=request.composer_concurrency,
            reviewer_feedback_sent=False,
            final_latex=None,
            calls=calls,
        )
        if isinstance(request, Request) and request.rag_evidence:
            report["rag_evidence"] = {
                question_id: passage.model_dump(exclude={"text"})
                for question_id, passage in request.rag_evidence.items()
            }

        async def call(agent, data, revision, validate=None):
            self.check_control()
            report["active_stage"] = agent.role
            report["active_part"] = data.get("part")
            if self.on_progress:
                self.on_progress(agent.role, data.get("part"), revision)
            fingerprint = sha256(
                json.dumps(
                    {
                        "role": agent.role,
                        "revision": revision,
                        "data": data,
                        "system": agent.common + agent.instruction,
                        "schema": agent.contract(data).model_json_schema(),
                        "template": self.template.TEMPLATE_SHA256,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ).encode()
            ).hexdigest()
            checkpoint = checkpoints / f"{fingerprint}.json"
            prior = next(
                (
                    path / checkpoint.name
                    for path in checkpoint_sources
                    if (path / checkpoint.name).is_file()
                ),
                checkpoint if resume and checkpoint.is_file() else None,
            )
            if prior is not None:
                response = restore_response(prior, fingerprint, agent.contract(data))
                if validate:
                    validate(response)
                if prior != checkpoint:
                    self.checkpoint_writer(checkpoint, response_checkpoint(fingerprint, response))
                return response
            provider = RecordingProvider(
                self.providers[agent.role],
                agent.role,
                revision,
                calls,
                internal / "responses",
                retries=0 if agent.role == "reviewer" else 1,
                on_attempt=lambda: save(internal / "result.json", report),
                operation_id=fingerprint,
            )
            try:
                response, _ = await agent.run(provider, data)
            except Exception:
                report["active_stage"] = agent.role
                report["active_part"] = data.get("part")
                raise
            if validate:
                validate(response)
            self.checkpoint_writer(
                checkpoint,
                {
                    **response_checkpoint(fingerprint, response),
                    "stage": agent.role,
                    "revision": revision,
                    "part": data.get("part"),
                },
            )
            save(internal / "result.json", report)
            self.check_control()
            return response

        try:
            feedback = None
            for revision in range(1, self.max_revisions + 1):
                folder = internal / f"revision_{revision}"
                folder.mkdir(exist_ok=resume)
                questions = []
                previous_stems = []
                composer = self.composer_type()
                semaphore = asyncio.Semaphore(request.composer_concurrency)

                async def compose_part(
                    part,
                    *,
                    semaphore=semaphore,
                    composer=composer,
                    feedback=feedback,
                    revision=revision,
                    folder=folder,
                    previous_stems=previous_stems,
                ):
                    async with semaphore:
                        section = await call(
                            composer,
                            self.composer_data(
                                composer, request, part, references[part], feedback, previous_stems
                            ),
                            revision,
                            validate=lambda section: self.validate_section(section, request, part),
                        )
                    self.validate_section(section, request, part)
                    if request.composer_concurrency == 1:
                        previous_stems.extend(q.stem for q in section.questions)
                    save(folder / f"{part}.json", section.model_dump())
                    return section

                if request.composer_concurrency == 1:
                    sections = [await compose_part(part) for part in self.parts(request)]
                else:
                    tasks = [
                        asyncio.create_task(compose_part(part)) for part in self.parts(request)
                    ]
                    try:
                        sections = await asyncio.gather(*tasks)
                    except BaseException:
                        for task in tasks:
                            task.cancel()
                        await asyncio.gather(*tasks, return_exceptions=True)
                        raise
                for section in sections:
                    questions.extend(section.questions)
                stems = [q.stem.casefold().strip() for q in questions]
                if len(set(stems)) != len(stems):
                    raise ValueError("Duplicate question stems")
                drawings = await self.illustrate(call, questions, revision)
                report["active_stage"] = "rendering"
                report["active_part"] = None
                source = self.render_source(questions, drawings, request, sections)
                save(folder / "illustrations.json", drawings.model_dump())
                (folder / "candidate.tex").write_bytes(source)
                solutions = await self.solve(call, questions, drawings, revision, sections, request)
                ids = [s.id for s in request.slots]
                if [s.question_id for s in solutions.entries] != ids:
                    raise ValueError("Solver must cover every question in matrix order")
                save(folder / "solver.json", solutions.model_dump())
                agreement = compare_answers(questions, solutions)
                report["solver_agreement"] = agreement
                if revision == 1:
                    review = await call(
                        self.reviewer_type(),
                        self.review_data(request, questions, drawings, solutions, source, sections),
                        revision,
                    )
                    if review.checked_ids != ids:
                        raise ValueError("Reviewer must check every question in matrix order")
                    if any(s.status != "solved" for s in solutions.entries):
                        review.decision = "needs_revision"
                        review.issues.append("Solver found ambiguous or unsolvable questions")
                    for mismatch in agreement["mismatched"]:
                        review.decision = "needs_revision"
                        review.issues.append(
                            f"{mismatch['question_id']}: Composer key ({mismatch['composer']}) "
                            f"disagrees with independent Solver ({mismatch['solver']})."
                        )
                    save(folder / "review.json", review.model_dump())
                    report["review_issues"] = review.issues
                    if revision < self.max_revisions and review.decision == "needs_revision":
                        feedback = self.feedback_data(review, questions, sections)
                        report["reviewer_feedback_sent"] = True
                        continue
                # A final revision always requires human inspection.
                (output / "de_thi.tex").write_bytes(source)
                save(
                    output / "dap_an_va_loi_giai.json",
                    {
                        "status": "pending_human_review",
                        "revision": revision,
                        "composer": [q.model_dump() for q in questions],
                        "independent_solver": solutions.model_dump(),
                        **self.extra_output(sections),
                    },
                )
                lines = ["# Đáp án và lời giải — cần giáo viên kiểm tra", ""]
                for q in questions:
                    lines += [
                        f"## {q.id}",
                        q.stem,
                        "",
                        f"Đáp án: {q.answer or 'xem từng ý'}",
                        q.solution,
                        "",
                    ]
                    for label, statement in zip("abcd", q.statements, strict=False):
                        lines += [
                            f"{label}) {'Đúng' if statement.answer else 'Sai'}: "
                            + statement.solution,
                            "",
                        ]
                lines += ["# Lời giải độc lập của Solver", ""]
                for entry in solutions.entries:
                    lines += [
                        f"## {entry.question_id} ({entry.status})",
                        entry.answer,
                        entry.reasoning,
                        "",
                    ]
                (output / "loi_giai.md").write_text("\n".join(lines), encoding="utf-8")
                report.update(
                    execution_status="completed",
                    quality_decision="pending_human_review",
                    revision=revision,
                    final_latex=str(output / "de_thi.tex"),
                    latex_sha256=sha256(source).hexdigest(),
                    answers_sha256=sha256(
                        (output / "dap_an_va_loi_giai.json").read_bytes()
                    ).hexdigest(),
                    latex_validation="not_compiled",
                )
                (output / "KIEM_TRA.txt").write_text(
                    "Cần kiểm tra bằng mắt de_thi.tex/PDF, hình vẽ, đáp án và mức độ từng câu.\n"
                    + (
                        "Xem nhận xét của Reviewer trong _internal/result.json.\n"
                        if self.max_revisions == 1
                        else "Reviewer đã chạy một lần; bản sửa chưa được Reviewer duyệt lại.\n"
                    )
                    + "Lời giải nằm trong dap_an_va_loi_giai.json. Chưa tự động biên dịch LaTeX.\n",
                    encoding="utf-8",
                )
                break
            return report
        except GenerationPaused:
            report["execution_status"] = "paused"
            raise
        except Exception as exc:
            report["error_type"] = type(exc).__name__
            if isinstance(exc, ContractError):
                report["error"] = dict(code="invalid_contract", stage=exc.stage, fields=exc.fields)
            raise
        finally:
            report["invocation_elapsed_seconds"] = round(perf_counter() - started, 3)
            report["elapsed_seconds"] = round(previous_elapsed + perf_counter() - started, 3)
            report["metrics"] = summarize_calls(calls)
            save(internal / "result.json", report)
