"""Replay Composer corrections and compile the result: python -m scripts.ui_pdf_smoke."""

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

TABLE_TIKZ = r"""\begin{tikzpicture}
\draw (0,0) grid[xstep=1,ystep=0.8] (3,1.6);
\node at (0.5,1.2) {Khoảng};
\node at (1.5,1.2) {$[0;10)$};
\node at (2.5,1.2) {$[10;20)$};
\node at (0.5,0.4) {Tần số};
\node at (1.5,0.4) {$3$};
\node at (2.5,0.4) {$8$};
\end{tikzpicture}"""


def replay_format_errors(providers):
    """Reproduce the rejected raw table and oversized P3 answer with synthetic data."""
    composer = providers["composer"]
    complete = composer.complete
    repaired = []

    async def compose(prompt):
        payload = json.loads(prompt.user)
        part = payload["part"]
        if feedback := payload.get("contract_feedback"):
            [old] = feedback["previous_questions"]
            assert [slot["id"] for slot in payload["slots"]] == [old["id"]]
            if part == "P1":
                assert feedback["fields"][0]["question_id"] == "P1-12"
                fixed = {
                    **old,
                    "stem": "Dựa vào bảng sau, tần số lớn nhất bằng bao nhiêu?",
                    "illustration_request": ("Bảng hai hàng: Khoảng [0;10), [10;20); Tần số 3, 8."),
                    "choices": {"A": "$8$", "B": "$3$", "C": "$5$", "D": "$11$"},
                    "solution": "Hai tần số là $3$ và $8$, lớn nhất là $8$.",
                }
            else:
                assert part == "P3" and old["answer"] == "1178,1"
                fixed = {
                    **old,
                    "stem": "Đổi $1178{,}1$ mét sang kilômét và làm tròn đến hàng phần mười.",
                    "answer": "1,2",
                    "solution": "Đổi được $1{,}1781$ kilômét, làm tròn được $1{,}2$ kilômét.",
                }
            repaired.append(fixed["id"])
            data = {"questions": [fixed]}
        else:
            result = await complete(prompt)
            data = json.loads(result.text)
            if part == "P1":
                data["questions"][-1]["stem"] = (
                    r"Dùng bảng sau: \begin{array}{cc} 3 & 8 \end{array}."
                )
            elif part == "P3":
                data["questions"][1]["answer"] = "1178,1"
        return Completion(text=json.dumps(data), model=composer.model)

    async def illustrate(prompt):
        [visual] = json.loads(prompt.user)["requests"]
        assert visual["question_id"] == "P1-12" and "3, 8" in visual["description"]
        return Completion(
            text=json.dumps({"drawings": [{"question_id": "P1-12", "latex": TABLE_TIKZ}]}),
            model="offline-contract-fixture",
        )

    composer.complete = compose
    providers["illustrator"].complete = illustrate
    return repaired


def main():
    root = Path("runs/pdf-smoke") / uuid4().hex[:8]
    app, providers = fixture_app(root)
    repaired = replay_format_errors(providers)
    settings = app.state.settings
    settings.latex_cache_dir = Path("runs/latex-cache")
    with TestClient(app) as client:
        assert client.get("/api/health").json()["latexCompilerAvailable"]
        job = client.post(
            "/api/exams/generate", json=PAYLOAD, headers={"Idempotency-Key": "real-tex-smoke"}
        ).json()["jobId"]
        status = wait(client, job)
        assert status["status"] == "completed", status
        assert sorted(repaired) == ["P1-12", "P3-2"] and len(providers["reviewer"].calls) == 1
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
        assert TABLE_TIKZ.encode("utf-8") in source and b"PRIVATE_BANK_KEY" not in source
        assert not package["approved"]
        receipt = {
            "jobId": job,
            "latex": str((root / job / "de_thi.tex").resolve()),
            "pdf": str(output.resolve()),
            "preview": state,
            "repairedQuestions": sorted(repaired),
        }
        (root / "receipt.json").write_text(json.dumps(receipt, indent=2), "utf-8")
        print(json.dumps(receipt))


if __name__ == "__main__":
    main()
