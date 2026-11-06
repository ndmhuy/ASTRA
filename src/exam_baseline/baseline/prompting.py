import hashlib
import json
from importlib.resources import files

from exam_baseline.core.contracts import AgentInput, CompletionRequest
from exam_baseline.core.models import GeneratedExam
from exam_baseline.core.profiles import hcm_de11_prompt


class PromptBuilder:
    def __init__(self, version: str = "v1"):
        if version != "v1":
            raise ValueError(f"unknown prompt version: {version}")
        self.version = version
        self.system = (
            files("exam_baseline.resources.prompts").joinpath(f"{version}.txt").read_text("utf-8")
        )
        self.schema = GeneratedExam.model_json_schema()
        contract = json.dumps({"system": self.system, "schema": self.schema}, sort_keys=True)
        self.sha256 = hashlib.sha256(contract.encode()).hexdigest()

    def build(self, context: AgentInput) -> CompletionRequest:
        schema = self.schema
        user = json.dumps(
            {
                "request": context.request.model_dump(mode="json"),
                "output_schema": schema,
                "format_instructions": hcm_de11_prompt()
                if context.request.format_profile == "hcm_dgnl_de11"
                else None,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        return CompletionRequest(system=self.system, user=user, output_schema=schema)
