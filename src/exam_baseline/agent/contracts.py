"""Semantic turn boundary shared with the React instruction compiler."""

import json
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

CATALOG = json.loads(
    (Path(__file__).parents[1] / "resources" / "agent" / "catalog.json").read_text(encoding="utf-8")
)
VERSION = CATALOG["schemaVersion"]
INTENTS = CATALOG["intents"]
MAX_ACTIONS = CATALOG["maxActions"]
MAX_MESSAGE = 4000
MAX_BODY = 128 * 1024
BOUND = 600
Text = Annotated[str, StringConstraints(min_length=1, max_length=BOUND)]
Id = Annotated[str, StringConstraints(pattern=r"^[a-f0-9-]{36}$")]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Context(Contract):
    screen: Literal["start", "workspace"]
    setup: bool
    status: Literal["draft", "generating", "complete", "error"] | None = None
    view: Literal["paper", "review", "pdf"] = "paper"
    history: list[Text] = Field(default_factory=list, max_length=8)
    facts: list[Text] = Field(default_factory=list, max_length=6)
    questionRefs: list[Text] = Field(default_factory=list, max_length=8)
    editor: bool = False
    approved: bool = False
    confirmationPending: bool = False
    preview: (
        Literal["not_requested", "unavailable", "queued", "compiling", "ready", "failed"] | None
    ) = None


class Turn(Contract):
    schemaVersion: Literal["astra-intent-v1"]
    clientMessageId: Id
    workspaceId: Id
    message: Annotated[str, StringConstraints(min_length=1, max_length=MAX_MESSAGE)]
    context: Context


def arg_schema(rule: str) -> dict:
    kind = rule.rstrip("?")
    if "|" in kind:
        return {"type": "string", "enum": kind.split("|")}
    if kind == "string":
        return {"type": "string", "minLength": 1, "maxLength": BOUND}
    if kind == "integer":
        return {"type": "integer", "minimum": 1, "maximum": 999}
    return {"type": kind}


class Intent(Contract):
    id: str
    args: dict[str, str | int | bool]

    @model_validator(mode="after")
    def validate_args(self):
        if self.id not in INTENTS:
            raise ValueError("unknown intent")
        rules = INTENTS[self.id]["args"]
        if self.args.keys() - rules.keys() or any(
            key not in self.args and not rule.endswith("?") for key, rule in rules.items()
        ):
            raise ValueError("invalid intent arguments")
        for key, value in self.args.items():
            schema = arg_schema(rules[key])
            if type(value) is not {"string": str, "integer": int, "boolean": bool}[schema["type"]]:
                raise ValueError("invalid argument type")
            if "enum" in schema and value not in schema["enum"]:
                raise ValueError("invalid option")
            if isinstance(value, str) and not 1 <= len(value) <= BOUND:
                raise ValueError("invalid argument length")
            if type(value) is int and not 1 <= value <= 999:
                raise ValueError("invalid argument range")
        return self


class ExamIntake(Contract):
    mode: Literal["request", "structure", "capability"]
    family: Literal["thpt", "vact", "custom"] | None = None
    subject: Annotated[str, StringConstraints(min_length=1, max_length=80)] | None = None
    topic: Annotated[str, StringConstraints(min_length=1, max_length=250)] | None = None
    grade: Annotated[int, Field(ge=1, le=12)] | None = None
    count: Annotated[int, Field(ge=1, le=999)] | None = None
    minutes: Annotated[int, Field(ge=1, le=999)] | None = None
    useDefaults: bool | None = None


class Decision(Contract):
    kind: Literal["task", "answer", "clarify", "unsupported", "temporarily_unavailable"]
    intents: list[Intent] = Field(default_factory=list, max_length=MAX_ACTIONS)
    guidance: Literal["start", "capabilities", "remark"] | None = None
    title: Annotated[str, StringConstraints(min_length=1, max_length=60)] | None = None
    intake: ExamIntake | None = None
    reasonCode: (
        Literal[
            "disabled",
            "configuration",
            "transient",
            "quota",
            "schema",
            "budget",
            "auth",
            "model",
            "timeout",
            "rejected",
        ]
        | None
    ) = None

    @model_validator(mode="after")
    def validate_kind(self):
        if self.reasonCode and self.kind != "temporarily_unavailable":
            raise ValueError("reason code requires unavailable decision")
        if (self.intake or self.guidance) and self.kind not in {"answer", "clarify"}:
            raise ValueError("guidance and intake are non-executable proposals")
        if self.intake and self.guidance:
            raise ValueError("choose either intake or guidance")
        if (self.kind == "task") != bool(self.intents):
            raise ValueError("task must contain actions")
        return self
