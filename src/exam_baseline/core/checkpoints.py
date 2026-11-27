"""Atomic native-workflow checkpoints. No provider calls or academic algorithms."""

import json
import os
import tempfile
from hashlib import sha256
from pathlib import Path

VERSION = 1


class CheckpointError(ValueError):
    pass


class GenerationPaused(Exception):
    """A cooperative pause at a validated, durable execution boundary."""


def digest(value) -> str:
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def atomic_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix=".checkpoint-", delete=False
        ) as handle:
            temporary = Path(handle.name)
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def read_json(path: Path):
    try:
        return json.loads(path.read_bytes())
    except (OSError, ValueError) as error:
        raise CheckpointError(
            "Checkpoint is missing or corrupt; no inference was started"
        ) from error


def manifest(request, providers, engine: str, template: str) -> dict:
    return {
        "schemaVersion": VERSION,
        "engine": engine,
        "template": template,
        "requestHash": digest(request),
        "providers": {
            role: {
                "name": str(provider.name),
                "model": str(provider.model),
                # Store a digest, never credentials or raw transport configuration.
                "parametersHash": digest(provider.parameters),
            }
            for role, provider in providers.items()
        },
    }


def response_checkpoint(operation: str, response) -> dict:
    value = response.model_dump()
    return {
        "schemaVersion": VERSION,
        "operation": operation,
        "response": value,
        "sha256": digest(value),
    }


def restore_response(path: Path, operation: str, contract):
    saved = read_json(path)
    if (
        not isinstance(saved, dict)
        or saved.get("schemaVersion") != VERSION
        or saved.get("operation") != operation
        or "response" not in saved
        or saved.get("sha256") != digest(saved["response"])
    ):
        raise CheckpointError("Checkpoint version, operation or output digest does not match")
    try:
        return contract.model_validate(saved["response"])
    except ValueError as error:
        raise CheckpointError("Checkpoint output failed its academic contract") from error
