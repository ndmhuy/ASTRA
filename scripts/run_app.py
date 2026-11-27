"""Clone-and-run team entry point. Never submits a model request or exam job."""

import argparse
import getpass
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import urllib.request
import venv
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from exam_baseline.worker_profile import (  # noqa: E402
    DEFAULTS,
    TOKEN_NAMES,
    read_tokens,
    save_profile,
    startup_profile,
    user_profile,
)


def fingerprint(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        if path.is_file():
            digest.update(str(path.relative_to(ROOT)).encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def runtime_python() -> Path:
    candidates = [
        ROOT / ".venv-win/Scripts/python.exe",
        ROOT / ".venv/Scripts/python.exe",
        ROOT / ".venv/bin/python",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    target = ROOT / ".venv"
    venv.create(target, with_pip=True)
    return target / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def prepare_corpus(python: Path) -> None:
    if os.environ.get("EXAM_RAG_PACK_DIR"):
        return
    git = shutil.which("git")
    if not git:
        raise RuntimeError("Install Git first; the Backend needs its pinned RAG corpus")
    ref = (
        os.environ.get("EXAM_RAG_CORPUS_REF")
        or subprocess.check_output(
            [
                str(python),
                "-c",
                "from exam_baseline.config import DEFAULT_RAG_CORPUS_REF; "
                "print(DEFAULT_RAG_CORPUS_REF)",
            ],
            cwd=ROOT,
            text=True,
        ).strip()
    )
    present = (
        subprocess.run(
            [git, "rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}"],
            cwd=ROOT,
            capture_output=True,
            check=False,
        ).returncode
        == 0
    )
    if not present:
        # Single-branch/shallow clones can omit the pinned corpus. Fetch objects
        # only: do not switch branches, merge, or alter the working tree.
        subprocess.run([git, "fetch", "--no-tags", "--", "origin", ref], cwd=ROOT, check=True)


def prepare() -> Path:
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if not npm:
        raise RuntimeError("Install Node24/npm first, then run start.cmd again")
    node = shutil.which("node")
    if (
        not node
        or int(subprocess.check_output([node, "--version"], text=True).lstrip("v").split(".")[0])
        < 24
    ):
        raise RuntimeError("Node24 or newer is required for the current frontend")
    python = runtime_python()
    stamp = python.parent.parent / ".astra-dependencies.sha256"
    signature = fingerprint([ROOT / "pyproject.toml", ROOT / "requirements-tested.txt"])
    if not stamp.is_file() or stamp.read_text() != signature:
        has_pip = (
            subprocess.run(
                [str(python), "-c", "import pip"], capture_output=True, check=False
            ).returncode
            == 0
        )
        if not has_pip:
            subprocess.run([str(python), "-m", "ensurepip", "--upgrade"], cwd=ROOT, check=True)
        command = [str(python), "-m", "pip", "install", "-e", str(ROOT)]
        if (ROOT / "requirements-tested.txt").is_file():
            command.extend(["-c", str(ROOT / "requirements-tested.txt")])
        subprocess.run(command, cwd=ROOT, check=True)
        stamp.write_text(signature)
    prepare_corpus(python)
    frontend = ROOT / "astra-frontend"
    lock_stamp = frontend / "node_modules/.astra-lock.sha256"
    lock_hash = fingerprint([frontend / "package-lock.json", frontend / "package.json"])
    if not lock_stamp.is_file() or lock_stamp.read_text() != lock_hash:
        subprocess.run([npm, "ci"], cwd=frontend, check=True)
        lock_stamp.write_text(lock_hash)
    sources = [
        *frontend.joinpath("src").rglob("*"),
        *frontend.joinpath("public").rglob("*"),
        *frontend.glob("*.json"),
        *frontend.glob("*config.*"),
        frontend / "index.html",
        *(ROOT / "src/exam_baseline/resources/agent").glob("*.json"),
    ]
    build_hash = fingerprint(sources)
    build_stamp = frontend / "dist/.astra-build.sha256"
    if (
        not (frontend / "dist/index.html").is_file()
        or not build_stamp.is_file()
        or build_stamp.read_text() != build_hash
    ):
        subprocess.run([npm, "run", "build"], cwd=frontend, check=True)
        build_stamp.write_text(build_hash)
    return python


def launch_command(python: Path, profile: Path, port: int) -> list[str]:
    return [
        str(python),
        str(ROOT / "scripts/start_mas_worker.py"),
        "--profile",
        str(profile),
        "--port",
        str(port),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--configure", action="store_true", help="Update local Worker access once")
    parser.add_argument("--import-profile", nargs="*", type=Path, default=[])
    parser.add_argument("--profile", type=Path, default=None)
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument(
        "--check", action="store_true", help="Read-only check; no install/start/inference"
    )
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("Port must be between 1 and 65535")
    default = user_profile() if args.configure or args.import_profile else startup_profile()
    profile = (args.profile or default).expanduser().resolve()
    # Explicit import is restricted to the two caller fields; API/Gateway keys ignored.
    try:
        existing = read_tokens([profile])
        tokens = {
            **read_tokens([ROOT / ".env.agent-worker", ROOT / ".env.mas-worker"]),
            **existing,
            **read_tokens(args.import_profile),
        }
    except ValueError as error:
        parser.error(str(error))
    if args.check:
        print(
            json.dumps(
                {
                    "callerCredentialsPresent": all(key in tokens for key in TOKEN_NAMES),
                    "frontendBuilt": (ROOT / "astra-frontend/dist/index.html").is_file(),
                    "nodeAvailable": shutil.which("node") is not None,
                    "profileExists": profile.is_file(),
                    "profileSource": "repository" if profile.is_relative_to(ROOT) else "personal",
                    "inferenceRequests": 0,
                }
            )
        )
        return 0
    try:
        with socket.socket() as connection:
            if connection.connect_ex(("127.0.0.1", args.port)) == 0:
                raise RuntimeError(
                    f"Port {args.port} already in use; stop the old app or choose --port"
                )
        if args.configure or not profile.is_file() or args.import_profile:
            for key in TOKEN_NAMES:
                if key not in tokens or (args.configure and not args.import_profile):
                    if not sys.stdin.isatty():
                        raise ValueError(
                            "Missing Worker access; run start.cmd --configure interactively"
                        )
                    entered = getpass.getpass(
                        f"{key} (Worker access only, hidden; blank keeps current): "
                    )
                    if entered:
                        tokens[key] = entered
            save_profile(profile, tokens, replace=args.configure or bool(args.import_profile))
            print("Worker access saved in your local user profile, outside Git.")
        python = prepare()
        child_env = {**os.environ, **DEFAULTS, **tokens, "ASTRA_WORKER_PROFILE": str(profile)}
        if not args.no_browser:

            def open_when_ready():
                # Only a non-inference health GET; never submit Chat or an exam.
                for _ in range(30):
                    try:
                        with urllib.request.urlopen(
                            f"http://127.0.0.1:{args.port}/api/health", timeout=1
                        ):
                            webbrowser.open(f"http://localhost:{args.port}")
                        return
                    except OSError:
                        threading.Event().wait(0.5)

            threading.Thread(target=open_when_ready, daemon=True).start()
        print(f"ASTRA: http://localhost:{args.port} (Ctrl+C to stop)")
        return subprocess.call(launch_command(python, profile, args.port), cwd=ROOT, env=child_env)
    except (ValueError, RuntimeError, FileExistsError, subprocess.CalledProcessError) as error:
        print(f"Startup failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
