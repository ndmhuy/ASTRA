import asyncio
import shutil
from pathlib import Path

import pytest

from exam_baseline.pipeline.bootstrap import replay_providers
from exam_baseline.pipeline.orchestration.orchestrator import Orchestrator
from exam_baseline.pipeline.rendering.compiler import compile_document
from exam_baseline.pipeline.rendering.syntax import prose, validate_drawing_code
from tests.pipeline.helpers import (
    VISUAL,
    payload,
)


def test_native_code_validation_and_math_escaping():
    assert prose(r"50% & $x_1$") == r"50\% \& $x_1$"
    for code in (
        r"\begin{tikzpicture}\directlua{bad}\end{tikzpicture}",
        r"\begin{tikzpicture}\addplot table {secret};\end{tikzpicture}",
        r"\begin{tikzpicture}\draw (0,0)--(1,1);",
    ):
        with pytest.raises(ValueError):
            validate_drawing_code(code)
    with pytest.raises(ValueError):
        prose("$x+1")


@pytest.mark.skipif(
    not (shutil.which("xelatex") or shutil.which("lualatex")),
    reason="No terminal TeX compiler installed; editor compilation tested separately",
)
def test_native_tex_compiles_when_terminal_compiler_available(tmp_path):
    result = asyncio.run(
        Orchestrator(replay_providers(VISUAL)).run(
            payload(VISUAL), tmp_path / "run", compile_latex=True
        )
    )
    assert result.final_latex and result.latex_validation == "compiled"
    compile_document(Path(result.final_latex))
