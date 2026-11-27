import json
import time
from hashlib import sha256
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter

from exam_baseline.thpt.content import choice_latex
from exam_baseline.thpt.rendering import render_choice_rows
from tests.api.test_ui_jobs import PAYLOAD, fixture_app, wait


def start(client):
    job = client.post(
        "/api/exams/generate", json=PAYLOAD, headers={"Idempotency-Key": "preview"}
    ).json()["jobId"]
    assert wait(client, job)["status"] == "completed"
    package = client.get(f"/api/exams/{job}").json()
    binding = {key: package[key] for key in ("revision", "contentHash")}
    return job, package, binding


def ready(client, job, binding):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        state = client.get(f"/api/exams/{job}/preview", params=binding).json()
        if state["status"] not in {"queued", "compiling"}:
            return state
        time.sleep(0.01)
    raise AssertionError("Preview did not finish")


@pytest.fixture
def compiler(monkeypatch):
    calls = []
    monkeypatch.setattr("exam_baseline.ui.preview.find_compiler", lambda _: "fixture-compiler")

    def compile_fixture(path, **kwargs):
        calls.append(path.read_bytes())
        writer = PdfWriter()
        writer.add_blank_page(width=595, height=842)
        writer.write(path.with_suffix(".pdf"))
        (path.parent / "compile.log").write_text("fixture: no TeX executed", "utf-8")

    monkeypatch.setattr("exam_baseline.ui.preview.compile_document", compile_fixture)
    return calls


def test_preview_exact_source_cache_restart_and_reviewed_pdf_export(
    tmp_path, compiler, monkeypatch
):
    app, providers = fixture_app(tmp_path)
    with TestClient(app) as client:
        job, package, binding = start(client)
        before = {role: len(p.calls) for role, p in providers.items()}
        url = f"/api/exams/{job}/preview"
        assert package["preview"]["status"] == "not_requested"
        assert client.get(url + ".pdf", params=binding).status_code == 409
        replace = Path.replace

        def same_directory_replace(source, target):
            # A configured cache may reside on another filesystem/drive from jobs.
            if source.parent != Path(target).parent:
                raise OSError(18, "Cross-device move is not supported")
            return replace(source, target)

        monkeypatch.setattr(Path, "replace", same_directory_replace)
        assert client.post(url, json=binding).status_code == 202
        state = ready(client, job, binding)
        assert state["status"] == "ready" and state["pageCount"] == 1 and state["draft"]
        assert compiler == [(tmp_path / job / "de_thi.tex").read_bytes()]
        # Staging must not append another UUID directory under the long source-hash cache.
        assert not list((tmp_path / job / "_preview").glob("*/attempt-*"))
        staged_sources = list((tmp_path / "_tex-cache" / "previews").glob("*/de_thi.tex"))
        assert len(staged_sources) == 1
        assert staged_sources[0].read_bytes() == compiler[0]
        assert client.post(url, json=binding).status_code == 200
        assert len(compiler) == 1
        pdf = client.get(state["pdfUrl"])
        assert pdf.content.startswith(b"%PDF-")
        assert pdf.headers["content-type"] == "application/pdf"
        assert pdf.headers["content-disposition"].startswith("inline;")
        assert "Cộng trực tiếp" not in pdf.content.decode("latin1")
        assert {role: len(p.calls) for role, p in providers.items()} == before
        export = f"/api/exams/{job}/export?type=STUDENT_EXAM&format=pdf"
        assert client.get(export).status_code == 409
        assert (
            client.post(
                f"/api/exams/{job}/approve", json={**binding, "reviewer": "fixture-teacher"}
            ).status_code
            == 200
        )
        assert client.get(export).content == pdf.content
        assert client.get(state["logUrl"]).status_code == 200
    restarted, _ = fixture_app(tmp_path)
    with TestClient(restarted) as client:
        assert client.get(url, params=binding).json()["status"] == "ready"
        assert client.post(url, json=binding).status_code == 200
        assert len(compiler) == 1


def test_revision_hash_source_and_cached_pdf_tampering_are_rejected(tmp_path, compiler):
    app, _ = fixture_app(tmp_path)
    with TestClient(app) as client:
        job, _, binding = start(client)
        url = f"/api/exams/{job}/preview"
        assert client.post(url, json={**binding, "contentHash": "0" * 64}).status_code == 409
        client.post(url, json=binding)
        state = ready(client, job, binding)
        cached = next((tmp_path / job / "_preview").glob("*/preview.pdf"))
        cached.write_bytes(b"tampered")
        assert client.get(state["pdfUrl"]).status_code == 409
        client.post(url, json=binding)
        assert ready(client, job, binding)["status"] == "ready"
        client.put(
            f"/api/exams/{job}/questions/1",
            json={
                "revision": binding["revision"],
                "question": {"stem": "Tính $2+2$ (bản mới)."},
            },
        )
        assert client.get(state["pdfUrl"]).status_code == 409
        package = client.get(f"/api/exams/{job}").json()
        new_binding = {key: package[key] for key in binding}
        assert package["preview"]["status"] == "not_requested"
        (tmp_path / job / "de_thi.tex").write_bytes(b"tampered source")
        assert client.post(url, json=new_binding).status_code == 409


