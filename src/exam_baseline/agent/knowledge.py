"""Shared domain vocabulary. Runnable presets come from the Backend catalog."""

import json
from importlib.resources import files

DOMAIN = json.loads(
    files("exam_baseline.resources").joinpath("agent/domain.json").read_text(encoding="utf-8")
)
