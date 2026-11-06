# ASTRA

Team Trial and Success's exam-generation and verification project. This branch
contains a runnable **local retrieval prototype**: a subject-and-range query
returns relevant source passages and provenance for a later generation stage.

## Run the prototype

Requires Python 3.11 (tested with 3.11.1). No runtime packages or API keys needed.

```powershell
python -m rag_workflow.app
```

Open <http://127.0.0.1:8765>. Try:

```text
Vật lí lớp 11 chương 1 về dao động
Toán lớp 11 chương 2 về cấp số cộng
```

The app now reads the existing private corpus from the local
`origin/staging/rag` Git snapshot: **687 curriculum rows and 108 usable exam
transcriptions** (26 registry papers excluded). Choose curriculum search for
grade/chapter/lesson ranges, or exam search for subject/topic, e.g. `Vật lí dao động`.
Exam grade/chapter mappings are unknown. Draft/OCR status and provenance remain
visible; results are for internal prototype use. Keys, profiles and audits are
excluded. No source text is copied into this branch or sent to external services.

Run `git fetch --all` once if the corpus branch is unavailable locally.
`--corpus-ref <commit>` pins a snapshot; `--demo` restores the 12-note demo with
session text imports. `--corpus <file.jsonl>` loads an approved passage pack.
This prototype retrieves evidence; it does not generate exams.

## Documentation

- [Workflow, API examples, verification, screenshots and limitations](docs/rag-workflow.md)
- [Team MVP proposal and unresolved decisions](docs/mvp-plan.md)
- [Repository collaboration rules](AGENTS.md)
- [AI session record](agent-log/chautanphat.log)

## Verify

```powershell
python -m unittest discover -s tests -v
```

See the workflow document for the complete compilation/lint/test command and the
optional browser test. Development dependencies are pinned separately from the
dependency-free app. Verification uses synthetic data; real-corpus relevance and
teacher acceptance have not been measured.
