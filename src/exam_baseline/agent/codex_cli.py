"""Non-interactive, tool-disabled Codex interpretation for local development."""

import asyncio
import json
import logging
import os
import re
import shutil
import tempfile
import time
from pathlib import Path

from pydantic import ValidationError

from .contracts import INTENTS, Decision, Turn
from .prompt import SYSTEM, schema, turn_text
from .provider import ProviderFailure

logger = logging.getLogger("exam_baseline.agent.provider")


def sanitized_stderr(data: bytes) -> str:
    for line in reversed(data.decode("utf-8", errors="replace").splitlines()):
        if "ERROR:" not in line:
            continue
        raw = line.split("ERROR:", 1)[1].strip()
        try:
            message = str(json.loads(raw)["error"]["message"])
        except (ValueError, KeyError, TypeError):
            message = raw
        message = re.sub(
            r"(?i)(bearer\s+|(?:api[_-]?key|token)\s*[:=]\s*)\S+", r"\1[redacted]", message
        )
        message = re.sub(r"(?i)\b(?:sk-|AIza)[A-Za-z0-9_-]{10,}", "[redacted]", message)
        return message[:1000]
    return "(no diagnostic error text)"


def codex_output_schema() -> dict:
    result = schema()
    for item in result["properties"]["intents"]["items"]["anyOf"]:
        intent_id = item["properties"]["id"]["enum"][0]
        args = item["properties"]["args"]
        for name, rule in INTENTS[intent_id]["args"].items():
            if rule.endswith("?"):
                args["properties"][name] = {"anyOf": [args["properties"][name], {"type": "null"}]}
        args["required"] = list(args["properties"])

    def strip_unsupported(value):
        if isinstance(value, dict):
            return {
                key: strip_unsupported(item)
                for key, item in value.items()
                if key not in {"minLength", "maxLength", "minimum", "maximum", "maxItems"}
            }
        if isinstance(value, list):
            return [strip_unsupported(item) for item in value]
        return value

    return strip_unsupported(result)


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
        started = time.monotonic()
        with tempfile.TemporaryDirectory(prefix="astra-codex-") as directory:
            root = Path(directory)
            schema_path = root / "schema.json"
            result_path = root / "result.json"
            schema_path.write_text(json.dumps(codex_output_schema()), encoding="utf-8")
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
                SYSTEM + "\nReturn only the requested JSON. Do not call tools.\n" + turn_text(turn)
            ).encode("utf-8")
            try:
                process = await asyncio.create_subprocess_exec(
                    *args,
                    cwd=root,
                    env=env,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.PIPE,
                    creationflags=getattr(__import__("subprocess"), "CREATE_NO_WINDOW", 0),
                )
            except OSError as error:
                logger.error("codex_spawn_failed category=%s", type(error).__name__)
                raise ProviderFailure("configuration") from None
            try:
                _, stderr = await asyncio.wait_for(
                    process.communicate(prompt), timeout=max(0.1, timeout - 0.5)
                )
                exists = result_path.is_file()
                logger.info(
                    "codex_process exit=%s elapsed_ms=%.1f output_file=%s",
                    process.returncode,
                    (time.monotonic() - started) * 1000,
                    exists,
                )
                if process.returncode:
                    logger.error("codex_process_failure stderr=%s", sanitized_stderr(stderr))
                    raise ProviderFailure("configuration")
                if not exists or result_path.stat().st_size > 32768:
                    logger.error("codex_output_invalid category=missing_or_oversize")
                    raise ProviderFailure("schema")
                data = json.loads(result_path.read_text(encoding="utf-8"))
                if not isinstance(data, dict) or set(data) != {"kind", "intents"}:
                    raise ProviderFailure("schema")
                for intent in data.get("intents", []):
                    if isinstance(intent, dict) and isinstance(intent.get("args"), dict):
                        intent["args"] = {
                            key: value for key, value in intent["args"].items() if value is not None
                        }
                decision = Decision.model_validate(data)
                logger.info(
                    "codex_output_valid kind=%s intents=%s",
                    decision.kind,
                    [i.id for i in decision.intents],
                )
                return decision
            except asyncio.TimeoutError:
                logger.error("codex_timeout elapsed_ms=%.1f", (time.monotonic() - started) * 1000)
                raise ProviderFailure("transient") from None
            except (OSError, ValueError, ValidationError) as error:
                logger.error("codex_parse_failed category=%s", type(error).__name__)
                raise ProviderFailure("schema") from None
            finally:
                if process.returncode is None:
                    process.kill()
                    await process.wait()
