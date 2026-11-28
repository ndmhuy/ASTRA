"""Team/local Worker caller profiles. Provider keys are never imported."""

import json
import os
import re
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOKEN_NAMES = ("ASTRA_AGENT_WORKER_CALLER_TOKEN", "ASTRA_MAS_CALLER_TOKEN")
DEFAULTS = json.loads(
    (Path(__file__).parent / "resources/agent/worker-client.json").read_text(encoding="utf-8")
)["environment"]


def user_profile() -> Path:
    base = Path(
        os.environ.get("LOCALAPPDATA")
        or os.environ.get("XDG_CONFIG_HOME")
        or Path.home() / ".config"
    )
    return base / "ASTRA" / "worker.env"


def resolve_profile(legacy_name: str, explicit: str | Path | None = None) -> Path:
    override = explicit or os.environ.get("ASTRA_WORKER_PROFILE")
    if override:
        return Path(override).expanduser().resolve()
    legacy = ROOT / legacy_name
    return legacy if legacy.is_file() else user_profile()


def read_tokens(paths: list[Path]) -> dict[str, str]:
    result = {}
    for path in paths:
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            key, separator, value = line.partition("=")
            key = key.strip()
            if not separator or key not in TOKEN_NAMES:
                continue
            value = value.strip().strip("\"'")
            if not re.fullmatch(r"[a-f0-9]{64}", value):
                raise ValueError(f"{key} must be a 64-character Worker caller token")
            result[key] = value
    return result


def save_profile(path: Path, tokens: dict[str, str], *, replace: bool = False) -> None:
    if path.resolve().is_relative_to(ROOT):
        raise ValueError(
            "Save shared credentials outside the Git checkout; import legacy files only"
        )
    if any(not re.fullmatch(r"[a-f0-9]{64}", tokens.get(key, "")) for key in TOKEN_NAMES):
        raise ValueError("Both Worker caller tokens are required; no Gemini/Gateway keys")
    if path.exists() and not replace:
        raise FileExistsError("Profile exists; use --configure to replace it explicitly")
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    content = (
        "\n".join(
            f"{key}={value}"
            for key, value in {**DEFAULTS, **{key: tokens[key] for key in TOKEN_NAMES}}.items()
        )
        + "\n"
    )
    if not replace:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
        return
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix=".worker-", delete=False
        ) as handle:
            temporary = Path(handle.name)
            os.chmod(temporary, 0o600)
            handle.write(content)
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
