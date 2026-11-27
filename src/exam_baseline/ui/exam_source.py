"""Keep the current LaTeX file in sync with a committed exam revision."""

import os
from hashlib import sha256
from pathlib import Path

SOURCE_NAME = "de_thi.tex"
PENDING_NAME = ".de_thi.pending"


def _read(path: Path) -> bytes | None:
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None


def _replace(path: Path, data: bytes) -> None:
    staged = path.with_name(path.name + ".tmp")
    try:
        with staged.open("wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        staged.replace(path)
    finally:
        staged.unlink(missing_ok=True)


def publish_source(root: Path, source: bytes) -> None:
    path = root / SOURCE_NAME
    previous = _read(path)
    checkpoint = b"0" if previous is None else b"1" + previous
    pending = sha256(source).hexdigest().encode("ascii") + b"\n" + checkpoint
    _replace(root / PENDING_NAME, pending)
    _replace(path, source)


def settle_source(root: Path, committed_hash: str | None) -> None:
    """Roll back an interrupted publication only if its bytes reached the current file."""
    marker = root / PENDING_NAME
    pending = _read(marker)
    if pending is None:
        return
    published_hash, previous = pending.split(b"\n", 1)
    if published_hash.decode("ascii") != committed_hash:
        path = root / SOURCE_NAME
        current = _read(path)
        if current is not None and sha256(current).hexdigest().encode("ascii") == published_hash:
            if previous[:1] == b"1":
                _replace(path, previous[1:])
            else:
                path.unlink()
    marker.unlink()
