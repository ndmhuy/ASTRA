# Vật lí (THPTQG) — sample matrix M0 — note for the owner (26 Oct 2026)

Files: `matrix.json`, `matrix.docx` (Phụ lục I + II, landscape), `matrix.md`, `checks.txt` (16/16), `build.py` (single source; shared builder `../m0lib.py`).

## What the sample is
28 câu, 40 scoring units of 0,25 = 10 điểm, 50 phút: Phần I 18 nhiều lựa chọn; Phần II 4 đúng/sai x 4 ý; Phần III 6 trả lời ngắn (0,25 mỗi câu, not Toán's 0,5). Levels (units): Biết 14 (35%), Hiểu 13 (32,5%), Vận dụng 13 (32,5%). Phần I 10/5/3, Phần II 4/6/6, Phần III 0/2/4. Four chương (nhiệt 11 units, khí 10, từ trường 11, hạt nhân 8) over 20 of the 25 Kết nối tri thức bài (the five asked-for gaps are the four "Bài tập" bài 7, 13, 20, 25 and Bài 24 công nghiệp hạt nhân). Per unit: yêu cầu cần đạt, dạng, năng lực (NL.1 / NL.2 / NL.3), style hint; Phần II: the situation of each câu.

## Sources used (internal evidence only, nothing copied)
- Registered format (`exam_formats/thptqg_2026.py`): 18 + 4 + 6, marks, 50 minutes.
- Lesson list: the table of contents of a school's Vật lí 12 Kết nối tri thức teaching-plan PDF (khbd-vat-li-12, locthanhbaoloc.lamdong.edu.vn, 2024), fetched 26 Oct. The repo's own `vat-li-12.jsonl` is EMPTY, so this list is third-party and unverified against the book itself.
- Shape and level pattern: typed transcripts of the 2025 official Vật lí 0201 and the Ministry 2025 sample, the session's level labels for them (official 0201 by those labels: Phần I 14/4/0, Phần II 7/5/4, Phần III 0/2/4; the sample: 9/8/1, 0/15/1, 0/3/3), and one school matrix (hạt nhân only, 40/30/30, the same 18 + 16 + 6 split). Used for SHAPE only.

## What was invented
All cells and all 40 requirement sentences (none equal to the school spec's 75 lines; the closest, 82% similar, is the phản ứng hạt nhân line, which is the topic's own vocabulary), the four Phần II situations, câu numbering (Phần I numbered by level 1–10 / 11–15 / 16–18), style hints, and the 35/32,5/32,5 split.

## Owner should check
1. Level split: 35/32,5/32,5 here; the school matrix and the Ministry sample table use 40/30/30 for this subject. Which should the sample teach?
2. Phần II rule: this sample varies the levels per câu (câu 1 b NB; câu 4 starts at Hiểu), unlike GDKT&PL's fixed a/b/c/d pattern, because the 2025 official labels show Vật lí Phần II spread Biết to Vận dụng. OK?
3. Lesson titles come from a third-party plan; confirm Bài 1–25 against the book.
4. Coverage: Bài 7, 13, 20, 25 (bài tập) and Bài 24 (công nghiệp hạt nhân) are not asked.
5. Năng lực names NL.1–3 are my wording.

## Not proven
Nothing generated from the sample yet (M3). Docx checked by the app's reader and a LibreOffice render, not opened in Word. The 2025 level evidence is the session's own labelling of subagent transcripts.

## Skeleton check (26 Oct, owner rule: the registered skeleton is the authority)
The sample is slot-addressed: `matrix.json` has a `slots` list (part, position, key, level, topic, requirement per slot) and the rows are derived from it. `check.py` compares it with the slot list read from the registered layout: same slots, same order, none extra, none missing. No block layout is registered for this subject (`blocks_for` returns nothing), so there is no block order to check; none was invented. `checks.txt` now has 27 checks (all pass).
