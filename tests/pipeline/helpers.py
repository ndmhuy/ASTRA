import json

from exam_baseline.core.contracts import Completion
from exam_baseline.core.models import TokenUsage
from exam_baseline.pipeline.bootstrap import ReplayProvider
from exam_baseline.pipeline.contracts import PipelineRequest
from tests.paths import ROOT

TEXT = ROOT / "examples/pipeline/text_01"


VISUAL = ROOT / "examples/pipeline/visual_graph"


def payload(folder=TEXT):
    return PipelineRequest.model_validate_json((folder / "input.json").read_text(encoding="utf-8"))


class Scripted:
    name = "test"
    model = "test-only"
    parameters = {}
    supports_images = True

    def __init__(self, fn):
        self.fn, self.requests = fn, []

    async def complete(self, request):
        self.requests.append(request)
        text = self.fn(request, len(self.requests))
        return Completion(
            text=text, model=self.model, usage=TokenUsage(input_tokens=10, output_tokens=20)
        )


def response(role, request, decision="approved", issues=None, wrong=False):
    data = json.loads((TEXT / f"{role}_01.json").read_text(encoding="utf-8"))
    view = json.loads(request.user)["input"]
    if role == "reviewer":
        data["solution_sha256"] = view["solution_sha256"]
        view = view["student_view"]
        data.update(decision=decision, issues=issues or [])
    for key in ("exam_id", "draft_id", "revision", "artifact_sha256"):
        data[key] = view[key]
    if wrong:
        data["entries"][0]["answer"] = "D"
    return json.dumps(data, ensure_ascii=False)


def issue(target="composer"):
    return {
        "code": "wrong_content",
        "severity": "major",
        "target": target,
        "question_id": "q1",
        "evidence": "Specific arithmetic inconsistency at q1.",
        "message": "Recalculate the question.",
        "suggested_action": "Correct the arithmetic.",
    }


def repeated_providers():
    return {
        role: ReplayProvider([(TEXT / f"{role}_01.json").read_text(encoding="utf-8")] * 2)
        for role in ("composer", "illustrator", "solver", "reviewer")
    }
