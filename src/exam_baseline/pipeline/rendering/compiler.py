"""Optional local XeLaTeX/LuaLaTeX compilation with explicit diagnostics."""

import shutil
import subprocess
from pathlib import Path


def compile_document(path: Path) -> None:
    compiler = shutil.which("xelatex") or shutil.which("lualatex")
    if compiler is None:
        raise ValueError("xelatex_or_lualatex_not_installed")
    with (path.parent / "compile.log").open("w", encoding="utf-8") as log:
        try:
            result = subprocess.run(
                [
                    compiler,
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    "-no-shell-escape",
                    "-output-directory",
                    str(path.parent.resolve()),
                    path.name,
                ],
                cwd=path.parent,
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=60,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ValueError("latex_compile_timeout") from exc
    if result.returncode or not path.with_suffix(".pdf").is_file():
        raise ValueError("latex_compile_failed: see internal compile.log")
