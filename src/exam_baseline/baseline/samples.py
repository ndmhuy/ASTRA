"""Load the canonical request packaged with the application, without mutable globals."""

from importlib.resources import files

from exam_baseline.core.models import GenerationRequest


def sample_request() -> GenerationRequest:
    text = files("exam_baseline.resources.fixtures").joinpath("request.json").read_text("utf-8")
    return GenerationRequest.model_validate_json(text)
