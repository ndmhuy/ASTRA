"""Offline-agent, real-TeX API smoke: python -m scripts.ui_pdf_smoke."""

import json
import time
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from exam_baseline.core.contracts import Completion
from tests.api.test_ui_jobs import PAYLOAD, fixture_app, wait

TIKZ = r"""\begin{tikzpicture}[scale=0.8]
\draw[->] (-2,0)--(2,0) node[right] {$x$};
\draw[->] (0,-0.5)--(0,3) node[above] {$y$};
\draw[domain=-1.5:1.5,smooth,variable=\x,thick] plot ({\x},{\x*\x});
\node at (1.2,2.6) {$y=x^2$};
\end{tikzpicture}"""


def main():
    root = Path("runs/pdf-smoke") / uuid4().hex[:8]
    app, providers = fixture_app(root)
    composer = providers["composer"]
    complete = composer.complete

    async def compose(prompt):
        result = await complete(prompt)
        data = json.loads(result.text)
        if data["questions"][0]["id"] == "P1-1":
            data["questions"][0].update(
                stem="Cho đồ thị như hình vẽ. Hàm số nào được biểu diễn?",
                illustration_request="Draw y=x^2 on [-1.5;1.5] with labeled x/y axes.",
                choices={"A": "$y=x^2$", "B": "$y=x$", "C": "$y=-x$", "D": "$y=-x^2$"},
            )
        return Completion(text=json.dumps(data), model=composer.model)

    async def illustrate(prompt):
        return Completion(
            text=json.dumps({"drawings": [{"question_id": "P1-1", "latex": TIKZ}]}),
            model="offline-contract-fixture",
        )

    composer.complete = compose
    providers["illustrator"].complete = illustrate
    with TestClient(app) as client:
        assert client.get("/api/health").json()["latexCompilerAvailable"]
        job = client.post(
            "/api/exams/generate", json=PAYLOAD, headers={"Idempotency-Key": "real-tex-smoke"}
        ).json()["jobId"]
        assert wait(client, job)["status"] == "completed"
        package = client.get(f"/api/exams/{job}").json()
        assert package["hasDrawings"] and not package["visualWarnings"]
        binding = {key: package[key] for key in ("revision", "contentHash")}
        response = client.post(f"/api/exams/{job}/preview", json=binding)
        assert response.status_code == 202, response.text
        deadline = time.monotonic() + 360
        state = response.json()
        while state["status"] in {"queued", "compiling"} and time.monotonic() < deadline:
            time.sleep(0.5)
            state = client.get(state["statusUrl"]).json()
        assert state["status"] == "ready", state
        pdf = client.get(state["pdfUrl"])
        assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF-")
        output = root / "preview.pdf"
        output.write_bytes(pdf.content)
        source = (root / job / "de_thi.tex").read_bytes()
        staged = app.state.ui_jobs.settings.latex_cache_dir / "previews"
        assert any(path.read_bytes() == source for path in staged.glob("*/de_thi.tex"))
        assert b"tikzpicture" in source and b"PRIVATE_BANK_KEY" not in source
        assert not package["approved"]
        receipt = {"jobId": job, "pdf": str(output.resolve()), "preview": state}
        (root / "receipt.json").write_text(json.dumps(receipt, indent=2), "utf-8")
        print(json.dumps(receipt))


if __name__ == "__main__":
    main()
