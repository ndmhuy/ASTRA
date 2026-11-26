"""Provider-independent meaning. React resolves goals against fresh domain/UI state."""

import json
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, model_validator

from .contracts import Context, Contract, Decision, ExamIntake, Intent, Turn, arg_schema

CATALOG = json.loads(
    (Path(__file__).parents[1] / "resources/agent/semantic-catalog.json").read_text("utf-8")
)
VERSION = CATALOG["schemaVersion"]
GOALS = CATALOG["goals"]
LIMITS = CATALOG["limits"]


class Dialogue(Contract):
    family: Literal["thpt", "vact", "custom"] | None = None
    subject: Annotated[str, StringConstraints(min_length=1, max_length=80)] | None = None
    missing: Literal["family", "subject"] | None = None
    phase: Literal["collecting", "selected", "evaluated", "confirmed"]


class SemanticContext(Context):
    dialogue: Dialogue | None = None
    recentQuestion: "QuestionReference | None" = None


class QuestionReference(Contract):
    number: Annotated[int, Field(ge=1, le=999)]
    part: Annotated[str, StringConstraints(min_length=1, max_length=40)] | None = None


class SemanticTurn(Turn):
    context: SemanticContext


class Goal(Contract):
    goal: str
    parameters: dict[str, str | int | bool] = Field(default_factory=dict)
    reference: Literal["current", "previous", "recent"] | None = None

    @model_validator(mode="after")
    def bounded_parameters(self):
        if self.goal not in GOALS:
            raise ValueError("unknown_semantic_goal")
        rules = GOALS[self.goal]["parameters"]
        if self.parameters.keys() - rules.keys():
            raise ValueError("unknown_semantic_parameter")
        # Missing information belongs to the workflow, not provider validation.
        for name, value in self.parameters.items():
            rule = arg_schema(rules[name])
            expected = {"string": str, "integer": int, "boolean": bool}[rule["type"]]
            if type(value) is not expected:
                raise ValueError("semantic_parameter_type")
            if "enum" in rule and value not in rule["enum"]:
                raise ValueError("semantic_parameter_enum")
            if type(value) is str and not 1 <= len(value) <= 600:
                raise ValueError("semantic_parameter_length")
            if type(value) is int and not 1 <= value <= 999:
                raise ValueError("semantic_parameter_range")
        return self


class SemanticFrame(Contract):
    schemaVersion: Literal["astra-semantic-v1"] = "astra-semantic-v1"
    dialogueAct: Literal[
        "REQUEST",
        "INFORM",
        "QUESTION",
        "GUIDANCE",
        "CORRECT",
        "CANCEL",
        "CONFIRM",
        "CONVERSATION",
        "AMBIGUOUS",
        "UNSUPPORTED",
        "OUT_OF_SCOPE",
    ]
    goals: list[Goal] = Field(default_factory=list, max_length=LIMITS["goalsPerTurn"])
    constraints: list[
        Literal[
            "NO_GENERATION",
            "NO_EXECUTION",
            "CONDITIONAL",
            "NEGATED",
            "CONTRADICTORY",
        ]
    ] = Field(default_factory=list, max_length=5)
    title: Annotated[str, StringConstraints(min_length=1, max_length=60)] | None = None


def normalize_frame(value: object) -> SemanticFrame:
    """Only representation defaults are normalized; meaning is never repaired."""
    if not isinstance(value, dict):
        raise ValueError("semantic_object_required")
    result = dict(value)
    for name in ("constraints", "goals"):
        if result.get(name) is None:
            result.pop(name, None)
    title = result.pop("title", None)
    # Optional title metadata cannot poison otherwise valid semantics.
    if isinstance(title, str):
        cleaned = " ".join(title.split())
        if 0 < len(cleaned) <= 60 and not any(ord(char) < 32 for char in title):
            result["title"] = cleaned
    if isinstance(result.get("goals"), list):
        result["goals"] = [
            {key: item for key, item in goal.items() if item is not None}
            if isinstance(goal, dict)
            else goal
            for goal in result["goals"]
        ]
    return SemanticFrame.model_validate(result)


def semantic_schema(*, compact: bool = False) -> dict:
    """Canonical validation stays strict; native Gemini uses a smaller slot union."""
    slots: dict = {}
    variants = []
    for name, definition in GOALS.items():
        properties = {key: arg_schema(rule) for key, rule in definition["parameters"].items()}
        for key, rule in properties.items():
            previous = slots.get(key)
            if previous and previous != rule:
                if "enum" in previous and "enum" in rule:
                    rule = {"type": "string", "enum": sorted(set(previous["enum"] + rule["enum"]))}
                else:
                    rule = {"type": rule["type"], "minLength": 1, "maxLength": 600}
            slots[key] = rule
        variants.append(
            {
                "type": "object",
                "additionalProperties": False,
                "required": ["goal"],
                "properties": {
                    "goal": {"type": "string", "enum": [name]},
                    "parameters": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": properties,
                    },
                    "reference": {"type": "string", "enum": ["current", "previous", "recent"]},
                },
            }
        )
    frame = SemanticFrame.model_json_schema()
    frame.pop("$defs", None)
    frame["properties"]["goals"]["items"] = {"anyOf": variants}
    if compact:
        frame["properties"].pop("schemaVersion")
        frame["properties"]["goals"]["items"] = {
            "type": "object",
            "additionalProperties": False,
            "required": ["goal"],
            "properties": {
                "goal": {"type": "string", "enum": list(GOALS)},
                "parameters": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": slots,
                },
                "reference": {"type": "string", "enum": ["current", "previous", "recent"]},
            },
        }
    return frame


def legacy_decision(frame: SemanticFrame) -> Decision:
    """Migration for old local clients; never resolves domain IDs or confirmations."""
    if frame.constraints or frame.dialogueAct not in {"REQUEST", "INFORM", "CORRECT"}:
        return Decision(kind="clarify")
    if len(frame.goals) == 1:
        goal = frame.goals[0]
        definition = GOALS[goal.goal]
        if definition["resolver"] == "intake":
            try:
                return Decision(kind="answer", intake=ExamIntake(mode="request", **goal.parameters))
            except ValueError:
                return Decision(kind="clarify")
    intents = []
    for goal in frame.goals:
        definition = GOALS[goal.goal]
        if definition["resolver"] != "capability" or goal.reference == "previous":
            return Decision(kind="clarify")
        try:
            intents.append(Intent(id=definition["capability"], args=goal.parameters))
        except ValueError:
            return Decision(kind="clarify")
    return Decision(kind="task", intents=intents) if intents else Decision(kind="clarify")
