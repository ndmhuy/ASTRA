"""Small grounded product-knowledge fixture with provenance and status labels."""

from __future__ import annotations


class FixtureAppKnowledgeProvider:
    version = "app-knowledge/fixture-2026-11-15"

    _facts = {
        "functions": (
            "ASTRA hiện có backend tạo đề đồng bộ và giao diện mô phỏng tiến độ. "
            "Hội thoại điều khiển UI, tiến độ job thật và sửa đề theo lô vẫn là đề xuất.",
            "backend@24a2d09 + ui@a1e3f44",
        ),
        "export": (
            "Backend có luồng export cần duyệt cho một số artefact; UI export hiện chỉ một "
            "adapter chưa được xác minh end-to-end. Không thể khẳng định Word đã được tạo.",
            "backend exporter + UI handoff",
        ),
    }

    def answer(self, normalized_text: str) -> dict[str, str]:
        key = "export" if "xuat" in normalized_text else "functions"
        answer, provenance = self._facts[key]
        return {"answer": answer, "provenance": provenance, "version": self.version}
