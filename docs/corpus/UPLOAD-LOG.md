# Upload log - corpus, data processing, profiles and RAG (2026-11-03)

Who: Huy (ndmhuy), with Claude Code (Sonnet 5.5). Branch `feat/ndmhuy/rag-corpus`, cut from `origin/main` (8185395). Append-only record of what was copied, from where, and what was left out. Audience: the team and the reviewer of this PR.

## Sources (private Lecturing repos, snapshot copy, no history)

| Part | Source | State when copied |
| :--- | :--- | :--- |
| Corpus, registry, tools, audit, profiles | `~/Lecturing_Lab/wt-corpus-merged`, branch `data/merged-20261102`, HEAD `5a222ad` | **Live**: Sol (Codex) was still writing. 8 tracked files were modified and 1 call folder untracked at copy time; the snapshot includes those uncommitted files as they were. Profiles for several subjects are partial. |
| Toan profile lab | `~/Lecturing_Lab/agent-review/TOAN-PROFILE-1102` | Paused by the owner; experiment did not finish (see its REPORT.md). |
| Lab plan and Codex prompts | Lecturing `docs/release/next/exam-*` (uncommitted there) | As of 2026-11-03 |
| RAG | branch `claude/format-frames-7af6e7` (`435c3be7`) and commit `558be906` | Committed |

## Placement

- `corpus/` mirrors the corpus repo layout so the tools' relative paths still work: `registry/`, `transcriptions/`, `matrix-samples*/`, `prototypes/`, `docs/`, `audit/{tools,outputs,...}`, `profiles/`, `official-manifests/`, `lab/toan-profile-1102/`.
- `rag/` holds the RAG snapshot (see `rag/README.md`). `docs/corpus/` holds the lab plan, Codex prompts, this log and the summary.

## Left out on purpose

- `official/` PDFs, DOCX, JPG (465 MB, third-party scans): only each folder's README (source URL and Drive id) is in `corpus/official-manifests/`. Checksums: `corpus/SHA256SUMS.txt`.
- `provincial-toan-unverified/` (app-made, never evidence), `audit/work/` (165 MB scratch and product snapshot), lab `sb/` (app session sandbox) and `papers/`, `__pycache__`, `.DS_Store`.
- RAG: production prompts, licence/DRM code, keys, textbooks, the `mas_profile` and `assistant.knowledge` modules.

## Decisions by the owner in this session

- Include transcriptions of real papers (36 MB), exclude original PDFs. This departs from AGENTS.md rule 8 ("do not commit copyrighted exam papers"); the owner chose it for this private repo. The transcriptions came from third-party site copies and are internal evidence only. If the team prefers, they can be removed in a follow-up PR.
- Clean copy of the RAG code, no history.

## Checks run

- Secret scan (`sk-ant-`, `AIza...`, `sk-...` patterns) over copied data and docs: no hits.
- `python -m py_compile` on `rag/src/*.py`: passes. Tests under `rag/tests` were **not run** (missing product modules).
- `git fsck --connectivity-only`: clean after the recovery below. Nothing was run from `corpus/audit/tools` or the lab scripts.

## Incident

A `git gc` triggered automatically mid-run left a `tmp_pack` and lost one commit object (`d9c3d94`, the profile-text-review commit). Nothing was pushed. I moved the branch back to the last good commit (`git reset --mixed bcf1088`, files untouched), expired the reflog of this branch and worktree only, and re-committed the later steps with auto-gc and auto-maintenance off. A 34 MB `tmp_pack_*` garbage file remains in `ASTRA/.git/objects/pack`; it is safe to delete after `git gc` is run by hand.

## Commit sequence (small steps, in order)

1. `chore(repo)` ignore file.
2. Registry, corpus README, checksum manifest; official-paper source manifests.
3. Transcriptions, one commit per subject (19).
4. Matrix samples, prototypes, matrix rules and OCR notes.
5. Audit tools; audit protocol/run log/status; matrices, prompts, test cases.
6. Audit outputs: summaries, then one commit per output folder (20), then recorded model calls in 5 batches.
7. Profiles: spec and README, then one commit per subject (18).
8. Toan profile lab: plan and prompts, protocol/report, scripts, logs, runners, prompts/extraction, outputs.
9. RAG: README, design docs, 687-row curriculum map, retriever, assistant source, tests, bench arm.
10. This log and the summary.

`git log --oneline origin/main..` is the authoritative list.
