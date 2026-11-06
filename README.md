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
Vật lí lớp 11 chương 4 về định luật Ohm
Toán lớp 11 chương 2 về cấp số cộng
```

The app includes 12 original demo notes. Add `.txt` / `.md` notes through the UI,
then search by their subject and scope. Imported text stays in memory until the
server stops. Demo chapter labels are illustrative; they are not a reviewed
textbook map. This prototype retrieves evidence; it does not generate exams.

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
