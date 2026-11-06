# GAPS (groupA)

## Global

- No school or province plan (phân phối chương trình) was found for any subject-grade. Every plan used is a third-party sample or template on hoatieu.vn, several gated or truncated. The provenance value "school_plan" was therefore never used; every row keeps "assumed".
- The publisher's own pages (nxbgd.vn, hanhtrangso.nxbgd.vn) did not expose any KNTT mục lục or PPCT. All contents are from loigiaihay.com (third-party mirror).
- Tập (volume) split: sourced only for Toán 10, 11, and 12 (volume labels on loigiaihay, and the Toán plan). For Vật lí 10, 11, Hóa 10, 11, 12, Sinh 10, 11, 12 no source gave the Tập split. Rows there carry book.volume = null and typical_phase.semester = null (or a semester taken from a sample plan where the plan states HK, see per-file notes). band = null everywhere in those files.
- Outcomes (yêu cầu cần đạt) not transcribed: outcomes_vi = null everywhere. GDPT 2018 chủ đề tables were read only for Toán (Lớp 10 and part of Lớp 11). Lớp 12 Toán, and all Lý, Hóa, Sinh GDPT tables, were not reached.
- Extra fields added to every row beyond the spec: periods (int, from plan), plan_weeks (string, from plan), test_point (string, from plan). They are null when the source does not state them. keywords_vi and prerequisites are empty arrays.
- Vật lí 12: no source reached for any volume. The file vat-li-12.jsonl is empty (0 rows). Tried loigiaihay search and one guessed SGK URL (c1733), which was the wrong book.

## Per subject-grade

### Toán 10 (toan-10.jsonl, 50 rows)
- Tập 1 and Tập 2 sourced (contents + sample plan). Periods, weeks and tests from the sample plan 128699, cross-checked with 236253.
- Plan Tập 1 sums to 55 tiết (includes "giữa kì I" 3 tiết) while the plan states 54; not reconciled.
- HĐTN Tập 2 rows (toan-10-hd-t2-1, toan-10-hd-t2-2) have titles from the plan only; no contents title was read.
- Lớp 10 chủ đề read from GDPT copy (hoatieu). Outcomes not transcribed.

### Toán 11 (toan-11.jsonl, 53 rows)
- Tập 1 and Tập 2 titles from loigiaihay (complete list read).
- Plan (128699) gives tests but no per-bài tiết, so periods are null except bài tập cuối năm (4).
- Conflict: the plan puts "Hoạt động thực hành trải nghiệm" in Tập 1 (before cuối kì I), but the loigiaihay list puts it in Tập 2. The row toan-11-hd is kept in Tập 2 (loigiaihay); verify.
- GDPT Lớp 11 chủ đề read only partly (Chương 9 Đạo hàm and the xác suất strands not reached).

### Toán 12 (toan-12.jsonl, 30 rows)
- Tập 1 chương I–III and Tập 2 chương IV–V titles from loigiaihay.
- Chương VI (Xác suất có điều kiện): only the chapter title is sourced (2048.vn topic index). Bài 18, bài 19 and bài tập cuối chương VI have NO row because no fetched page showed their titles. The search snippet's titles were not verified and are not used.
- HĐTN rows: no periods in the plan.
- GDPT Lớp 12 not read.

### Vật lí 10 (vat-li-10.jsonl, 41 rows)
- Titles from loigiaihay (chương I–VII, bài 1–34). No plan found. Volume unknown (book.volume = null). Chương VII title is completed from bài 34 because the source is cut.
- Anomaly: the loigiaihay page header reads "GIẢI SGK VẬT LÍ 11" over the list; the lesson labels are Vật lí 10. Lesson names match Lớp 10. Verify.
- No periods, weeks or tests.

