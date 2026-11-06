# GDKT&PL (THPTQG) — sample matrix M0 — note for the owner (26 Oct 2026)

Files: `matrix.json` (loads through `upgrade_matrix_document`), `matrix.docx` (Phụ lục I ma trận + Phụ lục II đặc tả, landscape), `matrix.md` (same, teacher-readable), `checks.txt`, `build.py` (single source; edit the data there and re-run).

## What the sample is
28 câu, 40 scoring units of 0,25 = 10 điểm: Phần I 24 câu nhiều lựa chọn; Phần II 4 câu đúng/sai x 4 ý. Levels: Biết 16 (40%), Hiểu 12 (30%), Vận dụng 12 (30%). Phần I: Biết 12 / Hiểu 8 / Vận dụng 4. Phần II: ý a Biết, ý b Hiểu, ý c–d Vận dụng, in every câu. All 16 bài of the Kết nối tri thức book, six chủ đề; Phần II câu 1–4 sit on Bài 1, 6, 9, 15. Per unit: yêu cầu cần đạt, dạng, năng lực, and for Phần II the situation each câu is built on. Level cues (what "Biết/Hiểu/Vận dụng" look like in the stem) are in the json.

## Sources used
- Bài list and order: the repo's curriculum map `gdktpl-12.jsonl` (Kết nối tri thức; status draft, taken from a third-party plan, so lesson titles should be checked against the book).
- Format shape and table layout: the owner's HK1 matrix (`Ma_tran_GDKTPL_12_HK1_2025-2026.xlsx` / the repo fixture docx): the two appendices, columns type x level, câu addresses `C1`, `1C`. Used for LAYOUT ONLY.
- Registered format: 24 + 4, 0,25 and 1,0 per câu, 10 điểm (`exam_formats/thptqg_2026.py`).
- No official 2025/2026 paper or spec text was opened for this subject, so nothing could be copied from one.

## What was invented
Everything below the layout: which bài get how many câu and at which level; all 40 requirement sentences (written fresh; none identical to the HK1 sheet's 40 lines; 7 pairs are more than 80% similar by character match, all on the same topic phrase "thực hiện trách nhiệm xã hội của doanh nghiệp"); the four situations; câu numbering (Phần I numbered by level, Biết 1–12, Hiểu 13–20, Vận dụng 21–24); style hints per cell ("khái niệm trực tiếp", "tình huống 2–3 dòng"…); the 15 / 5 / 2,5 % per-bài shares that follow from the counts.

## Owner should check
1. Level split 16/12/12 (40/30/30) and Phần II rule a=Biết, b=Hiểu, c–d=Vận dụng: is that the shape you want the sample to teach? The default matrix and the HK1 file use other splits (the HK1 file puts the MCQ at Biết/Hiểu only and the Vận dụng all in Phần II).
2. Economics versus law weight: Bài 1–7 (kinh tế) have 13 of the 24 MCQ and 2 of the 4 Phần II câu; Bài 8–16 (pháp luật) have 11 MCQ and 2 câu. Change if the real paper leans differently.
3. Năng lực codes: I used NL.1 nhận thức, NL.2 tìm hiểu, NL.3 vận dụng, following the HK1 sheet's NL.1/NL.3; NL.2 is not used. Confirm the names.
4. Bài titles come from a draft map; confirm against the textbook.
5. Whether the Phần II situations (growth table, corporate responsibility, family property, maritime sovereignty) are the kinds you want the model to imitate.

## Not proven
Nothing was generated from this sample: whether the model, shown it, produces better matrices is the M3 measurement. The docx was checked by the app's reader and by a LibreOffice render; it was not opened in Word.

## Skeleton check (26 Oct, owner rule: the registered skeleton is the authority)
The sample is slot-addressed: `matrix.json` has a `slots` list (part, position, key, level, topic, requirement per slot) and the rows are derived from it. `check.py` compares it with the slot list read from the registered layout: same slots, same order, none extra, none missing. No block layout is registered for this subject (`blocks_for` returns nothing), so there is no block order to check; none was invented. `checks.txt` now has 26 checks (all pass).
