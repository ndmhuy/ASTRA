from io import BytesIO

from docx import Document
from docx.oxml.ns import qn
from fastapi.testclient import TestClient
from PIL import Image

from tests.api.test_ui_jobs import fixture_app
from tests.api.test_ui_preview import start


def test_word_download_uses_approved_revision_and_editable_equations(tmp_path, monkeypatch):
    def sample_assets(directory, *args, **kwargs):
        Image.new("RGB", (30, 30), "black").save(directory / "sample.png")
        return {"p1-1": {"path": "sample.png"}}

    # Exercise real DOCX conversion on hosts without the optional TikZ compiler.
    monkeypatch.setattr("exam_baseline.ui.word_export.render_assets", sample_assets)
    app, _ = fixture_app(tmp_path)
    with TestClient(app) as client:
        job, package, binding = start(client)
        url = f"/api/exams/{job}"
        export_url = url + "/export?type=STUDENT_EXAM&format=docx"
        assert client.get(export_url).status_code == 409
        assert client.post(url + "/approve", json={**binding, "reviewer": "fixture"}).is_success
        response = client.get(export_url)
        assert response.is_success
        assert response.headers["content-disposition"] == 'attachment; filename="de_thi.docx"'
        assert response.headers["content-type"].endswith("wordprocessingml.document")

        doc = Document(BytesIO(response.content))
        student_text = "\n".join(p.text for p in doc.paragraphs)
        assert "Câu 1." in student_text and "Trả lời ngắn" in student_text
        assert package["questions"][0]["explanation"] not in student_text
        assert list(doc.element.iter(qn("m:oMath")))
        assert len(doc.inline_shapes) == 1

        edited = client.put(
            url + "/questions/1",
            json={"revision": binding["revision"], "question": {"stem": r"Tính $\frac{1}{2}$."}},
        )
        assert edited.is_success
        assert client.get(export_url).status_code == 409
        new_binding = {key: edited.json()[key] for key in binding}
        assert client.post(url + "/approve", json={**new_binding, "reviewer": "fixture"}).is_success
        revised = client.get(export_url)
        assert revised.is_success
        doc = Document(BytesIO(revised.content))
        assert list(doc.element.iter(qn("m:f")))
