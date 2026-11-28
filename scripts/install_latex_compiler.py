"""Install a pinned portable Windows compiler inside ignored tools/.local/ only."""

import argparse
import io
import json
import platform
import urllib.request
import zipfile
from hashlib import sha256
from pathlib import Path

VERSION = "0.17.0"
ARCHIVE_SHA256 = "f61ce51f0b0ade1015b7de7ef368541c5424e9756ecbd0d7af97d6d48030845f"
URL = (
    "https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.17.0/"
    "tectonic-0.17.0-x86_64-pc-windows-msvc.zip"
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--if-missing", action="store_true", help="Keep an available compiler")
    args = parser.parse_args()
    if args.if_missing:
        from exam_baseline.config import Settings
        from exam_baseline.pipeline.rendering.compiler import find_compiler

        configured = Settings().latex_compiler
        if find_compiler(configured):
            return
        if configured:
            raise SystemExit("EXAM_LATEX_COMPILER does not point to an available executable.")
    if platform.system() != "Windows" or platform.machine().lower() not in {"amd64", "x86_64"}:
        raise SystemExit("Install XeLaTeX/LuaLaTeX/Tectonic on PATH or set EXAM_LATEX_COMPILER.")
    target = Path(__file__).resolve().parents[1] / "tools/.local/tectonic"
    target.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(URL, headers={"User-Agent": "ASTRA-local-compiler-setup"})
    with urllib.request.urlopen(request, timeout=120) as response:
        archive_bytes = response.read()
    if sha256(archive_bytes).hexdigest() != ARCHIVE_SHA256:
        raise SystemExit("Compiler archive checksum mismatch; nothing was installed")
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        matches = [name for name in archive.namelist() if Path(name).name == "tectonic.exe"]
        if len(matches) != 1:
            raise SystemExit("Expected exactly one tectonic.exe in the verified archive")
        executable = archive.read(matches[0])
    path = target / "tectonic.exe"
    path.write_bytes(executable)
    (target / "manifest.json").write_text(
        json.dumps(
            {
                "version": VERSION,
                "source": URL,
                "archive_sha256": ARCHIVE_SHA256,
                "executable_sha256": sha256(executable).hexdigest(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Installed Tectonic {VERSION}: {path}")
    print("The first local compile downloads TeX support packages; exam source stays local.")


if __name__ == "__main__":
    main()
