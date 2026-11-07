"""THPT policy: compose sections, illustrate, solve, review once, optional correction."""

import json
from hashlib import sha256
from pathlib import Path

from exam_baseline.core.contracts import LLMProvider
from exam_baseline.thpt.agents import (
    ComposerAgent,
    IllustratorAgent,
    ReviewerAgent,
    SolverAgent,
)
from exam_baseline.thpt.models import Request
from exam_baseline.thpt.rendering import render, student_view
from exam_baseline.thpt.runtime import ContractError, RecordingProvider
from exam_baseline.thpt.template import TEMPLATE_SHA256, original, reference_parts


def save(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class Orchestrator:
    def __init__(self, providers: dict[str, LLMProvider]):
        self.providers = providers

    async def run(self, request: Request, output: Path, *, resume: bool = False) -> dict:
        original()  # Verify locked resource before spending any provider calls.
        references = reference_parts()
        internal = output / "_internal"
        calls = []
        if resume:
            previous = Request.model_validate_json((internal / "request.json").read_bytes())
            if previous != request:
                raise ValueError("Resume requires the same input request")
            previous_report = json.loads((internal / "result.json").read_text("utf-8"))
            if previous_report["execution_status"] == "completed":
                return previous_report
            calls = previous_report["calls"]
        else:
            output.mkdir(parents=True, exist_ok=False)
            internal.mkdir()
            save(internal / "request.json", request.model_dump())
        checkpoints = internal / "checkpoints"
        checkpoints.mkdir(exist_ok=True)
        report = dict(
            execution_status="failed",
            human_review_required=True,
            template_sha256=TEMPLATE_SHA256,
            font_profile=request.font_profile,
            reviewer_feedback_sent=False,
            final_latex=None,
            calls=calls,
        )

        async def call(agent, data, revision):
            report["active_stage"] = agent.role
            report["active_part"] = data.get("part")
            fingerprint = sha256(
                json.dumps(
                    {
                        "role": agent.role,
                        "revision": revision,
                        "data": data,
                        "system": agent.instruction,
                        "schema": agent.contract(data).model_json_schema(),
                        "template": TEMPLATE_SHA256,
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
            response, _ = await agent.run(provider, data)
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
                composer = ComposerAgent()
                for part in ("P1", "P2", "P3"):
                    section = await call(
                        composer, composer.data(request, part, references[part], feedback), revision
                    )
                    expected = [s.id for s in request.slots if s.part == part]
                    if [q.id for q in section.questions] != expected:
                        raise ValueError("Composer question IDs/count/order differ from matrix")
                    questions.extend(section.questions)
                    save(folder / f"{part}.json", section.model_dump())
                stems = [q.stem.casefold().strip() for q in questions]
                if len(set(stems)) != len(stems):
                    raise ValueError("Duplicate question stems")
                drawings = await call(
                    IllustratorAgent(),
                    dict(
                        requests=[
                            dict(question_id=q.id, stem=q.stem, description=q.illustration_request)
                            for q in questions
                            if q.illustration_request
                        ]
                    ),
                    revision,
                )
                report["active_stage"] = "rendering"
                report["active_part"] = None
                source = render(questions, drawings, font_profile=request.font_profile)
                save(folder / "illustrations.json", drawings.model_dump())
                (folder / "candidate.tex").write_bytes(source)
                solutions = await call(
                    SolverAgent(),
                    dict(questions=student_view(questions), drawings=drawings.model_dump()),
                    revision,
                )
                ids = [s.id for s in request.slots]
                if [s.question_id for s in solutions.entries] != ids:
                    raise ValueError("Solver must cover every question in matrix order")
                save(folder / "solver.json", solutions.model_dump())
                if revision == 1:
                    review = await call(
                        ReviewerAgent(),
                        dict(
                            matrix=request.model_dump(),
                            questions=[q.model_dump() for q in questions],
                            drawings=drawings.model_dump(),
                            solver=solutions.model_dump(),
                            student_latex=source.decode("utf-8"),
                        ),
                        revision,
                    )
                    if review.checked_ids != ids:
                        raise ValueError("Reviewer must check every question in matrix order")
                    if any(s.status != "solved" for s in solutions.entries):
                        review.decision = "needs_revision"
                        review.issues.append("Solver found ambiguous or unsolvable questions")
                    save(folder / "review.json", review.model_dump())
                    if review.decision == "needs_revision":
                        feedback = dict(
                            review=review.model_dump(),
                            previous_questions=[q.model_dump() for q in questions],
                        )
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
            save(internal / "result.json", report)