### Vật lí 11 (vat-li-11.jsonl, 30 rows)
- Chương I–IV only (bài 1–26) from loigiaihay. Chương V and later NOT sourced: no rows.
- Plan (220221) periods matched to bài by number (Chương I–II) and by title (Chương III–IV). Numbering differs: plan Chương III–IV use bài 16–29 with 23 and 24 absent; loigiaihay uses 16–26. Plan lists "Điện trường của hệ điện tích" (2 tiết) that loigiaihay does not; it has no row. Plan total stated 70, sum 62.
- Plan "Kiểm tra, đánh giá: 7 tiết" has no position; not placed.
- Volume unknown.

### Hóa học 10 (hoa-hoc-10.jsonl, 30 rows)
- Titles from loigiaihay (chương 1–7, bài 1–23). Volume unknown.
- No main-book PPCT found. The only Hóa 10 hoatieu plan read (222467) is for the elective chuyên đề (fire/explosion), so it is NOT used.

### Hóa học 11 (hoa-hoc-11.jsonl, 22 rows)
- Only the sample plan 222700 exists (no contents page found). Rows: chương 1–3 (bài 1–14, HK1) and bài 15–19 (HK2, from Mẫu 2 only).
- Chương 4 title is not in any source (HK2 bài 15–18 rows have no chapter parent). Chương 5 title and bài 19 onwards not sourced; no further rows.
- Mẫu 1 and Mẫu 2 disagree: bài 12 is 2 tiết vs 3; bài 14 is 2 vs 1; end-of-HK1 review 3 vs 1. Periods taken from Mẫu 1 where it gives them.
- Mẫu 1 HK2 table and Mẫu 2 after bài 19 are not visible (truncated / gated).
- Test-point scope for giữa HK1 differs between the two Mẫu (Mẫu 1 scope to bài 7; Mẫu 2 no scope).
- Volume unknown; semester values are from the sample plan.

### Hóa học 12 (hoa-hoc-12.jsonl, 20 rows)
- Titles from loigiaihay: chương 1–4 (bài 1–14) and chương 5 bài 15. Bài 16 onward not sourced (page truncated).
- No PPCT found (the hoatieu Hóa 12 plan is gated). Volume unknown.

### Sinh học 10 (sinh-hoc-10.jsonl, 33 rows)
- Titles from loigiaihay (Mở đầu bài 1–3, chương 1–7, bài 4–26).
- Sample plan 226349 covers HK1 weeks 1–9 and tiết 18; bài 7 has no week; bài 8–11 weeks/tiết come from the sample's tổ chuyên môn sub-table; bài 12 and bài 13–26 have no plan data. Plan metadata mis-labelled "Môn: Ngữ Văn" (ignored for content).
- HK1 semester values are from the sample, not a school plan. Volume unknown.
- Test point (giữa HK1 week 8) is placed after bài 5 (plan weeks 6–7); the plan's title for tiết 13–14 is cut.

### Sinh học 11 (sinh-hoc-11.jsonl, 32 rows)
- Only the sample plan 220221 was read (no contents page). Chương 1–4 with tiết per bài. The WebFetch extractor's note says the periods were matched to lessons by table order; verify against the source table.
- "Kiểm tra, đánh giá: 7 tiết" has no position; not placed.
- Volume unknown.

### Sinh học 12 (sinh-hoc-12.jsonl, 43 rows)
- Titles from loigiaihay Phần 4, 5, 6 (chương 1–8, bài 1–35), complete.
- Sinh 12 Phần 1–3 (if any) were not reached.
- No PPCT found. Volume unknown.

## What the lead needs to verify first

1. Volume split for all eight subject-grades without a Tập label (see Global).
2. Vật lí 11 Chương V onwards, and Hóa 11 Chương 4–5 and bài 20+.
3. Hóa 12 bài 16 onwards and Toán 12 bài 18–19 and bài tập cuối chương VI.
4. The conflict on Toán 11 HĐTN placement, and the Vật lí 11 bài 16–26 vs plan numbering.
5. Whether the sample plans (hoatieu) should be trusted for periods and weeks at all; none is a school or province plan.
