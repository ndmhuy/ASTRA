# ASTRA

Team Trial and Success's exam-generation and verification project. This branch
contains a runnable **local retrieval and testing workbench**: a subject-and-scope
query returns relevant source passages, question labels, score breakdowns and
provenance across **BM25 (`bm25-v2`)**, **Embedding (`embedding-char-word-v1`)**,
and **Hybrid (`hybrid-rrf-v1`)** retrieval modes.

## Run the prototype app

Requires Python 3.11 (tested with 3.11.1). No runtime packages or API keys needed.

```powershell
python -m rag_workflow.app
```

Open <http://127.0.0.1:8765>. Try:

```text
Vật lí lớp 11 chương 1 về dao động
Toán lớp 11 chương 2 về cấp số cộng
Vật lí lớp 10 chương 2 vận tốc gia tốc định luật 2 Newton
```

- **Three retrieval modes:** Select `Hybrid (BM25 + Embedding)`, `BM25 (Lexical + Bigrams)`, or `Embedding (Vector Cosine)` in the UI, or click **Compare 3 modes** to inspect all three side by side.
- **MAS Exam-Matrix & Topic-Pack Handoff (Toán THPT):** Provides `retrieve_exam_context()` and `get_topic_pack()` (plus `/api/matrix-retrieve` and `/api/topic-packs/{id}`) to deliver complete, untruncated Topic Packs (`71` Toán packs, `748` observations, `139` ready examples, `133` curriculum rows) per `question_id` (`12 P1`, `4 P2` with `a..d` levels, `6 P3`), with explicit `NB/TH/VD` vs `VDC`/`unknown` policies, strict evidence separation (`official`, `provincial_third_party`, `synthetic`, `curriculum`), and `mas-intake-v1` adapter output.
- **In-app Benchmark & Evaluation Lab:** Expand **Benchmark & evaluation lab** and click **Run benchmark suite** to verify gold targets (`auto-corpus-check-v1`) and compare `Hit@5`, `Recall@5`, `MRR`, `Passage Hit@5`, `Gap Accuracy`, and `False Gap Rate`. Click any benchmark query to test it live.
- **Existing corpus integration:** Reads the private corpus from the local `origin/staging/rag` Git snapshot (**687 curriculum rows and 108 usable exam transcriptions**; 26 registry papers excluded). Exam transcriptions are split along question boundaries (`Câu N`, `Question N`, `PHẦN I`) with exact character offsets.

Run `git fetch --all` once if the corpus branch is unavailable locally.
`--corpus-ref <commit>` pins a snapshot; `--demo` restores the 12-note demo with
session text imports. `--corpus <file.jsonl>` loads an approved passage pack.
`--export-pack <dir>` and `--pack-dir <dir>` export and load a self-contained
portable Toán THPT release folder with SHA-256 verification on Windows.

## Documentation

- [RAG guide: MAS handoff, Topic Pack & Matrix API, multi-mode ranking, benchmark results and verification](docs/rag-workflow.md)
- [Evaluation benchmark suite, auto-verifier & Toán THPT acceptance suite](eval/README.md)
- [Team MVP proposal and unresolved decisions](docs/mvp-plan.md)
- [Repository collaboration rules](AGENTS.md)
- [AI session record](agent-log/chautanphat.log)

## Verify & Benchmark

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
./.venv/Scripts/python.exe scripts/verify.py
./.venv/Scripts/python.exe -m rag_workflow.eval --acceptance
./.venv/Scripts/python.exe -m rag_workflow.eval --existing --mode all
```

`scripts/verify.py` checks compilation, Ruff lint/formatting, 61 unit/HTTP/CLI/eval/MAS-handoff
tests and JavaScript syntax when Node is available.
