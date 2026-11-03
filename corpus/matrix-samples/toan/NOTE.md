# Toán (THPTQG) — sample matrix M0 — note for the owner (26 Oct 2026)

Files: `matrix.json` (loads through `upgrade_matrix_document`), `matrix.docx` (Phụ lục I ma trận + Phụ lục II đặc tả, landscape, 8 pages), `matrix.md`, `checks.txt` (16/16), `build.py` (single source; edit the data there and re-run; shared builder `../m0lib.py`).

## What the sample is
22 câu, 34 scoring units, 10 điểm, 90 phút: Phần I 12 nhiều lựa chọn (0,25); Phần II 4 đúng/sai x 4 ý (trung bình 0,25 mỗi ý); Phần III 6 trả lời ngắn (0,5). Levels (units): Biết 12, Hiểu 12, Vận dụng 10; marks 3,0 / 3,5 / 3,5 (30/35/35 %). Phần I 8/3/1, Phần II 4/7/5 (ý a Biết in every câu), Phần III 0/2/4. Topics: 18 of the 19 Kết nối tri thức lớp 12 bài in six chủ đề (Bài 8 is not asked) plus two lớp 10–11 foundation units (cấp số, tổ hợp–xác suất). Per unit: yêu cầu cần đạt, dạng, năng lực (TD / GQ / MHH), style hint; Phần II: the situation of each câu.

## Sources used (internal evidence only, nothing copied)
- Registered format: 12 + 4 + 6, marks, 90 minutes (`exam_formats/thptqg_2026.py`).
- Lesson list: curriculum map `toan-12.jsonl` (chapter VI has no bài entries in the map; Bài 18–19 names come from the school spec below).
- Table shape and the TD/GQ/MHH codes: a school matrix + specification for Toán 12 (`docs/mas-cloud/level-sources/toan12-cuoi-hk2-2025-2026`), which also uses the 10/2/0, 2/11/3, 0/0/6 pattern of the Ministry sample.
- Level pattern and topic spread: the typed transcripts of the 2025 official Toán 0101 and the Ministry 2025 sample, and the session's level labels for them. Read for the SHAPE only (how many câu per kind, which chapters, what a Vận dụng câu looks like); no question, number or stem was reused.

## What was invented
Every cell: which bài gets which câu at which level; all 34 requirement sentences (none identical to the school spec's 185 lines; the closest, 77% similar, is the nguyên hàm Biết line); the four Phần II situations (growth of a cubic, motion by integral, a 3-D layout with a coverage sphere, a two-stage probability); câu numbering; style hints; the 30/35/35 mark split.

## Owner should check
1. Level split. The 2025 official paper by the session's labels is NB 4 / TH 17 / VD 13 (units); the Ministry sample table is 12 / 13 / 9; this sample is 12 / 12 / 10. I took the sample's shape because it is the one that teaches all three levels. Say if the sample should instead lean to the official paper (harder).
2. lớp 10–11 content: the 2025 official paper used it in about half its câu; this sample has 2 units (C8 cấp số cộng, P3 câu 5 tổ hợp). The app's default Toán topics are lớp 12 only. Decide whether the sample should show more or none.
3. Phần III Hiểu: the 2025 paper and the sample have no Phần III below Vận dụng; here 2 of 6 are Hiểu. Keep?
4. Phần II ý a is always Biết; Phần II câu 1 has its ý d on Bài 4 (different bài from ý a–b). Is mixing bài inside one situation what you want the model to learn?
5. Năng lực codes TD / GQ / MHH only (GT, CC not used).

## Not proven
Nothing was generated from the sample (M3 measures that). The docx was checked by the app's reader and a LibreOffice render, not opened in Word. The 2025 transcripts were typed by subagents and only partly re-read, so the level evidence itself is soft.

## Skeleton check (26 Oct, owner rule: the registered skeleton is the authority)
The sample is slot-addressed: `matrix.json` has a `slots` list (part, position, key, level, topic, requirement per slot) and the rows are derived from it. `check.py` compares it with the slot list read from the registered layout: same slots, same order, none extra, none missing. No block layout is registered for this subject (`blocks_for` returns nothing), so there is no block order to check; none was invented. `checks.txt` now has 27 checks (all pass).
