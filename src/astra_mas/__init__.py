"""Public import surface for the compiled MAS planner bundled with ASTRA."""

import sys

if sys.implementation.name != "cpython" or sys.version_info[:2] != (3, 11):
    raise ImportError("The ASTRA MAS planner requires CPython 3.11. See .python-version.")

from astra_mas.contracts import (  # noqa: E402
    MasCompletion,
    MasError,
    MasFile,
    MasInput,
    MasLimits,
    MasPrompt,
    MasResult,
)
from astra_mas.runtime import prepare_plan  # noqa: E402

__all__ = [
    "MasCompletion",
    "MasError",
    "MasFile",
    "MasInput",
    "MasLimits",
    "MasPrompt",
    "MasResult",
    "prepare_plan",
]
