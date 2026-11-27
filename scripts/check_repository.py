"""Check Git candidates for local artifacts and likely credentials; never print secret values."""

import hashlib
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEY_PATTERNS = (
    re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    re.compile(r"AQ\.[0-9A-Za-z_-]{40,}"),
    re.compile(r"sk-(?:proj-|svcacct-)?[0-9A-Za-z_-]{24,}"),
)
LOCAL_DIRECTORIES = {
    "runs",
    "inputs",
    "tmp",
    "build",
    "dist",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
}


MAS_RUNTIME_SHA256 = {
    "__init__.pyc": "bc8b7ad9b432e4037b716b541108d8ae187bbccb2d0ffd33cb71ed1c0e0443b9",
    "contracts.pyc": "b9419cd80a6f46dd6fecabef2240579d0fed4725b0e0dc5464afdf3b89b3b0d3",
    "runtime.pyc": "030fff00a18500bd14abcf66bdde6e47ea3aafb3097e0fdb2cf4099d9659c8f1",
    "mas_core.zip": "b8097d0f93a76fc30dc6583f37f2858cf03156ca000776d41c6eb7dafbe0dbbe",
}


def check_repository(root: Path = ROOT) -> list[str]:
    listed = (
        subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "-z",
            ],
            check=True,
            capture_output=True,
        )
        .stdout.decode("utf-8")
        .split("\0")
    )
    staged: dict[str, str] = {}
    index = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--stage", "-z"],
        check=True,
        capture_output=True,
    ).stdout.decode("utf-8")
    for entry in filter(None, index.split("\0")):
        metadata, relative = entry.split("\t", 1)
        _, object_id, _ = metadata.split()
        staged[relative] = object_id
    # Also detect a local key accidentally copied to an otherwise ordinary source file.
    local_keys: list[str] = []
    env_path = root / ".env"
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8-sig").splitlines():
            name, separator, value = line.partition("=")
            if separator and re.search(r"API_KEY|SECRET|TOKEN|PASSWORD", name):
                value = value.strip().strip("\"'")
                if len(value) >= 16:
                    local_keys.append(value)
    issues: list[str] = []
    # The release contains intentional BLA decoys. Accept only the exact reviewed bytes.
    for relative in sorted(set(listed) - {""}):
        path = root / relative
        if path.parent == root / "src" / "astra_mas" and path.name in MAS_RUNTIME_SHA256:
            expected = MAS_RUNTIME_SHA256[path.name]
            if (
                not path.is_file()
                or hashlib.sha256(path.read_bytes()).hexdigest() != expected
                or relative not in staged
                or hashlib.sha256(
                    subprocess.check_output(
                        ["git", "-C", str(root), "cat-file", "blob", staged[relative]]
                    )
                ).hexdigest()
                != expected
            ):
                issues.append(f"Invalid MAS release payload: {relative}")
            continue
        parts = Path(relative).parts
        forbidden = (
            any(
                p in LOCAL_DIRECTORIES or p.startswith(".venv") or p.endswith(".egg-info")
                for p in parts
            )
            or (path.name.startswith(".env") and path.name != ".env.example")
            or path.name.startswith(".coverage")
            or path.suffix in {".pyc", ".pem", ".key", ".p12", ".pfx"}
        )
        if forbidden:
            issues.append(f"Local/private artifact: {relative}")
        contents = []
        if path.is_file():
            contents.append(path.read_text(encoding="utf-8-sig", errors="replace"))
        if relative in staged:
            contents.append(
                subprocess.run(
                    ["git", "-C", str(root), "cat-file", "blob", staged[relative]],
                    check=True,
                    capture_output=True,
                ).stdout.decode("utf-8-sig", errors="replace")
            )
        if any(
            any(key in text for key in local_keys) or any(p.search(text) for p in KEY_PATTERNS)
            for text in contents
        ):
            issues.append(f"Possible credential: {relative}")
    return issues


def main() -> int:
    try:
        issues = check_repository()
    except (OSError, subprocess.CalledProcessError):
        print("Cannot inspect Git candidates. Run this check inside an initialized repository.")
        return 2
    for issue in issues:
        print(issue)
    if not issues:
        print("Git candidates contain no detected local artifacts or credentials.")
    return int(bool(issues))


if __name__ == "__main__":
    raise SystemExit(main())
