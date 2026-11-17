import json
import time
from hashlib import sha256

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter

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


def test_preview_exact_source_cache_restart_and_reviewed_pdf_export(tmp_path, compiler):
    app, providers = fixture_app(tmp_path)
    with TestClient(app) as client:
        job, package, binding = start(client)
        before = {role: len(p.calls) for role, p in providers.items()}
        url = f"/api/exams/{job}/preview"
        assert package["preview"]["status"] == "not_requested"
        assert client.get(url + ".pdf", params=binding).status_code == 409
        assert client.post(url, json=binding).status_code == 202
        state = ready(client, job, binding)
        assert state["status"] == "ready" and state["pageCount"] == 1 and state["draft"]
        assert compiler == [(tmp_path / job / "de_thi.tex").read_bytes()]
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


@pytest.mark.parametrize("failure", ["missing", "timeout", "invalid_pdf"])
def test_compiler_failures_have_diagnostics_and_no_pdf(tmp_path, monkeypatch, failure):
    monkeypatch.setattr(
        "exam_baseline.ui.preview.find_compiler",
        lambda _: None if failure == "missing" else "fixture",
    )

    def fail(path, **kwargs):
        (path.parent / "compile.log").write_text("compile diagnostic", "utf-8")
        if failure == "timeout":
            raise ValueError("latex_compile_timeout")
        path.with_suffix(".pdf").write_bytes(b"invalid pdf")

    monkeypatch.setattr("exam_baseline.ui.preview.compile_document", fail)
    app, _ = fixture_app(tmp_path)
    with TestClient(app) as client:
        job, _, binding = start(client)
        url = f"/api/exams/{job}/preview"
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
        assert client.get(state["logUrl"]).text == "compile diagnostic"


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
        source_hash = sha256((tmp_path / job / "de_thi.tex").read_bytes()).hexdigest()
        directory = tmp_path / job / "_preview" / f"{binding['revision']}-{source_hash}"
        directory.mkdir(parents=True)
        (directory / "status.json").write_text(json.dumps({"status": "compiling"}), "utf-8")
        state = client.get(package["preview"]["statusUrl"]).json()
        assert state["error"] == "preview_interrupted"
        client.post(f"/api/exams/{job}/preview", json=binding)
        assert ready(client, job, binding)["status"] == "ready"
