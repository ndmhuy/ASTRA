"""Compile exact student LaTeX locally; cache only validated, revision-bound PDFs."""

import asyncio
import json
import shutil
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from pypdf import PdfReader

from exam_baseline.pipeline.rendering.compiler import compile_document, find_compiler
from exam_baseline.ui.errors import UiError


class PreviewService:
    def __init__(self, root, settings):
        self.root = Path(root)
        self.settings = settings
        self.tasks = {}
        self.capacity = asyncio.Semaphore(1)

    def compiler(self):
        return find_compiler(self.settings.latex_compiler)

    def directory(self, job):
        return self.root / job["jobId"] / "_preview" / f"{job['revision']}-{job['sourceHash']}"

    def status(self, job):
        directory = self.directory(job)
        metadata = directory / "status.json"
        state = json.loads(metadata.read_text("utf-8")) if metadata.is_file() else {}
        if state.get("status") in {"queued", "compiling"} and directory not in self.tasks:
            state = {"status": "failed", "error": "preview_interrupted"}
        if state.get("status") == "ready":
            pdf = directory / "preview.pdf"
            if not pdf.is_file() or sha256(pdf.read_bytes()).hexdigest() != state["pdfHash"]:
                state = {"status": "failed", "error": "preview_artifact_changed"}
        query = f"revision={job['revision']}&contentHash={job['contentHash']}"
        base = f"/api/exams/{job['jobId']}/preview"
        return {
            **state,
            "status": state.get("status", "not_requested" if self.compiler() else "unavailable"),
            "revision": job["revision"],
            "contentHash": job["contentHash"],
            "sourceHash": job["sourceHash"],
            "compilerAvailable": bool(self.compiler()),
            "statusUrl": f"{base}?{query}",
            "pdfUrl": f"{base}.pdf?{query}",
            "logUrl": f"{base}.log?{query}",
            "draft": not bool(job["approval"]),
        }

    def _save(self, directory, state):
        directory.mkdir(parents=True, exist_ok=True)
        temp = directory / "status.tmp"
        temp.write_text(json.dumps(state), "utf-8")
        temp.replace(directory / "status.json")

    def request(self, job):
        state = self.status(job)
        if state["status"] == "ready" or self.directory(job) in self.tasks:
            return state
        compiler = self.compiler()
        if not compiler:
            raise UiError(
                "latex_compiler_unavailable",
                "Install XeLaTeX/LuaLaTeX/Tectonic or run scripts/install_latex_compiler.py",
                503,
            )
        directory = self.directory(job)
        source = (self.root / job["jobId"] / "de_thi.tex").read_bytes()
        if sha256(source).hexdigest() != job["sourceHash"]:
            raise UiError("artifact_changed", "Exam source changed outside the reviewed revision")
        self._save(directory, {"status": "queued"})
        task = asyncio.create_task(self._compile(directory, source, compiler))
        self.tasks[directory] = task
        task.add_done_callback(lambda _: self.tasks.pop(directory, None))
        return self.status(job)

    async def _compile(self, directory, source, compiler):
        # Unique staging prevents canceled/timed-out work from publishing an old PDF.
        # Job roots can be deeply nested on Windows. Keep TeX work paths short;
        # only validated PDF/log/metadata are published into the revision cache.
        attempt = self.settings.latex_cache_dir / "previews" / uuid4().hex
        try:
            async with self.capacity:
                attempt.mkdir(parents=True)
                path = attempt / "de_thi.tex"
                path.write_bytes(source)
                self._save(directory, {"status": "compiling"})
                await asyncio.to_thread(
                    compile_document,
                    path,
                    compiler=compiler,
                    timeout=self.settings.latex_timeout_seconds,
                    cache_directory=self.settings.latex_cache_dir,
                )
                pdf = path.with_suffix(".pdf")
                pages = len(PdfReader(pdf).pages)
                if pages < 1:
                    raise ValueError("empty_pdf")
                digest = sha256(pdf.read_bytes()).hexdigest()
                pending = directory / "preview.tmp"
                shutil.copyfile(pdf, pending)
                pending.replace(directory / "preview.pdf")
                self._copy_log(attempt, directory)
                self._save(directory, {"status": "ready", "pageCount": pages, "pdfHash": digest})
        except asyncio.CancelledError:
            self._save(directory, {"status": "failed", "error": "preview_interrupted"})
            raise
        except Exception as exc:
            if not self._copy_log(attempt, directory):
                (directory / "compile.log").write_text(
                    "Preview failed before compiler diagnostics were available: "
                    f"{type(exc).__name__}; errno={getattr(exc, 'errno', None)}; "
                    f"winerror={getattr(exc, 'winerror', None)}\n",
                    encoding="utf-8",
                )
            code = (
                "latex_compile_timeout"
                if str(exc) == "latex_compile_timeout"
                else ("latex_compile_failed")
            )
            self._save(directory, {"status": "failed", "error": code})

    def _copy_log(self, attempt, directory):
        log = attempt / "compile.log"
        if log.is_file():
            # Compiler has no provider API keys; diagnostics never include private answer files.
            (directory / "compile.log").write_bytes(log.read_bytes())
            return True
        return False

    def file(self, job, *, log=False):
        state = self.status(job)
        if not log and state["status"] != "ready":
            raise UiError(
                "preview_not_ready", "Request preview and poll until ready", details=state
            )
        path = self.directory(job) / ("compile.log" if log else "preview.pdf")
        if not path.is_file():
            raise UiError("preview_log_unavailable", "No compiler diagnostics yet", 404)
        return path

    async def close(self):
        tasks = list(self.tasks.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
