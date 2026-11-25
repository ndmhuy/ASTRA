"""Optional local XeLaTeX/LuaLaTeX compilation with explicit diagnostics."""

import os
import shutil
import subprocess
from pathlib import Path


def find_compiler(configured: Path | str | None = None) -> str | None:
    if configured:
        path = Path(configured)
        return str(path.resolve()) if path.is_file() else shutil.which(str(configured))
    for name in ("xelatex", "lualatex", "tectonic"):
        if executable := shutil.which(name):
            return executable
    portable = Path(__file__).resolve().parents[4] / "tools/.local/tectonic/tectonic.exe"
    return str(portable) if portable.is_file() else None


def compile_document(
    path: Path,
    *,
    compiler: str | Path | None = None,
    timeout: float = 180,
    cache_directory: Path | None = None,
) -> None:
    compiler = find_compiler(compiler)
    if compiler is None:
        raise ValueError("latex_compiler_unavailable")
    environment = {
        key: value for key, value in os.environ.items() if not key.upper().endswith("_API_KEY")
    }
    if Path(compiler).stem.lower() == "tectonic":
        command = [
            str(compiler),
            "--untrusted",
            "--keep-logs",
            "--outdir",
            str(path.parent.resolve()),
            path.name,
        ]
        environment["TECTONIC_UNTRUSTED_MODE"] = "1"
        if cache_directory is not None:
            cache_directory.resolve().mkdir(parents=True, exist_ok=True)
            environment["TECTONIC_CACHE_DIR"] = str(cache_directory.resolve())
        passes = 1  # Tectonic itself reruns until references stabilize.
    else:
        command = [
            str(compiler),
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-no-shell-escape",
            "-output-directory",
            str(path.parent.resolve()),
            path.name,
        ]
        passes = 2  # Page-count labels and footer references require the second pass.
    with (path.parent / "compile.log").open("w", encoding="utf-8") as log:
        try:
            for _ in range(passes):
                result = subprocess.run(
                    command,
                    cwd=path.parent,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=timeout,
                    check=False,
                    env=environment,
                )
                if result.returncode:
                    break
        except subprocess.TimeoutExpired as exc:
            raise ValueError("latex_compile_timeout") from exc
    if result.returncode or not path.with_suffix(".pdf").is_file():
        raise ValueError("latex_compile_failed: see internal compile.log")
