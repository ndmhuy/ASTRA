"""V-ACT profile for the same bounded, checkpointed four-agent run policy."""

from exam_baseline.pipeline.orchestration.concurrency import run_bounded
from exam_baseline.thpt.orchestrator import Orchestrator as BaseWorkflow
from exam_baseline.vact import agents, template
from exam_baseline.vact.models import Illustrations, Request, Solutions
from exam_baseline.vact.rendering import render, student_view
from exam_baseline.vact.validation import validate_batch


class Orchestrator(BaseWorkflow):
    request_model = Request
    template = template
    composer_type = agents.ComposerAgent
    illustrator_type = agents.IllustratorAgent
    solver_type = agents.SolverAgent
    reviewer_type = agents.ReviewerAgent

    def parts(self, request):
        return tuple(b.id for b in template.batches())

    def validate_section(self, section, request, part):
        super().validate_section(section, request, part)
        batch = next(b for b in template.batches() if b.id == part)
        validate_batch(section, batch)

    def render_source(self, questions, drawings, request, sections):
        return render(sections, drawings, request.font_profile)

    def extra_output(self, sections):
        return dict(passages=[p.model_dump() for section in sections for p in section.passages])

    async def illustrate(self, call, questions, revision):
        requested = [
            dict(question_id=q.id, stem=q.stem, description=q.illustration_request)
            for q in questions
            if q.illustration_request
        ]
        drawings = []
        for offset in range(0, len(requested), 4):
            chunk = requested[offset : offset + 4]
            book = await call(
                self.illustrator_type(), dict(part=f"drawings_{offset}", requests=chunk), revision
            )
            if {d.question_id for d in book.drawings} != {r["question_id"] for r in chunk}:
                raise ValueError("Illustrator returned drawings for the wrong batch")
            drawings.extend(book.drawings)
        return Illustrations(drawings=drawings)

    async def solve(self, call, questions, drawings, revision, sections, request):
        # Each Solver batch receives complete student context, never private answers.
        async def solve_batch(item):
            batch, section = item
            book = await call(
                self.solver_type(),
                dict(
                    part=batch.id,
                    question_ids=batch.ids,
                    **student_view(section),
                    drawings=[
                        d.model_dump() for d in drawings.drawings if d.question_id in batch.ids
                    ],
                ),
                revision,
            )
            if [entry.question_id for entry in book.entries] != batch.ids:
                raise ValueError("Solver batch IDs differ from the VACT matrix")
            return book

        books = await run_bounded(
            list(zip(template.batches(), sections, strict=True)),
            solve_batch,
            request.solver_concurrency,
        )
        return Solutions(entries=[entry for book in books for entry in book.entries])

    def review_data(self, request, questions, drawings, solutions, source, sections):
        data = super().review_data(request, questions, drawings, solutions, source, sections)
        data["passages"] = [p.model_dump() for section in sections for p in section.passages]
        return data

    def feedback_data(self, review, questions, sections):
        data = super().feedback_data(review, questions, sections)
        data["previous_passages"] = [
            p.model_dump() for section in sections for p in section.passages
        ]
        return data
