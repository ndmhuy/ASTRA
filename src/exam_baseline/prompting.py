import hashlib
import json
from importlib.resources import files

from .contracts import AgentInput, CompletionRequest
from .models import GeneratedExam


class PromptBuilder:
    def __init__(self, version: str = "v1"):
        if version != "v1":
            raise ValueError(f"unknown prompt version: {version}")
        self.version = version
        self.system = files("exam_baseline.prompts").joinpath(f"{version}.txt").read_text("utf-8")
        self.schema = GeneratedExam.model_json_schema()
        contract = json.dumps({"system": self.system, "schema": self.schema}, sort_keys=True)
        self.sha256 = hashlib.sha256(contract.encode()).hexdigest()

    def build(self, context: AgentInput) -> CompletionRequest:
        schema = self.schema
        user = json.dumps(
            {"request": context.request.model_dump(mode="json"), "output_schema": schema},
            ensure_ascii=False,
            sort_keys=True,
        )
        return CompletionRequest(system=self.system, user=user, output_schema=schema)
