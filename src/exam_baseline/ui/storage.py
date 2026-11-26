"""Durable job receipts and atomic idempotency, without storing credentials."""

import json
import sqlite3
from pathlib import Path
from typing import Literal
from uuid import uuid4

from exam_baseline.ui.errors import UiError


class JobConflict(ValueError):
    pass


class JobStore:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute(
                "CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, "
                "idem TEXT UNIQUE NOT NULL, request_hash TEXT NOT NULL, data TEXT NOT NULL)"
            )
            db.execute(
                """CREATE TABLE IF NOT EXISTS workspaces (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                    revision INTEGER NOT NULL,
                    draft TEXT NOT NULL,
                    job_id TEXT REFERENCES jobs(id),
                    archived INTEGER NOT NULL DEFAULT 0
                )"""
            )

    def connect(self):
        return sqlite3.connect(self.path, timeout=15)

    def create(
        self, key: str, fingerprint: str, data: dict, workspace_id: str | None = None
    ) -> tuple[dict, bool]:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT request_hash, data FROM jobs WHERE idem=?", (key,)).fetchone()
            if row:
                job = json.loads(row[1])
                if row[0] != fingerprint or job.get("workspaceId") != workspace_id:
                    raise JobConflict("Yêu cầu tạo đề bị trùng mã phiên với một nội dung khác.")
                return job, False
            if workspace_id is not None:
                current = db.execute(
                    """SELECT json_extract(j.data, '$.status') FROM workspaces w
                    LEFT JOIN jobs j ON j.id=w.job_id WHERE w.id=? AND w.archived=0""",
                    (workspace_id,),
                ).fetchone()
                if current is None:
                    raise UiError("workspace_not_found", "Không tìm thấy đề đã lưu.", 404)
                if current[0] in {"queued", "running"}:
                    raise UiError("workspace_generating", "Đề này đang được soạn.")
                data = {**data, "workspaceId": workspace_id}
            data = {**data, "jobId": str(uuid4())}
            db.execute(
                "INSERT INTO jobs VALUES (?, ?, ?, ?)",
                (data["jobId"], key, fingerprint, json.dumps(data, ensure_ascii=False)),
            )
            if workspace_id is not None:
                db.execute(
                    "UPDATE workspaces SET job_id=? WHERE id=?", (data["jobId"], workspace_id)
                )
            return data, True

    def list_workspaces(self) -> list[dict]:
        with self.connect() as db:
            rows = db.execute(
                """SELECT w.id, w.created_at, w.revision, w.draft, w.job_id,
                          json_extract(j.data, '$.status'), json_extract(j.data, '$.request'),
                          json_extract(j.data, '$.error')
                   FROM workspaces w LEFT JOIN jobs j ON j.id=w.job_id
                   WHERE w.archived=0 ORDER BY w.created_at DESC, w.id"""
            ).fetchall()
        return [
            {
                **json.loads(draft),
                "id": id_,
                "createdAt": created_at,
                "revision": revision,
                "jobId": job_id,
                "jobStatus": status,
                "jobMeta": self.workspace_job_meta(request) if request else None,
                "jobError": json.loads(error) if error else None,
            }
            for id_, created_at, revision, draft, job_id, status, request, error in rows
        ]

    @staticmethod
    def workspace_job_meta(raw: str) -> dict:
        request = json.loads(raw)
        return {key: request[key] for key in ("subject", "durationMinutes", "itemCount")}

    def save_workspace(self, workspace_id: str, revision: int, draft: dict) -> int:
        encoded = json.dumps(draft, ensure_ascii=False)
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT revision, draft, archived FROM workspaces WHERE id=?", (workspace_id,)
            ).fetchone()
            if row is None and revision == 0:
                db.execute(
                    "INSERT INTO workspaces (id, revision, draft) VALUES (?, 1, ?)",
                    (workspace_id, encoded),
                )
                return 1
            if row is None or row[2]:
                raise UiError("workspace_not_found", "Đề này không còn trong tủ đề.", 404)
            current, saved, _ = row
            if saved == encoded:
                return current
            if current != revision:
                raise UiError("workspace_changed", "Bản nháp đã được lưu ở một cửa sổ khác.")
            db.execute(
                "UPDATE workspaces SET draft=?, revision=? WHERE id=?",
                (encoded, revision + 1, workspace_id),
            )
            return revision + 1

    def archive_workspace(self, workspace_id: str) -> None:
        with self.connect() as db:
            db.execute(
                """INSERT INTO workspaces (id, revision, draft, archived) VALUES (?, 0, '{}', 1)
                   ON CONFLICT(id) DO UPDATE SET archived=1""",
                (workspace_id,),
            )

    def import_workspace(
        self, workspace_id: str, created_at: str, job_id: str | None, draft: dict
    ) -> Literal["imported", "existing"]:
        encoded = json.dumps(draft, ensure_ascii=False)
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute(
                "SELECT draft, job_id, archived FROM workspaces WHERE id=?", (workspace_id,)
            ).fetchone()
            if existing:
                saved, saved_job, archived = existing
                if not archived and saved_job == job_id and json.loads(saved) == draft:
                    return "existing"
                raise UiError(
                    "workspace_import_conflict",
                    "Bản lưu trên máy chủ khác với bản trên trình duyệt hoặc đã được lưu trữ.",
                )

            if job_id is not None:
                job = db.execute(
                    "SELECT json_extract(data, '$.status') FROM jobs WHERE id=?", (job_id,)
                ).fetchone()
                if job is None or (
                    job[0] == "completed"
                    and not (self.path.parent / job_id / "de_thi.tex").is_file()
                ):
                    raise UiError(
                        "workspace_import_missing_job",
                        "Không tìm thấy phiên tạo đề hoặc tệp đề thi trên máy chủ này.",
                    )
                if db.execute("SELECT 1 FROM workspaces WHERE job_id=?", (job_id,)).fetchone():
                    raise UiError(
                        "workspace_import_conflict",
                        "Phiên tạo đề này đã thuộc một mục trong tủ đề.",
                    )

            db.execute(
                """INSERT INTO workspaces (id, created_at, revision, draft, job_id)
                   VALUES (?, ?, 1, ?, ?)""",
                (workspace_id, created_at, encoded, job_id),
            )
            return "imported"

    def get(self, job_id: str) -> dict:
        with self.connect() as db:
            row = db.execute("SELECT data FROM jobs WHERE id=?", (job_id,)).fetchone()
        if row is None:
            raise KeyError(job_id)
        return json.loads(row[0])

    def save(self, data: dict) -> None:
        with self.connect() as db:
            db.execute(
                "UPDATE jobs SET data=? WHERE id=?",
                (json.dumps(data, ensure_ascii=False), data["jobId"]),
            )

    def interrupt_unfinished(self) -> None:
        with self.connect() as db:
            rows = db.execute("SELECT data FROM jobs").fetchall()
            for (raw,) in rows:
                job = json.loads(raw)
                if job["status"] in {"queued", "running"}:
                    job.update(
                        status="failed",
                        error={
                            "code": "server_restarted",
                            "message": (
                                "Quá trình tạo đề bị gián đoạn do máy chủ khởi động lại. "
                                "Thầy cô vui lòng bấm thử tạo lại."
                            ),
                        },
                    )
                    db.execute(
                        "UPDATE jobs SET data=? WHERE id=?",
                        (json.dumps(job, ensure_ascii=False), job["jobId"]),
                    )
