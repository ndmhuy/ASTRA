# Hóa học (THPTQG) — sample matrix M0 — note for the owner (26 Oct 2026)

Files: `matrix.json`, `matrix.docx` (Phụ lục I + II, landscape), `matrix.md`, `checks.txt` (16/16), `build.py` (single source; shared builder `../m0lib.py`).

## What the sample is
28 câu, 40 scoring units of 0,25 = 10 điểm, 50 phút: Phần I 18 nhiều lựa chọn; Phần II 4 đúng/sai x 4 ý; Phần III 6 trả lời ngắn (0,25 mỗi câu). Levels (units): Biết 15 (37,5%), Hiểu 13 (32,5%), Vận dụng 12 (30%). Phần I 10/6/2, Phần II 5/5/6, Phần III 0/2/4. All eight chương of the Kết nối tri thức Hóa 12 (20 of the 22 non-review bài: Bài 18 cấu tạo tinh thể kim loại and Bài 27 kim loại chuyển tiếp are not asked) plus two lớp 10–11 foundation units (cân bằng hoá học, biến thiên enthalpy). Per unit: yêu cầu cần đạt, dạng, năng lực (NL.1–3), style hint; Phần II: the situation of each câu.

## Sources used (internal evidence only, nothing copied)
- Registered format (`exam_formats/thptqg_2026.py`): 18 + 4 + 6, marks, 50 minutes.
- Lesson list: the repo map `hoa-hoc-12.jsonl` covers only Bài 1–15 (20 rows, status draft); Bài 16–30 and the chương 5–8 names come from a web search result of 26 Oct (loigiaihay / hoatieu table-of-contents pages, third-party), not the book.
- Shape and level pattern: typed transcripts of the 2025 official Hóa 0301 and the Ministry 2025 sample, the session's level labels for them (official: Phần I 10/7/1, Phần II 4/10/2, Phần III 0/3/3; sample 11/7/0, 8/8/0, 0/4/2), and one school matrix + specification for Hóa 12 (HK2 2025–26). Used for SHAPE only; the official 2025 paper also mixes lớp 10–11 content (phenol, cân bằng, enthalpy, mass spectra), which is why two foundation units are here.

## What was invented
All cells and all 40 requirement sentences (none equal to the school spec's 138 lines; closest 53% similar), the four Phần II situations, câu numbering, style hints, the 37,5/32,5/30 split.

## Owner should check
1. Level split: 37,5/32,5/30 here; the Ministry sample table uses 40/30/30 for Hóa; the 2025 official paper by the session's labels is 14/20/6 units (much more Hiểu). Which should the sample teach?
2. Spelling of names: the sample writes chemical names as the Kết nối tri thức Hóa 12 headings do (ester, amine, carbohydrate, polymer, nitrogen). I did not check the Ministry paper's own spelling beyond the 2025 transcript; confirm the style you want in prompts.
3. The 2025 official paper puts about a third of its câu on lớp 10–11 (hữu cơ, cân bằng, nhiệt hoá học). This sample has 2 units; the app's default Hóa topics are lớp 12 only. More, fewer or none?
4. Bài 16–30 titles come from a web table of contents, not the book; confirm.
5. Phần II: câu 3 is the only electrochemistry câu and has two Vận dụng ý (c, d): fine as a teaching example?

## Not proven
Nothing generated from the sample yet (M3). Docx checked by the app's reader and a LibreOffice render, not opened in Word. The 2025 level evidence is the session's own labelling of subagent transcripts.

## Skeleton check (26 Oct, owner rule: the registered skeleton is the authority)
The sample is slot-addressed: `matrix.json` has a `slots` list (part, position, key, level, topic, requirement per slot) and the rows are derived from it. `check.py` compares it with the slot list read from the registered layout: same slots, same order, none extra, none missing. No block layout is registered for this subject (`blocks_for` returns nothing), so there is no block order to check; none was invented. `checks.txt` now has 27 checks (all pass).
