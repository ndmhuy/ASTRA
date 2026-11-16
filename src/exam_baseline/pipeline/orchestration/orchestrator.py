"""Four-agent workflow with exactly one possible Reviewer-to-Composer callback."""

import asyncio
import json
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from exam_baseline.core.contracts import LLMProvider, ProviderError
from exam_baseline.draft.models import MiniRequest, StageResult
from exam_baseline.pipeline.agents import PipelineAgents
from exam_baseline.pipeline.contracts import (
    PipelineError,
    PipelineRequest,
    PipelineResult,
    WorkflowEvent,
)
from exam_baseline.pipeline.errors import PipelineFailure, StageContractError
from exam_baseline.pipeline.orchestration.artifacts import RunArtifacts, write_model
from exam_baseline.pipeline.orchestration.validation import (
    validate_draft,
    validate_publication,
    validate_request,
)
from exam_baseline.pipeline.rendering.document import render_document
from exam_baseline.pipeline.rendering.syntax import format_errors
from exam_baseline.pipeline.runtime import TracedProvider
from exam_baseline.pipeline.views import reviewer_view, student_view


class Orchestrator:
    def __init__(self, providers: dict[str, LLMProvider], *, agents: PipelineAgents | None = None):
        self.providers = providers
        self.agents = agents if agents is not None else PipelineAgents()

    async def run(
        self, payload: PipelineRequest, output: Path, *, compile_latex: bool = False
    ) -> PipelineResult:
        payload = PipelineRequest.model_validate(payload.model_dump())
        validate_request(payload, output, self.providers, self.agents.roles)
        artifacts = RunArtifacts(output)
        artifacts.initialize(payload)
        result, start = PipelineResult(run_id=str(uuid4())), perf_counter()
        try:
            await asyncio.wait_for(
                self._execute(payload, artifacts, result, compile_latex),
                payload.workflow.run_timeout_seconds,
            )
        except asyncio.TimeoutError:
            self._error(result, "orchestrator", "run_timeout", "Workflow deadline exceeded.")
        except PipelineFailure as exc:
            self._error(result, exc.stage, exc.code, str(exc))
        except ProviderError as exc:
            self._error(result, getattr(exc, "stage", "orchestrator"), exc.code, str(exc))
        except StageContractError as exc:
            self._error(result, exc.stage, "stage_contract", str(exc))
        except (OSError, ValueError) as exc:
            self._error(result, "finalizer", "artifact_error", str(exc))
        result.total_latency_ms = (perf_counter() - start) * 1000
        artifacts.save_result(result)
        return result

    async def _execute(self, payload, artifacts: RunArtifacts, result, compile_latex):
        mini = MiniRequest.model_validate(
            {name: getattr(payload, name) for name in MiniRequest.model_fields}
        )
        feedback = None
        # Two fixed passes, never an until-approved loop. Reviewer exists only in pass 1.
        for revision in (1, 2):
            result.revision = revision
            result.deterministic_passed = False
            root = artifacts.revision(revision)
            draft = await self._compose(mini, payload, root, result, feedback)
            self._event(result, "composer", "succeeded", "Question draft generated.")
            book = await self.agents.illustrator.run(
                draft,
                self._provider("illustrator", payload, result, root),
                payload.workflow.max_schema_repairs,
            )
            artifacts.save_illustrations(draft, book, result)
            self._event(result, "illustrator", "succeeded", "Native TikZ/PGFPlots code generated.")
            validate_draft(draft, mini, book)
            source = render_document(
                draft,
                payload.latex_template,
                {t.id: t.name for t in mini.request.matrix.topics},
                book,
            )
            (root / "merged.tex").write_text(source, encoding="utf-8")
            self._event(result, "merger", "succeeded", "Composer text + Illustrator code merged.")
            student, _ = student_view(draft, root, book, source)
            result.deterministic_passed = True
            solver_packet = dict(student)
            if revision == 2:
                solver_packet["correction"] = {
                    "instruction": "Independently re-solve the revised student exam and verify "
                    "arithmetic, units and native drawing source. No prior key is supplied."
                }
            solutions = await self.agents.solver.run(
                solver_packet,
                self._provider("solver", payload, result, root),
                payload.workflow.max_schema_repairs,
            )
            result.solutions = solutions
            write_model(root / "solution_book.json", solutions)
            self._event(
                result, "solver", "succeeded", "Independent source/math verification completed."
            )
            if revision == 1:
                review = await self.agents.reviewer.run(
                    reviewer_view(student, solutions, payload),
                    self._provider("reviewer", payload, result, root),
                    student,
                    solutions,
                )
                result.review = review
                write_model(root / "review_report.json", review)
                self._event(result, "reviewer", "succeeded", review.decision)
                needs_feedback = review.decision != "approved" or any(
                    i.severity != "info" for i in review.issues
                )
                if needs_feedback:
                    result.repairs = 1
                    result.reviewer_feedback_sent = True
                    feedback = {
                        "review": review.model_dump(mode="json"),
                        "previous_output": {
                            "exam": draft.exam.model_dump(mode="json"),
                            "questions": [q.model_dump(mode="json") for q in draft.questions],
                            "visuals": [v.model_dump(mode="json") for v in draft.visuals],
                        },
                        "instruction": "This is the ONLY Reviewer feedback. Correct the "
                        "identified defects, preserve matrix and question IDs. "
                        "The user performs final visual inspection.",
                    }
                    self._event(result, "composer", "repair", "Reviewer feedback delivered once.")
                    continue
                result.machine_approved = True
                result.review_covers_final_revision = True
            # Revision 2 goes directly to human handoff: no second Reviewer call or feedback.
            validate_publication(
                draft,
                mini,
                book,
                root,
                source,
                student,
                solutions,
                result.review if result.review_covers_final_revision else None,
            )
            artifacts.publish(source, result, compile_latex=compile_latex)
            self._event(result, "human_handoff", "succeeded", "Awaiting user visual inspection.")
            return

    async def _compose(self, mini, payload, root, result, feedback):
        # An initial schema correction is permitted; the Reviewer callback itself gets
        # exactly ONE Composer call. Failure never triggers another feedback cycle.
        attempts = 1 if feedback is not None else payload.workflow.max_schema_repairs + 1
        for attempt in range(attempts):
            produced = await self.agents.composer.run(
                mini,
                self._provider("composer", payload, result, root),
                root,
                result.revision,
                feedback,
            )
            errors = (
                [e.model_dump() for e in produced.errors]
                if isinstance(produced, StageResult)
                else format_errors(produced)
            )
            if not errors:
                return produced
            code = errors[0]["code"]
            if result.calls:
                result.calls[-1].error_code = code
            if (
                isinstance(produced, StageResult)
                and (
                    not produced.calls
                    or code.startswith("provider_")
                    or code
                    in {
                        "call_budget_exceeded",
                        "token_budget_exceeded",
                        "context_too_large",
                        "stage_timeout",
                        "figure_budget",
                        "fixture_exhausted",
                    }
                )
            ) or attempt == attempts - 1:
                raise PipelineFailure(
                    "composer", code, "Composer failed: " + errors[0].get("message", code)
                )
            feedback = {"contract_errors": errors}
            try:
                previous = json.loads(
                    (root / "composer_last_response.json").read_text(encoding="utf-8")
                )
                if isinstance(previous, dict) and "exam" in previous:
                    feedback["previous_output"] = previous
            except (OSError, ValueError):
                pass
            self._event(result, "composer", "repair", "Initial schema/format correction.")
        raise AssertionError("unreachable")

    def _provider(self, role, payload, result, root):
        return TracedProvider(
            self.providers[role],
            role,
            result.revision,
            payload.workflow,
            result,
            root / "responses",
        )

    @staticmethod
    def _event(result, stage, status, detail):
        result.events.append(
            WorkflowEvent(stage=stage, revision=result.revision, status=status, detail=detail)
        )

    @staticmethod
    def _error(result, stage, code, message):
        if code in {"final_validation", "stale_artifact", "artifact_error"}:
            result.deterministic_passed = False
        result.errors.append(PipelineError(stage=stage, code=code, message=message))
        Orchestrator._event(result, stage, "failed", code)
