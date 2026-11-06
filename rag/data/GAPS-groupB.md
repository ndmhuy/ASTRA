# GAPS (groupB, KNTT grades 10-12, draft)

## Source-level gaps (apply to every subject)

1. No official KNTT mục lục (contents page) was reached for any subject, volume or grade. nxbgd.vn product pages show no KNTT grade 10-12 book page. hanhtrangso.nxbgd.vn gave only a title. taphuan.nxbgd.vn failed with a TLS certificate error.
2. No official phân phối chương trình (PPCT) was reached, from the publisher, the Bộ, or a Sở/school. The school-plan PDFs that search returned (thptlytutrong.ninhbinh.edu.vn, thpt-hoangvanthu.ninhbinh.edu.vn) returned HTTP 404.
3. The Thông tư 32/2018 programme text (with the subject appendices) was not read. thuvienphapluat.vn returned 403, and search snippets did not include the Ngữ văn, Tiếng Anh or GDKT&PL appendices. Consequence: `outcomes_vi` is null on every row, as the rules require.
4. All rows come from hoatieu.vn sample plans, which are third-party uploads. Most are paywalled, so only preview tables were read. Uploaders are individuals; none is confirmed as author. They are not school or province plans, so `typical_phase.provenance` stays "assumed" everywhere (no row qualifies as "school_plan"). Lead should check the school-year and dating claims on each page.
5. Many plans are out of date for 2026-2027 (dated 2023-2025; some headers say "năm học 2024-2025" or "2023-2024"). Week and period numbers may not match the year being planned.

## Subject-grade gaps

| Subject | Grade | Volume | What is missing and why |
|---|---|---|---|
| Ngữ văn | 10 | Tập 1 & 2 | File exists (ngv-10.jsonl). Titles, tiết, tuần come from one tổ chuyên môn sample. Chuyên đề not applicable (no chuyên đề in source). |
| Ngữ văn | 11 | Tập 1 & 2 | Chuyên đề 1-3 rows have no titles (the source gives only tiết counts). No weeks anywhere. Test blocks have no placement. |
| Ngữ văn | 12 | Tập 1 & 2 | No weeks. Chuyên đề (if any) not in the source. |
| Tiếng Anh | 10 | Tập 1 & 2 | Unit 1-8 names come from loigiaihay (English, third-party index). Unit 9 and 10 names not read. Plan header inconsistent (Global Success vs Kết nối tri thức in the URL). |
| Tiếng Anh | 11 | Tập 1 & 2 | No unit names in the readable preview; Unit 1-10 rows are titled "(tên chưa xác minh)". Reviews listed. |
| Tiếng Anh | 12 | Tập 1 & 2 | NO FILE. No plan and no unit list was found in any readable source. Search results only gave generic PPCT templates and the Global Success exercise sites. |
| Lịch sử | 10 | Tập 1 & 2 | Chuyên đề not visible (in the downloadable file). Bài 3 and bài 9 listed as "không dạy" in the plan; kept with periods 0. Bài 8 split across semesters. |
| Lịch sử | 11 | Volume unknown | No weeks, no semester, no test placement. Ôn tập/kiểm tra (5) and thực hành (10) kept as unplaced rows. Page says 52 tiết; its lines add to 51. |
| Lịch sử | 12 | Volume unknown | No weeks, no semester, no test placement. Đánh giá định kì (5) and thực hành (10) kept unplaced. |
| Địa lí | 10 | Tập 1 & 2 | Internal mismatches: bài 13 tiết printed as 16 vs 26; bài 4 tiết 4 vs 5 across tables; giữa kì 1 tiết 16 (Phụ lục 1) vs 18 (PPCT); bài 19 weeks 19/21/20/21. Bài 27 is missing from the source numbering; the unnumbered thực hành row was kept. |
| Địa lí | 11 | Tập 1 & 2 | Source period note "2 (3)*" for bài 7 is unclear; recorded as 2. Chuyên đề rows have no title beyond the source's wording. Năm học 2023-2024. |
| Địa lí | 12 | Tập 1 (bài 1-9 / partly) & Tập 2 (bài 10-22); bài 23-35 unknown | Semester I/II for bài 1-22 come only from the "team plan" column on the same page; bài 23-35 have no semester. Tests not placed. PPCT and team-plan tiết counts disagree for several bài (kept PPCT). |
| GDKT&PL | 10 | Tập 1 & 2 | Bài 6-23 titles are English in the reader's summary, translated here (bài 10 and bài 20 need checking; bài 20 title not in the source). Plan semester-1 tiết add to 33 vs 36 stated. |
| GDKT&PL | 11 | Volume unknown | ONLY the chuyên đề table was readable (3 chuyên đề, 8 bài). The main bài (chính khoá) list is NOT in any readable source, so the file is incomplete. |
| GDKT&PL | 12 | Volume unknown | 16 bài with tiết; no weeks, no semester, no tests placed. Chuyên đề 10/10/15 tiết have no titles (not in the preview). Plan total 69 vs 70 stated. |

## Notes for lead

- Field additions beyond the base schema: `periods`, `plan_weeks`, `test_point`, `plan_note`, `source_type`. Kinds used beyond the base list: "chủ đề", "phần", "thực hành", "ôn tập kiểm tra", "unit", "review".
- `typical_phase.band` is computed by position within each volume among lesson-type rows (chủ đề/phần excluded). Rows with unknown volume have band null.
- Ngữ văn 10 gives two different test weeks for giữa kì 1 (wk 10 vs wk 11); the row records both.
