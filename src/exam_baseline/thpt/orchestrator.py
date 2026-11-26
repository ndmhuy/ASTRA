"""THPT policy: compose sections, illustrate, solve, review once, optional correction."""

import asyncio
import json
import re
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from pathlib import Path
from time import perf_counter

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
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


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


def compare_answers(questions, solutions) -> dict:
    """Deterministically compare Composer keys against Blind Solver answers."""
    by_id = {entry.question_id: entry for entry in solutions.entries}
    agreed: list[str] = []
    mismatched: list[dict] = []
    unparsed: list[str] = []

    for q in questions:
        entry = by_id.get(q.id)
        if entry is None or entry.status != "solved":
            unparsed.append(q.id)
            continue
        if getattr(q, "choices", None) and getattr(q, "answer", None):
            solver_letter = _parse_p1_letter(entry.answer)
            if solver_letter is None:
                unparsed.append(q.id)
            elif solver_letter == q.answer.strip().upper():
                agreed.append(q.id)
            else:
                mismatched.append(
                    {"question_id": q.id, "composer": q.answer, "solver": solver_letter}
                )
        elif getattr(q, "statements", None):
            solver_bools = _parse_p2_booleans(entry.answer)
            composer_bools = [st.answer for st in q.statements]
            if solver_bools is None or len(solver_bools) != len(composer_bools):
                unparsed.append(q.id)
            elif solver_bools == composer_bools:
                agreed.append(q.id)
            else:
                mismatched.append(
                    {
                        "question_id": q.id,
                        "composer": "".join("Đ" if b else "S" for b in composer_bools),
                        "solver": "".join("Đ" if b else "S" for b in solver_bools),
                    }
                )
        elif getattr(q, "answer", None):
            solver_num = _parse_p3_decimal(entry.answer)
            composer_num = _parse_p3_decimal(q.answer)
            if solver_num is None or composer_num is None:
                unparsed.append(q.id)
            elif solver_num == composer_num:
                agreed.append(q.id)
            else:
                mismatched.append(
                    {"question_id": q.id, "composer": q.answer, "solver": entry.answer.strip()}
                )
        else:
            unparsed.append(q.id)

    return {
        "agreed_count": len(agreed),
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

    def __init__(self, providers: dict[str, LLMProvider], *, on_progress=None):
        self.providers = providers
        self.on_progress = on_progress

    async def run(self, request: Request, output: Path, *, resume: bool = False) -> dict:
        started = perf_counter()
        self.template.original()  # Verify before spending provider calls.
        references = self.template.reference_parts()
        internal = output / "_internal"
        calls = []
        previous_elapsed = 0.0
        if resume:
            previous = self.request_model.model_validate_json(
                (internal / "request.json").read_bytes()
            )
            if previous != request:
                raise ValueError("Resume requires the same input request")
            previous_report = json.loads((internal / "result.json").read_text("utf-8"))
            if previous_report["execution_status"] == "completed":
                return previous_report
            calls = previous_report["calls"]
            previous_elapsed = previous_report.get("elapsed_seconds", 0.0)
        else:
            output.mkdir(parents=True, exist_ok=False)
            internal.mkdir()
            save(internal / "request.json", request.model_dump())
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

        async def call(agent, data, revision):
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
            if resume and checkpoint.exists():
                saved = json.loads(checkpoint.read_text("utf-8"))
                content = json.dumps(saved["response"], ensure_ascii=False, sort_keys=True)
                if sha256(content.encode()).hexdigest() != saved["sha256"]:
                    raise ValueError("Changed checkpoint; refusing to resume")
                response = agent.contract(data).model_validate(saved["response"])
                return response
            provider = RecordingProvider(
                self.providers[agent.role],
                agent.role,
                revision,
                calls,
                internal / "responses",
                retries=0 if agent.role == "reviewer" else 1,
            )
            try:
                response, _ = await agent.run(provider, data)
            except Exception:
                report["active_stage"] = agent.role
                report["active_part"] = data.get("part")
                raise
            content = json.dumps(response.model_dump(), ensure_ascii=False, sort_keys=True)
            save(
                checkpoint,
                {"response": response.model_dump(), "sha256": sha256(content.encode()).hexdigest()},
            )
            save(internal / "result.json", report)
            return response

        try:
            feedback = None
            for revision in (1, 2):
                folder = internal / f"revision_{revision}"
                folder.mkdir(exist_ok=resume)
                questions = []
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
                ):
                    async with semaphore:
                        section = await call(
                            composer,
                            composer.data(request, part, references[part], feedback),
                            revision,
                        )
                    self.validate_section(section, request, part)
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
                    if review.decision == "needs_revision":
                        feedback = self.feedback_data(review, questions, sections)
                        report["reviewer_feedback_sent"] = True
                        continue
                # No second Reviewer. The final revision always requires human inspection.
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
                    latex_validation="not_compiled",
                )
                (output / "KIEM_TRA.txt").write_text(
                    "Cần kiểm tra bằng mắt de_thi.tex/PDF, hình vẽ, đáp án và mức độ từng câu.\n"
                    "Reviewer đã chạy một lần; bản sửa chưa được Reviewer duyệt lại.\n"
                    "Lời giải nằm trong dap_an_va_loi_giai.json. Chưa tự động biên dịch LaTeX.\n",
                    encoding="utf-8",
                )
                break
            return report
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
