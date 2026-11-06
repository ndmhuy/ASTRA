"""Bind model-generated content to controller-owned identities and artifact hashes."""

import json
from dataclasses import dataclass
from typing import Generic, TypeVar

from pydantic import BaseModel

from exam_baseline.pipeline.contracts import IllustrationBook

ResponseT = TypeVar("ResponseT", bound=BaseModel)
MACHINE_FIELDS = frozenset(
    {"exam_id", "draft_id", "revision", "artifact_sha256", "solution_sha256"}
)


@dataclass(frozen=True)
class ResponseContract(Generic[ResponseT]):
    model: type[ResponseT]

    def schema(self, data: dict) -> dict:
        schema = self.model.model_json_schema()
        for name in MACHINE_FIELDS:
            schema.get("properties", {}).pop(name, None)
        schema["required"] = [n for n in schema.get("required", []) if n not in MACHINE_FIELDS]
        return schema

    def parse(self, text: str, data: dict) -> ResponseT:
        body = json.loads(text)
        if not isinstance(body, dict):
            raise ValueError("stage output must be a JSON object")
        return self.model.model_validate(self.bind(body, data))

    def bind(self, body: dict, data: dict) -> dict:
        context = data.get("student_view", data)
        for name in MACHINE_FIELDS & self.model.model_fields.keys():
            expected = data["solution_sha256"] if name == "solution_sha256" else context[name]
            if name in body and body[name] != expected:
                raise ValueError(f"{name} must match the current input")
            body[name] = expected
        return body


class IllustrationResponse(ResponseContract[IllustrationBook]):
    def schema(self, data: dict) -> dict:
        schema = super().schema(data)
        drawing = schema["$defs"]["Drawing"]
        drawing["properties"].pop("spec_sha256", None)
        drawing["required"] = [n for n in drawing.get("required", []) if n != "spec_sha256"]
        visual_ids = [s["visual_id"] for s in data["visual_specs"]]
        schema["properties"]["drawings"].update(minItems=len(visual_ids), maxItems=len(visual_ids))
        if visual_ids:
            drawing["properties"]["visual_id"]["enum"] = visual_ids
        return schema

    def bind(self, body: dict, data: dict) -> dict:
        body = super().bind(body, data)
        specs = {s["visual_id"]: s for s in data["visual_specs"]}
        drawings = body.get("drawings", [])
        for drawing in drawings if isinstance(drawings, list) else []:
            if not isinstance(drawing, dict) or not isinstance(drawing.get("visual_id"), str):
                continue
            spec = specs.get(drawing["visual_id"])
            if spec is None:
                raise ValueError(
                    "Use only requested visual IDs: "
                    + str(list(specs))
                    + '. With no visual specs return exactly {"drawings":[]}.'
                )
            expected = spec["spec_sha256"]
            if "spec_sha256" in drawing and drawing["spec_sha256"] != expected:
                raise ValueError("spec_sha256 must match the current visual spec")
            drawing["spec_sha256"] = expected
        return body
