"""Non-interactive, tool-disabled Codex interpretation for local development."""

import asyncio
import json
import os
import shutil
import tempfile
from pathlib import Path

from pydantic import ValidationError

from .contracts import Decision, Turn
from .prompt import SYSTEM, schema, turn_text
from .provider import ProviderFailure


def resolve_codex() -> str:
    shim = shutil.which("codex.cmd" if os.name == "nt" else "codex")
    if not shim:
        raise ValueError("Codex CLI is not installed")
    if os.name != "nt":
        return str(Path(shim).resolve())
    native = (
        Path(shim).parent
        / "node_modules"
        / "@openai"
        / "codex"
        / "node_modules"
        / "@openai"
        / "codex-win32-x64"
        / "vendor"
        / "x86_64-pc-windows-msvc"
        / "bin"
        / "codex.exe"
    )
    if not native.is_file():
        raise ValueError("Native Codex executable is unavailable")
    return str(native.resolve())


class CodexCliInterpretationProvider:
    def __init__(self, executable: str | None = None):
        self.executable = executable or resolve_codex()

    async def interpret(self, turn: Turn, timeout: float) -> Decision:
        with tempfile.TemporaryDirectory(prefix="astra-codex-") as directory:
            root = Path(directory)
            schema_path = root / "schema.json"
            result_path = root / "result.json"
            schema_path.write_text(json.dumps(schema()), encoding="utf-8")
            args = [
                self.executable,
                "exec",
                "--ignore-user-config",
                "--ignore-rules",
                "--ephemeral",
                "--skip-git-repo-check",
                "--sandbox",
                "read-only",
                "--disable",
                "shell_tool",
                "--disable",
                "apps",
                "--disable",
                "view_image",
                "-c",
                'web_search="disabled"',
                "-c",
                "mcp_servers={}",
                "-C",
                str(root),
                "--output-schema",
                str(schema_path),
                "--output-last-message",
                str(result_path),
                "--color",
                "never",
                "-",
            ]
            env = {
                k: v
                for k, v in os.environ.items()
                if not (
                    k.startswith("EXAM_")
                    or k.startswith("ASTRA_AGENT_")
                    or "API_KEY" in k
                    or "TOKEN" in k
                )
            }
            prompt = (
                SYSTEM
                + "\\nReturn only the requested JSON. Do not call tools.\\n"
                + turn_text(turn)
            ).encode("utf-8")
            try:
                process = await asyncio.create_subprocess_exec(
                    *args,
                    cwd=root,
                    env=env,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                    creationflags=getattr(__import__("subprocess"), "CREATE_NO_WINDOW", 0),
                )
            except OSError:
                raise ProviderFailure("configuration") from None
            try:
                await asyncio.wait_for(process.communicate(prompt), timeout=timeout)
                if process.returncode:
                    raise ProviderFailure("configuration")
                if not result_path.is_file() or result_path.stat().st_size > 32768:
                    raise ProviderFailure("schema")
                data = json.loads(result_path.read_text(encoding="utf-8"))
                if not isinstance(data, dict) or set(data) != {"kind", "intents"}:
                    raise ProviderFailure("schema")
                return Decision.model_validate(data)
            except asyncio.TimeoutError:
                raise ProviderFailure("transient") from None
            except (OSError, ValueError, ValidationError):
                raise ProviderFailure("schema") from None
            finally:
                if process.returncode is None:
                    process.kill()
                    await process.wait()
