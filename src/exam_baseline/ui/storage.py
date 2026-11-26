"""Durable job receipts and atomic idempotency, without storing credentials."""

import json
import sqlite3
from hashlib import sha256
from pathlib import Path
from typing import Literal
from uuid import uuid4

from exam_baseline.ui.errors import UiError
from exam_baseline.ui.exam_source import PENDING_NAME, SOURCE_NAME, publish_source, settle_source

EXAM_VERSION_FIELDS = (
    "rawQuestions",
    "rawPassages",
    "drawings",
    "solutions",
    "solverResultsVersion",
    "manualEdits",
    "approval",
    "sourceHash",
    "contentHash",
)


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
            db.execute(
                """CREATE TABLE IF NOT EXISTS exam_versions (
                    job_id TEXT NOT NULL REFERENCES jobs(id),
                    revision INTEGER NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                    change TEXT NOT NULL,
                    question_id INTEGER,
                    restored_from INTEGER,
                    data TEXT NOT NULL,
                    source BLOB,
                    PRIMARY KEY (job_id, revision)
                )"""
            )
            db.execute(
                """CREATE TABLE IF NOT EXISTS workspace_jobs (
                    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
                    job_id TEXT PRIMARY KEY REFERENCES jobs(id)
                )"""
            )
            db.execute(
                """CREATE TABLE IF NOT EXISTS exam_changes (
                    job_id TEXT NOT NULL REFERENCES jobs(id),
                    id TEXT NOT NULL,
                    fingerprint TEXT NOT NULL,
                    data TEXT NOT NULL,
                    PRIMARY KEY (job_id, id)
                )"""
            )
            db.execute(
                """INSERT OR IGNORE INTO workspace_jobs
                   SELECT w.id, j.id FROM workspaces w JOIN jobs j ON w.job_id=j.id"""
            )
            db.execute(
                """INSERT OR IGNORE INTO workspace_jobs
                   SELECT w.id, j.id FROM workspaces w
                   JOIN jobs j ON w.id=json_extract(j.data, '$.workspaceId')"""
            )
            db.execute(
                """UPDATE workspaces SET job_id=(
                       SELECT j.id FROM workspace_jobs l JOIN jobs j ON j.id=l.job_id
                       WHERE l.workspace_id=workspaces.id
                         AND json_extract(j.data, '$.status')='completed'
                       ORDER BY json_extract(j.data, '$.createdAt') DESC, j.rowid DESC LIMIT 1
                   ) WHERE job_id IS NOT NULL AND NOT EXISTS (
                       SELECT 1 FROM jobs j WHERE j.id=workspaces.job_id
                       AND json_extract(j.data, '$.status')='completed'
                   )"""
            )
        self._seed_versions()

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
                    "SELECT 1 FROM workspaces WHERE id=? AND archived=0",
                    (workspace_id,),
                ).fetchone()
                if current is None:
                    raise UiError("workspace_not_found", "Không tìm thấy đề đã lưu.", 404)
                if db.execute(
                    """SELECT 1 FROM workspace_jobs l JOIN jobs j ON j.id=l.job_id
                       WHERE l.workspace_id=? AND json_extract(j.data, '$.status') IN
                       ('queued', 'running') LIMIT 1""",
                    (workspace_id,),
                ).fetchone():
                    raise UiError("workspace_generating", "Đề này đang được soạn.")
                data = {**data, "workspaceId": workspace_id}
            data = {**data, "jobId": str(uuid4())}
            db.execute(
                "INSERT INTO jobs VALUES (?, ?, ?, ?)",
                (data["jobId"], key, fingerprint, json.dumps(data, ensure_ascii=False)),
            )
            if workspace_id is not None:
                db.execute(
                    "INSERT INTO workspace_jobs VALUES (?, ?)", (workspace_id, data["jobId"])
                )
            return data, True

    def list_workspaces(self) -> list[dict]:
        with self.connect() as db:
            rows = db.execute(
                """SELECT w.id, w.created_at, w.revision, w.draft, j.id,
                          json_extract(j.data, '$.status'), json_extract(j.data, '$.request'),
                          json_extract(j.data, '$.error'), g.id,
                          json_extract(g.data, '$.status'), json_extract(g.data, '$.error')
                   FROM workspaces w LEFT JOIN jobs g ON g.id=(
                       SELECT attempt.id FROM workspace_jobs l
                       JOIN jobs attempt ON attempt.id=l.job_id
                       WHERE l.workspace_id=w.id
                       ORDER BY attempt.rowid DESC LIMIT 1)
                   LEFT JOIN jobs j ON j.id=coalesce(
                       (SELECT id FROM jobs WHERE id=w.job_id
                        AND json_extract(data, '$.status')='completed'), g.id)
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
                "generationId": attempt,
                "generationStatus": attempt_status,
                "generationError": json.loads(attempt_error) if attempt_error else None,
            }
            for (
                id_,
                created_at,
                revision,
                draft,
                job_id,
                status,
                request,
                error,
                attempt,
                attempt_status,
                attempt_error,
            ) in rows
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
                if db.execute("SELECT 1 FROM workspace_jobs WHERE job_id=?", (job_id,)).fetchone():
                    raise UiError(
                        "workspace_import_conflict",
                        "Phiên tạo đề này đã thuộc một mục trong tủ đề.",
                    )

            db.execute(
                """INSERT INTO workspaces (id, created_at, revision, draft, job_id)
                   VALUES (?, ?, 1, ?, ?)""",
                (workspace_id, created_at, encoded, job_id),
            )
            if job_id is not None:
                db.execute("INSERT INTO workspace_jobs VALUES (?, ?)", (workspace_id, job_id))
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
            if data["status"] == "completed":
                db.execute(
                    "UPDATE exam_versions SET data=? WHERE job_id=? AND revision=?",
                    (self._snapshot(data), data["jobId"], data["revision"]),
                )

    @staticmethod
    def _snapshot(job: dict) -> str:
        return json.dumps(
            {key: job[key] for key in EXAM_VERSION_FIELDS if key in job}, ensure_ascii=False
        )

    def _seed_versions(self) -> None:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            for marker in self.path.parent.glob(f"*/{PENDING_NAME}"):
                row = db.execute(
                    "SELECT json_extract(data, '$.sourceHash') FROM jobs WHERE id=?",
                    (marker.parent.name,),
                ).fetchone()
                settle_source(marker.parent, row[0] if row else None)
            rows = db.execute(
                """SELECT j.data FROM jobs j
                   WHERE json_extract(j.data, '$.status')='completed'
                   AND NOT EXISTS (SELECT 1 FROM exam_versions v WHERE v.job_id=j.id)"""
            ).fetchall()
            for (raw,) in rows:
                job = json.loads(raw)
                path = self.path.parent / job["jobId"] / SOURCE_NAME
                source = path.read_bytes() if path.is_file() else None
                if source is not None and sha256(source).hexdigest() != job["sourceHash"]:
                    source = None
                db.execute(
                    """INSERT INTO exam_versions (job_id, revision, change, data, source)
                       VALUES (?, ?, 'baseline', ?, ?)""",
                    (job["jobId"], job["revision"], self._snapshot(job), source),
                )

    def save_version(
        self,
        job: dict,
        source: bytes,
        change: str,
        *,
        question_id: int | None = None,
        restored_from: int | None = None,
        promotion: tuple[str, str] | None = None,
        change_id: str | None = None,
    ) -> None:
        job_id, revision = job["jobId"], job["revision"]
        root = self.path.parent / job_id
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT data FROM jobs WHERE id=?", (job_id,)).fetchone()
            previous = json.loads(row[0])
            expected = change == "generated" and previous["status"] in {"queued", "running"}
            if not expected and previous.get("revision") != revision - 1:
                raise UiError("stale_revision", "Đề thi đã có bản cập nhật mới hơn.")
            committed_hash = previous.get("sourceHash")
            settle_source(root, committed_hash)
            try:
                if promotion is not None:
                    workspace_id, expected = promotion
                    changed = db.execute(
                        "UPDATE workspaces SET job_id=? WHERE id=? AND job_id=? AND archived=0",
                        (job_id, workspace_id, expected),
                    )
                    if changed.rowcount != 1:
                        raise UiError("stale_revision", "Đề đang dùng đã thay đổi.")
                db.execute(
                    """INSERT INTO exam_versions
                       (job_id, revision, change, question_id, restored_from, data, source)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        job_id,
                        revision,
                        change,
                        question_id,
                        restored_from,
                        self._snapshot(job),
                        source,
                    ),
                )
                db.execute(
                    "UPDATE jobs SET data=? WHERE id=?",
                    (json.dumps(job, ensure_ascii=False), job_id),
                )
                if change == "generated":
                    db.execute(
                        """UPDATE workspaces SET job_id=?
                           WHERE id=(SELECT workspace_id FROM workspace_jobs WHERE job_id=?)""",
                        (job_id, job_id),
                    )
                if change_id is not None:
                    self._finish_change(db, job_id, change_id, "completed", revision, None)
                publish_source(root, source)
                db.commit()
                committed_hash = job["sourceHash"]
            except Exception:
                db.rollback()
                raise
            finally:
                settle_source(root, committed_hash)

    def list_versions(self, job_id: str) -> list[dict]:
        with self.connect() as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                """SELECT revision, created_at AS createdAt, change, question_id AS questionId,
                          restored_from AS restoredFrom, source IS NOT NULL AS restorable
                   FROM exam_versions WHERE job_id=? ORDER BY revision DESC""",
                (job_id,),
            ).fetchall()
        return [{**row, "restorable": bool(row["restorable"])} for row in rows]

    def workspace_job(self, workspace_id: str) -> str | None:
        with self.connect() as db:
            row = db.execute(
                "SELECT job_id FROM workspaces WHERE id=? AND archived=0", (workspace_id,)
            ).fetchone()
        if row is None:
            raise UiError("workspace_not_found", "Không tìm thấy đề đã lưu.", 404)
        return row[0]

    def begin_change(self, job_id: str, change_id: str, signature: str, data: dict):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT fingerprint, data FROM exam_changes WHERE job_id=? AND id=?",
                (job_id, change_id),
            ).fetchone()
            if row is not None:
                if row[0] != signature:
                    raise JobConflict("Mã yêu cầu chỉnh sửa đã được dùng cho nội dung khác.")
                return json.loads(row[1])
            db.execute(
                "INSERT INTO exam_changes VALUES (?, ?, ?, ?)",
                (job_id, change_id, signature, json.dumps(data, ensure_ascii=False)),
            )
        return None

    @staticmethod
    def _finish_change(db, job_id, change_id, status, revision, error):
        db.execute(
            """UPDATE exam_changes SET data=json_set(data, '$.status', ?, '$.afterRevision', ?,
                      '$.finishedAt', strftime('%Y-%m-%dT%H:%M:%fZ', 'now'), '$.error', json(?))
               WHERE job_id=? AND id=? AND json_extract(data, '$.status')='pending'""",
            (status, revision, json.dumps(error, ensure_ascii=False), job_id, change_id),
        )

    def fail_change(self, job_id, change_id, error):
        with self.connect() as db:
            self._finish_change(db, job_id, change_id, "failed", None, error)

    def get_change(self, job_id, change_id):
        with self.connect() as db:
            row = db.execute(
                "SELECT data FROM exam_changes WHERE job_id=? AND id=?", (job_id, change_id)
            ).fetchone()
        if row is None:
            raise UiError("exam_change_not_found", "Không tìm thấy thay đổi này.", 404)
        return json.loads(row[0])

    def workspace_changes(self, workspace_id):
        self.workspace_job(workspace_id)
        with self.connect() as db:
            rows = db.execute(
                """SELECT c.data FROM exam_changes c JOIN workspace_jobs l ON l.job_id=c.job_id
                   WHERE l.workspace_id=? ORDER BY c.rowid""",
                (workspace_id,),
            ).fetchall()
        return [json.loads(raw) for (raw,) in rows]

    def owns_job(self, workspace_id: str, job_id: str) -> bool:
        with self.connect() as db:
            return (
                db.execute(
                    "SELECT 1 FROM workspace_jobs WHERE workspace_id=? AND job_id=?",
                    (workspace_id, job_id),
                ).fetchone()
                is not None
            )

    def workspace_versions(self, workspace_id: str) -> list[dict]:
        with self.connect() as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                """SELECT v.job_id AS jobId, v.revision, v.created_at AS createdAt, v.change,
                          v.question_id AS questionId, v.restored_from AS restoredFrom,
                          v.source IS NOT NULL AS restorable
                   FROM workspace_jobs l JOIN exam_versions v ON v.job_id=l.job_id
                   WHERE l.workspace_id=? ORDER BY v.created_at DESC, v.revision DESC""",
                (workspace_id,),
            ).fetchall()
        return [{**row, "restorable": bool(row["restorable"])} for row in rows]

    def get_version(self, job_id: str, revision: int) -> tuple[dict, bytes | None]:
        with self.connect() as db:
            row = db.execute(
                "SELECT data, source FROM exam_versions WHERE job_id=? AND revision=?",
                (job_id, revision),
            ).fetchone()
        if row is None:
            raise UiError("exam_version_not_found", "Không tìm thấy phiên bản đề này.", 404)
        return json.loads(row[0]), row[1]

    def interrupt_unfinished(self) -> None:
        with self.connect() as db:
            rows = db.execute(
                "SELECT job_id, id FROM exam_changes WHERE json_extract(data, '$.status')='pending'"
            ).fetchall()
            for job_id, change_id in rows:
                self._finish_change(
                    db,
                    job_id,
                    change_id,
                    "failed",
                    None,
                    {
                        "code": "server_restarted",
                        "message": "Thay đổi bị gián đoạn khi máy chủ khởi động lại.",
                    },
                )
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
