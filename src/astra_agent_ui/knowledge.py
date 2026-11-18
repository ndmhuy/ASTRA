from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .models import CapabilitySummary


class ApplicationKnowledgeSource(Protocol):
    status: str

    def answer(self, query: str, capabilities: list[CapabilitySummary]) -> str | None: ...


@dataclass(frozen=True)
class RegistryKnowledgeSource:
    """Current fallback: verified runtime registry only, no fictional document."""

    status: str = "verified_ui_registry_only"

    def answer(self, query: str, capabilities: list[CapabilitySummary]) -> str | None:
        del query
        real = [item.description for item in capabilities if item.status == "available_real"]
        if not real:
            return "ASTRA chưa xác nhận được chức năng khả dụng trong giao diện hiện tại."
        return "Trong phiên bản hiện tại, ASTRA đã xác minh các chức năng: " + "; ".join(real) + "."


@dataclass(frozen=True)
class ApprovedJsonKnowledgeSource:
    """Future read-only adapter. No production document is shipped with this change."""

    version: str
    compatible_baseline: str
    entries: tuple[dict[str, str], ...]
    status: str = "approved_document"

    @classmethod
    def load(cls, path: Path, expected_baseline: str) -> ApprovedJsonKnowledgeSource:
        if path.stat().st_size > 256 * 1024:
            raise ValueError("knowledge document exceeds the 256 KiB limit")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("approved") is not True:
            raise ValueError("knowledge document is not approved")
        if payload.get("compatibleBaseline") != expected_baseline:
            raise ValueError("knowledge document is stale or incompatible")
        version = payload.get("version")
        entries = payload.get("entries")
        if not isinstance(version, str) or not version or not isinstance(entries, list):
            raise ValueError("knowledge document metadata is malformed")
        clean: list[dict[str, str]] = []
        for entry in entries:
            if (
                not isinstance(entry, dict)
                or not isinstance(entry.get("question"), str)
                or not isinstance(entry.get("answer"), str)
            ):
                raise ValueError("knowledge entry is malformed")
            clean.append({"question": entry["question"][:300], "answer": entry["answer"][:1500]})
        return cls(version=version, compatible_baseline=expected_baseline, entries=tuple(clean))

    def answer(self, query: str, capabilities: list[CapabilitySummary]) -> str | None:
        words = {word.casefold() for word in query.split() if len(word) > 2}
        ranked = sorted(
            self.entries,
            key=lambda entry: len(words & {word.casefold() for word in entry["question"].split()}),
            reverse=True,
        )
        if not ranked or not words:
            return None
        return ranked[0]["answer"]
