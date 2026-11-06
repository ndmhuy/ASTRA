# SCHEMA — current GDKT&PL research dossier

- Source address: `Pnn|P1|index|-` for a multiple-choice question; `Pnn|P2|index|a-d` for a true/false subitem. Printed number is not a global identity.
- Topic IDs: T01–T21. A source row may list integrated topics; counts in topic pages intentionally overlap.
- Synthetic sample IDs: the IDs in `data/samples-current.json`; Markdown files live in `samples/<id>.md`. They are synthetic examples, never corpus sources.
- Coverage identity: topic × part × atomic cognitive level, with `sample_ids` linking accepted synthetic examples. `COVERAGE.csv` has one row per current cell (77 rows).
- Current source rows, working labels, provenance, unknowns and OCR paths/SHA: `data/source-observations-current.json`. Current accepted examples: `data/samples-current.json`. Current example coverage: `data/coverage-current.json`.
- Legacy intake, candidate, baseline and audit JSON files are preserved as inputs/receipts; they are not automatically current state.

## Interpretation boundaries

`source_class` distinguishes `provincial_third_party` from `official`; the current scope has 14 provincial third-party papers and zero official papers. Classification provenance is 160 full-OCR/Sol units and 400 structured Luna-triage units, with 39 flagged Sol adjudications within the process. Topic/level labels remain working labels pending teacher review. Source-key validation is incomplete. Do not claim official baseline, generalized frequency, measured difficulty, teacher approval, or runtime compatibility.

## Current schema versions

- `current-source-observations-v2`: full structured source rows plus classification provenance and interpretation limits.
- `research-samples-current-v2`: accepted synthetic samples pending teacher review.
- `research-coverage-current-v1`: 77 linked example cells; not proof of validated corpus frequency.
- `research-dossier-completion-v2`: acceptance/status summary; runtime and teacher approval remain false.
