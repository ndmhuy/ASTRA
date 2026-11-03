# Summary - what the RAG branch contains

For the team. Details and provenance: [UPLOAD-LOG.md](UPLOAD-LOG.md).

**Corpus (`corpus/`).** A registry of 134 exam papers (official, provincial, reference) with a usable/unusable flag per subject; 36 MB of transcriptions in 19 subject folders; matrix samples (v1, teacher, v3); 3 prototype papers (Toan, Hoa, Vat li); source manifests and checksums for the original PDFs, which are not in this repo.

**Data processing (`corpus/audit/`).** The stage 1-5 pipeline and helper tools (OCR, extraction, address checks, option coverage, figure review, profile publish), its protocol, run log and status, and all outputs including 1,689 files of recorded model calls. Per-step receipts show what each model call saw and returned.

**Exam profiles by Codex Sol (`corpus/profiles/`).** One folder per subject with rows, distributions, compact profile, paper structures, verification and a note, under `DOSSIER-SPEC.md`. State on 2026-11-03: Toan (22 papers, 748 items) and Hoa (8 papers) extracted; Sinh and Su have cognitive labels and aggregates; the rest are in progress. **No subject is accepted as a complete dossier yet**, and cognitive labels (NB/TH/VD) await teacher review. The snapshot was taken while Sol was still writing.

**Toan profile lab (`corpus/lab/toan-profile-1102/`).** The A/B experiment on whether a profile makes high-discrimination questions harder. Result: **no conclusion**; A1 and B1 stopped because the dev CLI backend rejects images, so no blind scores exist. Paused by the owner.

**RAG (`rag/`).** The existing curriculum RAG: a 687-row draft curriculum map for grades 10-12, a lexical retriever with a 3000-token evidence bundle, the assistant curriculum source with coverage re-ranking and honest gaps, tests, a 30-question eval, and the architecture plan. It compiles but is **not runnable here** (needs two product modules) and its tests were not run.

**Left out.** Original PDFs, app-made provincial Toan, scratch and caches, production prompts, keys, licence code, textbooks.

**Open points.** (1) Transcriptions of real papers conflict with AGENTS.md rule 8; the owner approved them for this private repo. (2) Sol's profiles will change after this snapshot; re-sync later. (3) The agent-log line is not added because `agent-log/` and `tools/agent-log.sh` live on the unmerged docs branch.
