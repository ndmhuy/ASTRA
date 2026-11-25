"""Durable job receipts and atomic idempotency, without storing credentials."""

import json
import sqlite3
from pathlib import Path
from uuid import uuid4


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

    def connect(self):
        return sqlite3.connect(self.path, timeout=15)

    def create(self, key: str, fingerprint: str, data: dict) -> tuple[dict, bool]:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT request_hash, data FROM jobs WHERE idem=?", (key,)).fetchone()
            if row:
                if row[0] != fingerprint:
                    raise JobConflict("Yêu cầu tạo đề bị trùng mã phiên với một nội dung khác.")
                return json.loads(row[1]), False
            data = {**data, "jobId": str(uuid4())}
            db.execute(
                "INSERT INTO jobs VALUES (?, ?, ?, ?)",
                (data["jobId"], key, fingerprint, json.dumps(data, ensure_ascii=False)),
            )
            return data, True

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
