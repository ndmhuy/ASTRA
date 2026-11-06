"""Filesystem layout and publication gates for one pipeline run."""

import shutil
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel

from exam_baseline.core.hashing import digest
from exam_baseline.core.models import TokenUsage
from exam_baseline.draft.models import ExamDraft, StageResult
from exam_baseline.pipeline.contracts import IllustrationBook, PipelineRequest, PipelineResult
from exam_baseline.pipeline.rendering.compiler import compile_document


def write_model(path: Path, model: BaseModel) -> None:
    path.write_text(model.model_dump_json(indent=2), encoding="utf-8")


@dataclass(frozen=True)
class RunArtifacts:
    root: Path

    @property
    def internal(self) -> Path:
        return self.root / "_internal"

    def initialize(self, payload: PipelineRequest) -> None:
        self.root.mkdir(parents=True, exist_ok=False)
        self.internal.mkdir()
        write_model(self.internal / "request.json", payload)

    def revision(self, number: int) -> Path:
        return self.internal / "drafts" / f"r{number}"

    def save_illustrations(
        self, draft: ExamDraft, book: IllustrationBook, result: PipelineResult
    ) -> None:
        root = self.revision(draft.revision)
        calls = [
            c for c in result.calls if c.stage == "illustrator" and c.revision == draft.revision
        ]
        draft.illustrator = StageResult(
            status="succeeded",
            calls=len(calls),
            reason="Illustrator Agent generated native TikZ/PGFPlots code.",
            latency_ms=sum(c.latency_ms for c in calls),
            usage=calls[-1].usage if calls else TokenUsage(),
        )
        write_model(root / "illustrations.json", book)
        write_model(root / "exam_draft.json", draft)

    def publish(self, source: str, result: PipelineResult, *, compile_latex: bool) -> None:
        candidate = self.internal / "de_thi.tex"
        candidate.write_text(source, encoding="utf-8")
        result.latex_validation = "static"
        if compile_latex:
            compile_document(candidate)
            result.latex_validation = "compiled"
        final = self.root / "de_thi.tex"
        shutil.copyfile(candidate, final)
        result.final_latex = str(final)
        result.latex_sha256 = digest(final.read_bytes())
        result.quality_decision = "pending_human_review"
        result.execution_status = "completed"
        self.write_human_review(result)

    def write_human_review(self, result: PipelineResult) -> None:
        note = (
            "# Cần người dùng kiểm tra bằng mắt\n\n"
            f"Đề hiện tại: revision {result.revision}. "
            "Reviewer kiểm tra revision 1 đúng một lượt.\n"
            f"Đã gửi phản hồi về Composer: {result.reviewer_feedback_sent}.\n"
            "Không có Reviewer lượt hai. Kiểm tra công thức, hình render, dữ kiện và đáp án "
            "trong solution_book trước khi sử dụng. Máy kiểm source LaTeX, chưa xác nhận "
            "bố cục PDF bằng vision.\n\n"
        )
        if result.review is not None:
            for issue in result.review.issues:
                note += f"- {issue.question_id or 'Toàn đề'}: {issue.message}\n"
        if result.solutions is not None:
            for entry in result.solutions.entries:
                if entry.solvability != "solvable":
                    note += f"- Solver: {entry.question_id}: {entry.solvability}.\n"
        (self.internal / "human_review.md").write_text(note, encoding="utf-8")

    def save_result(self, result: PipelineResult) -> None:
        write_model(self.internal / "pipeline_result.json", result)
