from fastapi.testclient import TestClient

from exam_baseline.api import create_app
from exam_baseline.config import Settings
from exam_baseline.pipeline.bootstrap import replay_providers
from tests.pipeline.helpers import (
    TEXT,
    payload,
)


def test_v2_api_returns_latex_with_explicit_human_handoff(tmp_path):
    app = create_app(
        Settings.for_offline(),
        pipeline_providers=replay_providers(TEXT),
        pipeline_output_root=tmp_path,
    )
    with TestClient(app) as client:
        result = client.post("/v2/exams/generate", json=payload().model_dump(mode="json"))
        assert result.status_code == 200
        assert result.headers["content-type"].startswith("application/x-tex")
        assert result.headers["x-human-review-required"] == "true"
        assert result.headers["x-reviewer-feedback-sent"] == "false"
        assert "/v1/exams/generate" in client.get("/openapi.json").json()["paths"]