@pytest.mark.parametrize("old_layout", ["separate_lines", "always_pair"])
def test_saved_exam_preview_reflows_choices_and_preserves_approval(
    tmp_path, compiler, monkeypatch, old_layout
):
    app, providers = fixture_app(tmp_path)
    with TestClient(app) as client:

        def old_choice_rows(choices):
            if old_layout == "always_pair":
                return render_choice_rows(choices, legacy_grid=True)
            return "\n".join(
                rf"\noindent {label}. {choice_latex(choices[label])}\\" for label in "ABCD"
            )

        with monkeypatch.context() as legacy:
            legacy.setattr("exam_baseline.thpt.rendering.render_choice_rows", old_choice_rows)
            job, package, binding = start(client)

        url = f"/api/exams/{job}"
        assert (
            client.post(
                url + "/approve", json={**binding, "reviewer": "fixture-teacher"}
            ).status_code
            == 200
        )
        source_path = tmp_path / job / "de_thi.tex"
        saved = source_path.read_bytes()
        old_key = f"{binding['revision']}-{package['preview']['sourceHash']}"
        if old_layout == "always_pair":
            old_key += "-2"
        old_cache = tmp_path / job / "_preview" / old_key
        old_cache.mkdir(parents=True)
        old_pdf = b"%PDF-old layout"
        (old_cache / "preview.pdf").write_bytes(old_pdf)
        (old_cache / "status.json").write_text(
            json.dumps({"status": "ready", "pdfHash": sha256(old_pdf).hexdigest()}), "utf-8"
        )

        before = {role: len(provider.calls) for role, provider in providers.items()}
        assert client.get(url + "/preview", params=binding).json()["status"] == "not_requested"
        assert client.post(url + "/preview", json=binding).status_code == 202
        state = ready(client, job, binding)
        assert state["status"] == "ready" and not state["draft"]
        marker = b"% ASTRA_CHOICE_ROWS_FIT"
        assert marker not in saved
        assert compiler[0].count(marker) == 12
        assert b"\n\\noindent A. " not in compiler[0]
        assert b"\\parbox[t]" in compiler[0]
        assert source_path.read_bytes() == saved
        assert client.get(url + "/export?type=STUDENT_EXAM&format=tex").content == saved
        pdf = client.get(state["pdfUrl"]).content
        assert pdf.startswith(b"%PDF-") and pdf != old_pdf
        assert client.get(url + "/export?type=STUDENT_EXAM&format=pdf").content == pdf
        assert {role: len(provider.calls) for role, provider in providers.items()} == before


@pytest.mark.parametrize("failure", ["missing", "timeout", "invalid_pdf", "preparation"])
def test_compiler_failures_have_diagnostics_and_no_pdf(tmp_path, monkeypatch, failure):
    monkeypatch.setattr(
        "exam_baseline.ui.preview.find_compiler",
        lambda _: None if failure == "missing" else "fixture",
    )

    def fail(path, **kwargs):
        if failure == "preparation":
            raise OSError(206, "test preparation failure")
        (path.parent / "compile.log").write_text("compile diagnostic", "utf-8")
        if failure == "timeout":
            raise ValueError("latex_compile_timeout")
        path.with_suffix(".pdf").write_bytes(b"invalid pdf")

    monkeypatch.setattr("exam_baseline.ui.preview.compile_document", fail)
    app, _ = fixture_app(tmp_path)
    with TestClient(app) as client:
        job, _, binding = start(client)
        url = f"/api/exams/{job}/preview"
        if failure == "preparation":
            directory = app.state.ui_jobs.previews.directory(app.state.ui_jobs.get(job))
            directory.mkdir(parents=True)
            (directory / "compile.log").write_text("stale successful compile", "utf-8")
        response = client.post(url, json=binding)
        if failure == "missing":
            assert response.status_code == 503
            return
        state = ready(client, job, binding)
        assert state["status"] == "failed"
        assert state["error"] == (
            "latex_compile_timeout" if failure == "timeout" else "latex_compile_failed"
        )
        assert client.get(state["pdfUrl"]).status_code == 409
        diagnostics = client.get(state["logUrl"])
        assert diagnostics.status_code == 200
        if failure == "preparation":
            assert "OSError" in diagnostics.text
            assert "stale successful compile" not in diagnostics.text
        else:
            assert diagnostics.text == "compile diagnostic"


def test_legacy_visual_warnings_are_explicit_and_source_is_not_rewritten(tmp_path):
    app, _ = fixture_app(tmp_path)
    with TestClient(app) as client:
        job, _, _ = start(client)
        manager = app.state.ui_jobs
        raw = manager.get(job)
        raw["rawQuestions"][0]["stem"] = "Dựa vào bảng biến thiên như sau."
        manager.store.save(raw)
        source = (tmp_path / job / "de_thi.tex").read_bytes()
        package = client.get(f"/api/exams/{job}").json()
        assert package["visualWarnings"][0]["questionId"] == "P1-1"
        assert not package["hasDrawings"]
        assert (tmp_path / job / "de_thi.tex").read_bytes() == source


def test_interrupted_preview_is_retryable(tmp_path, compiler):
    app, _ = fixture_app(tmp_path)
    with TestClient(app) as client:
        job, package, binding = start(client)
        manager = app.state.ui_jobs
        directory = manager.previews.directory(manager.get(job))
        directory.mkdir(parents=True)
        (directory / "status.json").write_text(json.dumps({"status": "compiling"}), "utf-8")
        state = client.get(package["preview"]["statusUrl"]).json()
        assert state["error"] == "preview_interrupted"
        client.post(f"/api/exams/{job}/preview", json=binding)
        assert ready(client, job, binding)["status"] == "ready"
