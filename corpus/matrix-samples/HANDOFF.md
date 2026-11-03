# M0 sample matrices: hand-off to the cloud session (26 Oct 2026, from S-C lab)

Done and checked: `gdktpl/`, `toan/`, `vat-li/`, `hoa-hoc/` (GDKTPL 26/26, others 27/27 checks). Not started: the other 13 registered subjects (yours). Nothing here is in the app repo; the owner approves each subject first.

## Files
- `m0lib.py` shared builder (`Spec`): one subject = one plain-data spec -> `matrix.json`, `matrix.docx`, `matrix.md`.
- `<subject>/build.py` the spec of that subject (data only, then `Spec(SPEC).write(HERE)`). `gdktpl/_v1.py` holds GDKT&PL's original cell data, `gdktpl/build.py` maps it.
- `check.py` the checker. `<subject>/NOTE.md` one page per subject (sources, what was invented, what the owner should check). `checks.txt` last result.

## Paths you MUST change on your machine
Both `m0lib.py` (`GT`, `_SCR`) and `check.py` (`GT`, `scratch`) hard-code the lab paths: `GT = /Users/huynguyen/Lecturing_Lab/lab-r1/work-r0/Grading_Tools` (the app code, R0 worktree at e703f6f5) and a scratch dir `/Users/huynguyen/Lecturing_Lab/lab-r1/runs/m0`. Point `GT` at your checkout's `Grading_Tools` and the scratch dir at any empty folder.

## Run
```bash
cd matrix-samples/toan && <app venv>/bin/python3 build.py        # writes matrix.json, matrix.docx, matrix.md next to it
cd .. && <app venv>/bin/python3 check.py toan THPTQG Toan        # args: folder, exam_type, subject id; writes toan/checks.txt; exit 1 on any FAIL
```
Use the app's venv (the app code imports its own dependencies). No model, no network. python-docx is NOT installed and not needed: the Word file is written with the app's `exchange.ooxml.DocxBuilder`, then `m0lib._landscape` post-processes the XML (A4 landscape, 8 pt cells). To eyeball it: `soffice --headless --convert-to pdf matrix.docx` into an empty folder.

## What check.py asserts (16 base + SKELETON, 26 or 27 in all)
Base: the json loads through `matrix.upgrade_matrix_document` with no row dropped; levels = `DEFAULT_LEVELS` (NB, TH, VD); every count an integer (Phần II rows are statement rows addressed by references); part totals = `composer_steps` of the registered format; `matrix_validation` ok/published and no conflicts; marks = the layout's total (score_per_correct x num_questions); the docx parses through `matrix_import.propose_from_file` with `propose_with_assistant` patched to raise (so no assistant call), source=table, unread empty, rows equal the json by (part, topic, level, references), level units equal the json totals, every Phần II câu has a-d.
SKELETON (owner rule: the registered skeleton is the authority; a sample only fills its slots): slot list read from `exam_formats.thptqg_2026.layout_for(subject).parts[].questions()` (part, question index, slot key, type); the sample's `slots` list must equal it exactly (count, order, none missing/extra/duplicate, same part order); every slot names part, position, level, topic, requirement; per part `exam_formats.blocks.blocks_for` blocks must match each slot's `block` when registered; the json rows must be exactly the distribution of the slots. Mutation-tested: dropping a slot and adding an extra one makes it FAIL.

