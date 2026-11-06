# Schema dữ liệu hiện hành

Các JSON current là publications derivation, không thay đổi source/intake receipts.

- [`samples-current.json`](data/samples-current.json): `schema_version`, `samples` (70 accepted records from `scoped-final-bank.json`), `superseded_or_held_ids` (three held drafts: LS-V-002/004/007), `origin`, `teacher_approved`. Mỗi sample giữ `id`, `topic_id`, `part`, `qtype`, stem, options/statements, answers per item, key, solution, model rationale and review.
- [`coverage-current.json`](data/coverage-current.json): `unit=topic-part-atomic-cognitive-level`, `cells` (all 67), `unknown_source_refs`, note. Cell status is `covered_model_checked` or `missing`; open VD cells have no exact-level supporting sample.
- [`source-observations-current.json`](data/source-observations-current.json): 240 source rows from `completion-plan.json`, joined to `sources.json` for `source_class`, OCR SHA and paper status; model is recorded and teacher approval is false.
- [`completion.json`](completion.json): dossier status/quantities/limits. `COVERAGE.csv` is a readable full-row export of the same 67 cells.

P2 units are the individual statements `(P2, question index, a|b|c|d)`; do not count four statements as four printed questions. `D` and `Đ` compare as the same true value only; this normalization does not settle the retained `P2/1a` ambiguity.
