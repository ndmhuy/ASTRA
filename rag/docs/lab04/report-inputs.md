# Lab04 report inputs from the owner

For whoever drafts `25125083_W04/Exercise01/report.md`. The AI may draft only under Huy's review, declared in the Appendix (AGENTS.md rule 5). The statements below are **Huy's own, given in chat on 2026-11-06**; the AI did not witness them. Huy must confirm each one is true when he signs the report, and fill in the blanks from real checks.

## 1. How the feature was developed (Huy's workflow)

1. Huy reviewed and accepted the phased spec and plan (`spec.md`, `plan.md`) before any code was written.
2. The plan was then executed phase by phase by AI agents.
3. Huy checked the tests himself, on his own machine.

| Check | Command Huy ran | Date and time | Result he saw | Evidence |
|---|---|---|---|---|
| Plan review | (reading, no command) | `<fill>` | `<fill: what he changed or accepted>` | commit history of `rag/docs/lab04/` |
| Snapshot tests | `python3 compat/run_snapshot_tests.py` from `rag/` | `<fill>` | `<fill>` | screenshot `<fill>` |
| Baseline tests | `python3 -m unittest discover -s tests -p 'test_astra_rag.py' -v` | `<fill>` | `<fill>` | screenshot `<fill>` |
| CLI queries | see `how-to-query.md` | `<fill>` | `<fill>` | screenshot `<fill>` |

What the AI sessions themselves ran is recorded separately in `p2-run-log.md` and `agent-log/huy.log`. Do not present those runs as Huy's own; only the rows he filled above are his.

## 2. Other work (the exercise asks for it)

Huy's statement: he took part in planning and setting the direction for most of the groups, deciding what each would do. Most of this happened in conversation, so direct evidence is thin. The report should say that plainly and must not claim more than Huy states.

Evidence that does exist in the repo (verifiable with `git log`):

- `4552cc5` `docs(repo): add AGENTS.md with git rules, PR template and agent-log tool`
- `85f2e9a` `docs(mas): draft abstract MVP plan and decision register`
- `d8a5c56` `docs(repo): log Huy's first ASTRA contribution`
- Pull request 1 (merged into `main`) carrying the three commits above.

Evidence Huy may still collect (only if it exists): group-chat screenshots with dates, meeting notes, task assignments, review comments on PRs, entries in `docs/DECISIONS.md` once the team agrees. Leave a blank rather than reconstruct from memory.

Wording for the report (edit to match what actually happened): "Besides the RAG feature, I helped plan and orient most groups' work through discussions. This was mostly spoken or chat-based, so I can show it only through the commits above and `<fill: other evidence>`."

## 3. Facts the report must state honestly

- Done and observed: P2 baseline (index, CLI, receipts), 8 own tests and 57 passing snapshot tests with 6 skipped (adapters, not product integration).
- Not done at the time of this note: P3 to P6, any retrieval-quality numbers, the Streamlit demo, screenshots.
- Profile labels (NB/TH/VD) are agent-reviewed, not teacher-confirmed; curriculum rows are draft.
- Update this list when the other agent finishes the remaining phases, using only what `results.md` and real runs show.
