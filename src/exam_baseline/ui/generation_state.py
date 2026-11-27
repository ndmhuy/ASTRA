"""Transactional lifecycle and execution fencing in the existing job SQLite store."""

import asyncio
import json
import time
from pathlib import Path

from exam_baseline.core.checkpoints import GenerationPaused, atomic_json
from exam_baseline.ui.errors import UiError

POLICY = json.loads(
    (Path(__file__).parents[1] / "resources/agent/recovery-policy.json").read_text("utf-8")
)
ACTIVE = frozenset({"queued", "running", "pausing", "resuming", "retrying"})
RESTING = frozenset({"paused", "interrupted", "cancelled", "failed"})


class ExecutionLost(asyncio.CancelledError):
    pass


class GenerationState:
    def __init__(self, store, *, clock=time.time):
        self.store, self.clock = store, clock

    @staticmethod
    def _get(db, job_id):
        row = db.execute("SELECT data FROM jobs WHERE id=?", (job_id,)).fetchone()
        if row is None:
            raise KeyError(job_id)
        return json.loads(row[0])

    @staticmethod
    def _put(db, job):
        db.execute(
            "UPDATE jobs SET data=? WHERE id=?",
            (json.dumps(job, ensure_ascii=False), job["jobId"]),
        )

    def _owned(self, job, version, owner):
        if (
            job.get("executionVersion", 1) != version
            or job.get("executionOwner") != owner
            or job["status"] not in ACTIVE
            or job.get("executionLeaseUntil", 0) <= self.clock()
        ):
            raise ExecutionLost

    def claim(self, job_id, version, owner):
        with self.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            job = self._get(db, job_id)
            if job.get("executionVersion", 1) != version or job["status"] not in {
                "queued",
                "resuming",
            }:
                return False
            if job.get("executionOwner") and job.get("executionLeaseUntil", 0) > self.clock():
                return False
            job.update(
                executionOwner=owner,
                executionLeaseUntil=self.clock() + POLICY["leaseSeconds"],
            )
            self._put(db, job)
            return True

    def heartbeat(self, job_id, version, owner):
        with self.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            job = self._get(db, job_id)
            self._owned(job, version, owner)
            job["executionLeaseUntil"] = self.clock() + POLICY["leaseSeconds"]
            self._put(db, job)

    def check(self, job_id, version, owner, *, pause=True):
        job = self.store.get(job_id)
        self._owned(job, version, owner)
        if pause and job.get("pauseRequested"):
            raise GenerationPaused
        return job

    def save(self, data):
        with self.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            current = self._get(db, data["jobId"])
            if current["status"] not in ACTIVE:
                return False
            if current.get("executionOwner"):
                try:
                    self._owned(
                        current, data.get("executionVersion", 1), data.get("executionOwner")
                    )
                except ExecutionLost:
                    return False
            if data.get("executionVersion", 1) != current.get("executionVersion", 1):
                return False
            data = {**data, "executionLeaseUntil": current.get("executionLeaseUntil", 0)}
            if current.get("pauseRequested"):
                data.update(status="pausing", pauseRequested=True)
            self._put(db, data)
            return True

    def control(self, job_id, version, operation):
        with self.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            job = self._get(db, job_id)
            current = job.get("executionVersion", 1)
            if current != version:
                if operation in {"resume", "retry"} and job.get("resumedVersion") == version:
                    return job, False
                raise UiError(
                    "stale_generation", "Phiên chạy đã thay đổi. Hãy tải lại trạng thái.", 409
                )
            if operation == "pause":
                if job["status"] in {"paused", "pausing"}:
                    return job, False
                if job["status"] not in ACTIVE:
                    raise UiError(
                        "generation_inactive", "Không có phiên đang chạy để tạm dừng.", 409
                    )
                busy = bool(job.get("executionOwner")) and job["status"] not in {
                    "queued",
                    "resuming",
                }
                job.update(pauseRequested=True, status="pausing" if busy else "paused")
                if not busy:
                    job.update(executionOwner=None, executionLeaseUntil=0)
                job["progress"]["statusMessage"] = (
                    "Đang chờ kết quả đang gọi để lưu và tạm dừng"
                    if job["status"] == "pausing"
                    else "Đã tạm dừng, kết quả hợp lệ được giữ lại"
                )
            elif operation == "cancel":
                if job["status"] not in ACTIVE:
                    return job, False
                job.update(status="cancelled", executionOwner=None, executionLeaseUntil=0)
                job["progress"].update(
                    stageName="cancelled", statusMessage="Đã dừng tạo đề", estimatedSecondsLeft=0
                )
            elif operation in {"resume", "retry"}:
                if job["status"] not in RESTING:
                    return job, False
                if job.get("checkpointVersion") != POLICY["checkpointVersion"]:
                    raise UiError(
                        "checkpoint_incompatible",
                        "Checkpoint cũ không tương thích. Không có yêu cầu AI nào được gửi.",
                        409,
                    )
                if operation == "retry" and job["status"] not in {
                    "failed",
                    "paused",
                    "interrupted",
                }:
                    raise UiError(
                        "generation_not_retryable",
                        "Phiên này cần tiếp tục, không phải thử lại.",
                        409,
                    )
                job.update(
                    status="resuming",
                    executionVersion=current + 1,
                    resumedVersion=current,
                    executionOwner=None,
                    executionLeaseUntil=self.clock() + POLICY["leaseSeconds"],
                    pauseRequested=False,
                    error=None,
                    retry=None,
                )
                job["progress"]["statusMessage"] = "Đang chuẩn bị tiếp tục từ kết quả đã lưu"
            else:
                raise ValueError("Unknown generation control operation")
            self._put(db, job)
            return job, operation in {"resume", "retry"}

    def settle(self, job_id, version, owner, status, *, error=None):
        with self.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            job = self._get(db, job_id)
            try:
                self._owned(job, version, owner)
            except ExecutionLost:
                return False
            job.update(
                status=status,
                error=error,
                executionOwner=None,
                executionLeaseUntil=0,
                pauseRequested=status == "paused",
                manualResumeRequired=status in RESTING,
            )
            job["progress"].update(
                statusMessage={
                    "paused": "Đã tạm dừng. Kết quả hợp lệ đã được lưu; thầy cô có thể tiếp tục.",
                    "interrupted": "Phiên bị gián đoạn. Kết quả đã lưu được giữ; cần bấm tiếp tục.",
                    "failed": "Chưa hoàn tất. Kiểm tra nguyên nhân và cấu hình trước khi thử lại.",
                }.get(status, status),
                estimatedSecondsLeft=0,
            )
            self._put(db, job)
            return True

    def persist(self, job_id, version, owner, path, data):
        """Fence file writes and checkpoint index updates with the same DB write lock."""
        path = path.resolve()
        root = (self.store.path.parent / job_id / "_generation").resolve()
        if not path.resolve().is_relative_to(root):
            raise ValueError("Checkpoint path escaped its generation directory")
        with self.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            job = self._get(db, job_id)
            self._owned(job, version, owner)
            atomic_json(path, data)
            if path.parent.name == "checkpoints":
                operation = data["operation"]
                index = job.setdefault("checkpoints", {})
                index[operation] = {
                    "file": str(path.relative_to(root)),
                    "sha256": data["sha256"],
                    "stage": data.get("stage"),
                    "revision": data.get("revision"),
                    "questionIds": [q["id"] for q in data["response"].get("questions", [])],
                }
                latest = max((item.get("revision") or 1 for item in index.values()), default=1)
                ids = {
                    qid
                    for item in index.values()
                    if item.get("revision") == latest and item.get("stage") == "composer"
                    for qid in item["questionIds"]
                }
                job["progress"]["completedItems"] = len(ids)
                self._put(db, job)

    def recover(self, job_id=None):
        with self.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            rows = db.execute(
                "SELECT data FROM jobs" + (" WHERE id=?" if job_id else ""),
                (job_id,) if job_id else (),
            ).fetchall()
            for (raw,) in rows:
                job = json.loads(raw)
                if job["status"] in ACTIVE and job.get("executionLeaseUntil", 0) <= self.clock():
                    job.update(
                        status="interrupted",
                        executionOwner=None,
                        executionLeaseUntil=0,
                        manualResumeRequired=True,
                        error={
                            "code": "server_restarted",
                            "message": (
                                "Phiên chạy đã gián đoạn. Có thể tiếp tục từ checkpoint; "
                                "chưa có inference nào tự khởi động."
                            ),
                        },
                    )
                    job["progress"]["statusMessage"] = "Bị gián đoạn; cần tiếp tục thủ công"
                    self._put(db, job)