## The builder, with one worked example
A spec is a dict (see `toan/build.py` for a full one, 34 cells):
```python
from m0lib import Spec
T = {"b1": ("Chủ đề 1: ...", "Bài 1: ...")}                     # topic id -> (chủ đề, nội dung/đơn vị kiến thức); order = table order
CELLS = [                                                         # (part, ref, topic id, level, requirement, style hint, competency)
 ("P1", 1, "b1", "NB", "Nhận biết ...", "khái niệm trực tiếp", "NL.1"),      # mcq / short answer: ref = question index
 ("P2", (1, "a"), "b1", "NB", "Nhận biết ...", "", "NL.1"),                 # true/false: ref = (question index, statement letter)
]
STEMS = {("P2", 1): "tình huống của câu 1 của Phần II"}          # one situation per true/false câu (needed for the style text)
SPEC = {"subject": "Toan", "exam_type": "THPTQG", "title": "TOÁN, LỚP 12", "intro": "Đề thi ...",
        "topics": T, "parts": {"P1": {"type": "mcq", "unit": 0.25}, "P2": {"type": "true_false", "unit": 0.25}, "P3": {"type": "short_answer", "unit": 0.5}},
        "cells": CELLS, "stems": STEMS, "level_cues": {"NB": "...", "TH": "...", "VD": "..."},
        "competencies": {"NL.1": "..."}, "scoring": {"total": 10.0, "duration_minutes": 90}}
Spec(SPEC).write(HERE)
```
Rules: one cell per answer SLOT of the registered layout (every a-d of every Phần II câu). `unit` = marks of one slot (Phần II ý average 0,25 of the câu's 1,0; short answer 0,5 for Toán, 0,25 for the sciences). `part` ids and types must match the registry (`composer_steps`). The builder emits the `slots` list (skeleton order, with `block` filled from `blocks_for`), the rows (one per part/topic/level, with `references`, `marks`, `note`, `items`), Phụ lục I (type x level grid, câu addresses `C1 C13`, `1A 1B`, totals) and Phụ lục II (one line per slot: mức độ, yêu cầu cần đạt, câu, dạng, năng lực).

## Pitfalls found
1. **Totals-row label.** `matrix_import` skips a totals row only when its label is exactly a known total word (`Tổng số câu`, `Tổng số điểm`, `Tỷ lệ %`, `Tổng`, ...). "Tổng số câu / ý" was read as DATA and doubled every count. `m0lib` writes the exact labels; keep them.
2. **Header words.** Type x level headers must read like `Nhiều lựa chọn - Biết` / `Đúng sai - Vận dụng` / `Trả lời ngắn - Hiểu`; Phụ lục II needs the columns `Mức độ`, `Câu`, `Dạng` and a `Nội dung/đơn vị kiến thức` column (it is the topic column the importer prefers).
3. **Parts passed to the importer.** `propose_from_file` must get plain-string `question_type` values as the web route builds them (`composer_steps` -> `part_id, label, question_type, width`); passing the raw `QuestionType` enum made every cell unread.
4. **Scratch base dir.** Importing app code resolves the owner's real Google Drive workspace unless `LECTURING_BASE_DIR` / `LECTURING_STATE_DIR` are set first; `m0lib` and `check.py` now set them to a scratch folder before any app import. Keep that order, and never run app code from a build script without it.
5. **The `\quad` row.** An option row written `A. x \quad B. y` keeps `\quad` in option A's text for the key check; real papers use `\makebox` rows. Not a sample problem, noted from R0 run 4.
6. **No block layout for THPTQG subjects.** `blocks_for("THPTQG", subject, part)` returns `()` for GDKTPL, Toán, Vật lí, Hóa: their parts are plain `Uniform(count, question)`; Phần II groups of 4 are slots a-d of one question, not blocks. The block check then reports "none registered" and stops. Check the same for each subject you add (Ngữ văn and the language subjects use blocks, see `thptqg_2026.py _language_blocks`).

## V-ACT: written, never run
`check.py` has a non-THPTQG path (every câu of a part is one slot, from `composer_steps`) and calls `blocks_for("VACT", ...)`, which reads `VACT_BLOCKS` (TV 20 single + 5 + 5 passages; TA 5/5/5/7/8; TO 12 single + 3 x 2 + 4 x 3; KH 2 logic + 2 data + 6 science, 3 each). `m0lib.Spec.slots()` fills `block` from the same table. No V-ACT sample exists, so this path has had NO run; expect to fix details (V-ACT has one slot per câu, four options, no level columns in its own forms, and its parts TV/TA/TO/KH each hold 30 câu). Do not trust it until it fails on a mutation and passes on a real sample.

## Per-subject checklist (what I did each time)
1. Registered shape from `thptqg_2026.py` (counts, marks, minutes). 2. Lesson list from `exam_generator/curriculum_map_data/<subject>-12.jsonl` (some are empty or draft: Vật lí 12 is empty; say where the list came from). 3. Shape/level evidence only from `docs/mas-cloud/official-exams-2025-transcripts/` and `tests/fixtures/mas_judged/levels/`; never copy a question. 4. Write cells; run `build.py`, `check.py`; render the docx. 5. Compare requirement lines with the school spec lines for the subject (difflib; I reported max similarity). 6. Write `NOTE.md`: sources, what was invented, what the owner should check, not proven.
