# OCR đề tỉnh: kế hoạch và bản bàn giao (2026-10-29)

Người nhận: phiên điều phối OCR (một phiên Claude, các worker cỡ Haiku 5.5; OCR chạy trên Antigravity như OCR-1 đến OCR-3). Chủ app duyệt phạm vi ngày 2026-10-29: mở rộng phiên âm lên các đề tỉnh, để các agent tự tìm nguồn, mục đích là tìm quy luật nội dung hay ra cho ma trận.

Phiên này mới viết kế hoạch. Chưa tìm nguồn, chưa tải file nào, chưa chạy OCR.

## 1. Vì sao cần

Ma trận mẫu Toán (`docs/release/next/matrix-samples-v3/toan/matrix-thuc-toan.md`) và luật viết ma trận (`docs/release/next/matrix-writing-rules.md`) chọn nội dung "hay ra" từ chỉ 7 đề: mã 0101 và 6 đề sở có nguồn chưa xác minh. Với 7 đề, một dạng gặp "3/7" hay "5/7" chưa đủ để kết luận. Mục tiêu: đếm trên vài chục đề thật để (a) xác định dạng kinh điển của từng phần, (b) kiểm lại tỉ lệ lớp 10 và 11, (c) có nhãn mức độ ước lượng cho từng dạng.

## 2. Tình hình hiện tại (đã kiểm tra, không suy diễn)

- **Corpus riêng tư:** `/Users/huynguyen/Lecturing_Lab/exam-corpus` (đọc README của nó trước). Nhánh `ocr-1-20261027` đang được checkout ngay trong bản chính của clone này, dù quy tắc OCR là không đổi nhánh của clone chính. Đừng sửa thêm gì ở đó.
- **OCR-1** (10 đề tham khảo 2025) và **OCR-2** (35 file đáp án 2025 và 2026) đã commit đủ. Lệch cần biết: khóa Tin học 2025 và 2026 có 6 câu Đúng/Sai ở Phần II, khung đăng ký ghi 4.
- **OCR-3** (đề ảnh chụp) **đang chạy**: worktree `/Users/huynguyen/Lecturing_Lab/scratch/wt-ocr-3`, nhánh `ocr-3-20261027`, đã có 6 commit (Vật lí 2026, GDKT&PL 2025, Sử 2025, Sinh 2025, Toán 2026, Ngữ văn 2026). Chưa audit.
- **Đề tỉnh hiện có:** `exam-corpus/provincial-toan-unverified/` có 6 đề (Bắc Ninh, Đà Nẵng, Hà Tĩnh, Hải Phòng lần 1, Hải Phòng lần 2, Phú Thọ), là sản phẩm của chính app, nguồn chưa xác minh, không phải bằng chứng chính thức. Việc đầu tiên là xác minh hay loại chúng bằng cách tìm bản gốc của từng đề.
- **Ổ đĩa:** còn khoảng 2,8 GB trống. Prompt OCR quy định dưới 3 GB thì không được mở thêm subagent. **Dọn chỗ hoặc chờ OCR-3 xong trước khi bắt đầu** (xem mục 7).

## 3. Phạm vi và thứ tự

| Giai đoạn | Môn | Số đề mục tiêu | Ghi chú |
|---|---|---|---|
| P-1 | Toán | 30 đến 40 đề tỉnh năm học 2025–2026 (thi thử tốt nghiệp, lần 1 và lần 2) | cần nhất cho ma trận; ưu tiên đề có đáp án |
| P-2 | GDKT&PL | 10 | ma trận Sa Đéc của chủ app là môn thứ hai |
| P-3 | Vật lí, Hóa học | 10 mỗi môn | cùng cấu trúc 18/4/6 |
| P-4 | Sinh, Sử, Địa, Tin học | 10 mỗi môn | |
| P-5 | Tiếng Anh, Ngữ văn, ngoại ngữ khác | tùy | ma trận các môn này cần luật riêng, xem `matrix-writing-rules.md` phần "Chưa chứng minh" |

Mỗi giai đoạn dừng ở cổng duyệt của chủ app (mục 8). Chỉ sang giai đoạn sau khi chủ app đọc báo cáo của giai đoạn trước.

## 4. Các bước và vai trò

```
SRC (tìm nguồn, KHÔNG tải)  ->  [chủ app duyệt danh sách]  ->  DL (tải, băm, kiểm text layer)
   ->  OCR (đề không có text layer) hoặc EXTRACT (đề có text layer)  ->  VERIFY (đọc lần hai)
   ->  TAG (gắn từng câu vào chủ đề và bài, đếm tần suất)  ->  báo cáo -> cập nhật mẫu ma trận
```

- **SRC:** worker có công cụ tìm web (Claude in Chrome hoặc subagent có WebSearch). Mỗi dòng của danh sách: tỉnh hoặc trường, tên đề, năm học, lần thi, URL, loại máy chủ (trang của sở, trang tài liệu, mạng xã hội), có đáp án không, có vẻ có text layer không (đuôi file, kích thước), ghi chú bản quyền. Không tải gì. Tối đa 20 phút một vòng, rồi giao danh sách.
- **DL:** chỉ sau khi chủ app duyệt danh sách. Mỗi file: thư mục riêng ngoài repo, ghi `source.json` (URL, ngày tải, SHA-256, kích thước), kiểm `pdftotext` xem có text layer. Một đề có nhiều bản sao: giữ một, ghi các URL còn lại.
- **EXTRACT:** đề có text layer đi qua `pdftotext -layout`, rồi worker chuyển công thức thành LaTeX trong `$...$` và dựng `de.md`. Không OCR vì tốn và dễ sai.
- **OCR:** đề scan. Dùng Antigravity như OCR-1, hai lượt, lượt hai là model khác, đọc lại hai trang nhiều công thức nhất.
- **VERIFY:** orchestrator tự kiểm, không tin báo cáo của worker: số câu mỗi phần bằng khung Toán (12 + 4 + 6) hoặc khung của môn, mở hai trang ảnh so 5 câu, đối chiếu mã đề trong chân trang.
- **TAG:** worker gắn mỗi câu vào (chủ đề, bài, lớp) theo bản đồ chương trình, kèm mức độ ước lượng. Dùng bộ gắn nhãn mức độ có sẵn của app để so (kết quả đo trước đó: Toán 2026, 33 trên 34 câu giữ nguyên mức qua 3 lần). Đầu ra là bảng `topic-tags.json` cho từng đề và một bảng tần suất cho cả đợt.

## 5. Bố cục dữ liệu

Trong worktree riêng của corpus, nhánh riêng:

```
transcriptions/<môn>/<năm>-provincial/<tỉnh>-<lần>/
  de.md            đề theo thứ tự đọc (quy ước giống OCR-1)
  key.json         chỉ khi file đề có đáp án
  structure.json   {"subject","province","exam","round","pages","parts":[...],"total_cau","unreadable_count"}
  source.json      URL, loại máy chủ, SHA-256, ngày tải, tên file gốc, bản sao khác
  STATUS.md        một dòng: phiên âm bởi model nào, ngày, trang, câu không đọc được, lượt hai có hay không,
                   "Đề của sở/trường, bản sao từ máy chủ bên thứ ba; chỉ dùng làm bằng chứng nội bộ"
  topic-tags.json  mỗi câu: số câu, chủ đề, bài, lớp, mức ước lượng, độ chắc
analysis/provincial-<môn>-<ngày>.md   bảng tần suất cả đợt
```

Giữ nguyên quy tắc đã có: đề thật chỉ là bằng chứng nội bộ, kho riêng tư, không đưa vào sản phẩm, không sao chép câu hỏi sang ma trận hay sang đề sinh ra.

## 6. Tiêu chí nghiệm thu

- Mỗi đề có đủ file ở mục 5, `structure.json` đọc được, SHA-256 đã vào `SHA256SUMS.txt`.
- Số câu mỗi phần bằng khung đã đăng ký (đọc bằng `layout_for` trong `/Users/huynguyen/Lecturing_Source/Grading_Tools/exam_formats/thptqg_2026.py`, không sửa app). Lệch thì báo, không sửa.
- Năm câu so với ảnh trang khớp (orchestrator tự làm).
- Không có đề trùng nội dung (kiểm SHA-256 và so 3 câu đầu).
- Đề sinh bởi app hoặc dựng lại (như sáu đề `provincial-toan-unverified`) phải được xác minh với bản gốc hoặc loại khỏi bảng đếm.
- Bảng tần suất ghi rõ N (số đề) và cách gắn nhãn là ước lượng.

## 7. Giới hạn vận hành

- Tối đa 2 subagent cùng lúc. Trước mỗi lần mở: `df -h /`; dưới 5 GB một subagent, dưới 3 GB không mở. Hiện đang dưới 3 GB.
- Render ảnh vào `~/Lecturing_Lab/scratch/ocr-4/` ngoài repo, ở 150 dpi cho đề in, 200 dpi chỉ cho trang nhiều công thức. Xóa ảnh trung gian khi xong từng đề, chỉ xóa đường dẫn cụ thể đã liệt kê.
- Worktree riêng: `git -C /Users/huynguyen/Lecturing_Lab/exam-corpus worktree add -b ocr-4-<ngày> /Users/huynguyen/Lecturing_Lab/scratch/wt-ocr-4 <nhánh cơ sở mới nhất>`. Không đổi nhánh và không sửa bản chính của clone. Xung đột `SHA256SUMS.txt`: giữ cả hai phía rồi sắp xếp.
- Bỏ qua mọi thư mục có `DO_NOT_DELETE.txt`. Không xóa bằng ký tự đại diện dưới `/private/tmp` hoặc `~/Lecturing_Lab`.
- Commit sau mỗi đề; ít nhất mỗi 30 phút với việc chạy lâu.
- Không đẩy lên, không sửa repo app (`/Users/huynguyen/Lecturing_Source`), không chép gì vào đó.
- Không dùng Astra (tốn token). Worker cỡ Haiku 5.5 trước; Sonnet chỉ khi việc khó.

## 8. Cổng chủ app

1. **Danh sách nguồn (sau SRC):** chủ app duyệt trước khi tải. Việc tải file là hành động cần cho phép rõ ràng.
2. **Cuối mỗi giai đoạn:** chủ app đọc bảng tần suất và duyệt trước khi sang giai đoạn sau.
3. **Cập nhật mẫu ma trận** từ bảng tần suất: do orchestrator Claude đề xuất, chủ app duyệt.

## 9. Prompt cho từng bước (sao chép nguyên văn)

### SRC-1: tìm nguồn đề Toán tỉnh

```text
You are the ORCHESTRATOR of source-finding batch SRC-1 for Lecturing. Find where provincial and school mock exams for Toán (graduation exam, school year 2025-2026, 90 minutes, 12 + 4 + 6 format) are published, and list candidates. You DOWNLOAD NOTHING and you open no file bigger than a page; the owner approves the list first. Never touch /Users/huynguyen/Lecturing_Source or the corpus clone.

GOAL: a table of 40 to 60 candidate papers, one row each: province or school, exam name, school year, round (lần 1, lần 2, thi thử), URL of the file or page, host type (Sở GD&ĐT site, document library, school site, social media), answer key present (yes, no, unknown), likely text layer (born-digital pdf or docx vs scan or photo), rights note (as stated on the page), and a one-line reason you believe it is the genuine paper. Cover at least 20 different provinces. Prefer papers from a Sở GD&ĐT or a school over copies re-typed by a document site; if a paper exists on several hosts, list the best host first and the others in a notes column.

ALSO: the corpus already holds six provincial Toán files of unverified origin (Bắc Ninh, Đà Nẵng, Hà Tĩnh, Hải Phòng lần 1, Hải Phòng lần 2, Phú Thọ; folder provincial-toan-unverified, read-only). For each, try to find the original paper and say whether the corpus copy matches the first three questions.

Skip anything that asks for login, payment or a personal account. Do not use paid or leaked material. Every row needs a URL you actually opened.

OUTPUT: write `sources-toan.csv` and a short `SRC-1-REPORT.md` (counts by province, hosts used, rows you are unsure of, what you could not find) under the scratch folder `/Users/huynguyen/Lecturing_Lab/scratch/src-1/`. Nothing goes in a repo. STOP after the report and wait for the owner.

LIMITS: at most 2 subagents; no downloads; no account creation; report within 60 minutes or when blocked for 20.
```

### Cập nhật 2026-10-29: tách tải và OCR

Chủ app đã duyệt thứ tự P-1 đến P-5 và cho dùng Claude in Chrome để tìm và tải. Việc tải do phiên Claude in Chrome làm, ghi vào `/Users/huynguyen/Lecturing_Lab/scratch/dl-1/` (một thư mục mỗi đề: file gốc và `source.json`, cộng `manifest.csv`). Prompt OCR cho Antigravity nằm ở file riêng, đã thêm bước **trích hình** (cắt từng hình thành PNG, tên theo `cau_<n>.png`, `cau_p2_<n>.png`, `cau_p3_<n>.png`, dòng `[HÌNH: ...]` và dòng ảnh như OCR-1, kiểm từng ảnh): `docs/release/next/ocr-provincial/prompts/AG-OCR-4-provincial-toan.txt`. Phiên bản OCR-4 bên dưới là bản cũ, dùng file riêng này thay thế.

### DL-1 và OCR-4 (bản cũ, đã thay): sau khi chủ app duyệt danh sách

```text
You are the ORCHESTRATOR of batch OCR-4 for Lecturing (provincial Toán papers). Only run after the owner has approved `sources-toan.csv` in writing in chat; download only the approved rows. Never merge, never push, never touch /Users/huynguyen/Lecturing_Source.

WORKTREE: never change the branch or edit files of the main clone /Users/huynguyen/Lecturing_Lab/exam-corpus. Run `git -C /Users/huynguyen/Lecturing_Lab/exam-corpus worktree add -b ocr-4-<today> /Users/huynguyen/Lecturing_Lab/scratch/wt-ocr-4 <latest corpus base branch>` and work only there. Read the corpus README first.

PER APPROVED PAPER: (1) download into /Users/huynguyen/Lecturing_Lab/scratch/ocr-4/<province-round>/, record source.json (URL, date, SHA-256, size, original file name); (2) run `pdftotext -layout`; if it yields the questions, build de.md from it (math as LaTeX in $...$), otherwise render pages with `pdftoppm -r 150 -png` and have a worker transcribe by vision (câu numbers as printed, options A-D on their own lines, true/false a-d, tables as markdown, figures as `[HÌNH: one line]`, unreadable as `[?]`, never guess); (3) a DIFFERENT subagent re-reads the two pages with the most math, diffs against de.md, lists disagreements in STATUS.md and fixes de.md only where the image settles it; (4) write structure.json and key.json (only if the file has answers; decimal comma stays a comma); (5) commit `corpus: transcribe toan <province> <round> provincial`. Add SHA-256 of new files to SHA256SUMS.txt.

CHECKS you run yourself (reports are not evidence): files exist and parse; câu per part equals the registered Toán layout (12 + 4 + 6; read `/Users/huynguyen/Lecturing_Source/Grading_Tools/exam_formats/thptqg_2026.py`, `layout_for`, without editing it); open two page images and compare five câu with de.md; compare the first three câu with any other paper in the batch to catch duplicates; `git diff --stat` touches only that paper's folder and SHA256SUMS.txt. A mismatch is reported, not fixed.

LIMITS: at most 2 subagents at once; `df -h /` before each spawn (under 5 GB: one at a time; under 3 GB: spawn nothing and log it); delete only explicit scratch paths you listed; skip folders with DO_NOT_DELETE.txt; commit after each paper and at least every 30 minutes; no push; no secrets; no copying into the app repo.

REPORT per paper: commit, province, câu per part vs layout, unreadable count, second-pass disagreements, duplicate or reconstruction suspicion, anything for the owner.
```

### TAG-1: gắn chủ đề và đếm tần suất

```text
You are the ORCHESTRATOR of TAG-1 for Lecturing. Input: the finished OCR-4 folders (de.md per paper) in the corpus worktree. Output: topic-tags.json per paper and one frequency report. Read-only on everything else; no app edits.

PER PAPER: for each câu, one worker tags (a) chủ đề and bài from the Kết nối tri thức Toán 10, 11, 12 programme (the lesson list is the curriculum map `curriculum_map_data/toan-10.jsonl`, `toan-11.jsonl`, `toan-12.jsonl` in /Users/huynguyen/Lecturing_Lab/wt-ui-1028/Grading_Tools/exam_generator/), (b) grade, (c) an estimated level (Biết, Hiểu, Vận dụng) by the definitions in /Users/huynguyen/Lecturing_Source/docs/release/next/matrix-writing-rules.md section C, (d) confidence (high, medium, low) and a one-line reason. Tag Phần II per ý, not per câu. Never copy question text into the tags.

CHECKS: a second worker re-tags a random 20% of câu without seeing the first tags; report the agreement rate per field. Below 80% agreement on bài: stop and report.

REPORT: `analysis/provincial-toan-<date>.md` with: N papers; for every (chủ đề, bài): in how many papers it appears, average câu per paper, by part; share of lớp 10 and 11 content by part; the most common situation types in Phần II and Phần III; estimated level split overall and by part, labelled as estimates; what changed against the 7-paper counts in matrix-thuc-toan.md. No recommendation to change the matrix without evidence from at least 20 papers.
```

## 10. Rủi ro đã biết

- **Nguồn không đáng tin:** đề sở nhiều khi bị trang tài liệu gõ lại và có lỗi. Luôn ghi loại máy chủ và ưu tiên bản của sở hoặc trường.
- **Đề do app sinh nhầm là đề thật:** sáu đề `provincial-toan-unverified` là ví dụ. Mọi đề phải có URL gốc.
- **Mã đề và phiên bản:** một tỉnh có thể có nhiều mã đề; chỉ lấy một mã mỗi đề, ghi mã.
- **OCR công thức:** công thức sai làm lệch số liệu gắn nhãn; lượt hai bắt buộc.
- **Ổ đĩa:** xem mục 7.
- **Bản quyền:** đề do trang bên thứ ba chép; chỉ dùng nội bộ, như README của corpus nói.

## 11. Việc cần chủ app quyết

1. Duyệt thứ tự P-1 đến P-5, hay đổi (ví dụ GDKT&PL lên trước Toán)?
2. Mục tiêu 30 đến 40 đề Toán có đủ, hay cần nhiều hơn để tin con số?
3. Đề thi thử của trường (không phải của sở) có được tính không, hay chỉ lấy đề của sở?
4. OCR-3 đang chạy dùng cùng ổ đĩa: cho nó xong trước, hay dọn ổ để chạy song song?

## 12. Cập nhật 2026-10-29 (tối): các môn khác đã tải

- Toán: 75 đề (toanmath.com, pdf), trong `official/2026-provincial-toan/` của nhánh corpus `docs-matrix-rules-20261029`. Prompt: `prompts/AG-OCR-4-provincial-toan.txt`. Nhánh cơ sở của worktree OCR-4 là chính nhánh này.
- Chín môn khác: 114 đề Word (thuvienhoclieu.com), mỗi môn một thư mục `official/2026-provincial-<môn>/`: Vật lí 12, Hóa 14, Sinh 14, Sử 14, Địa 14, GDKT&PL 14, Tiếng Anh 14, Ngữ văn 14, Tin học 4 (trang nguồn chỉ có 4 đề Tin có thể lấy). Hai đề Vật lí lỗi 404 do tên file ghi sai, chưa tải lại. Prompt: `prompts/AG-OCR-5-provincial-other-subjects.txt`.
- **Công thức trong file Word là hình MathType**, không phải công thức Word: trích chữ từ docx sẽ mất công thức. Prompt OCR-5 bắt đổi docx sang pdf bằng LibreOffice (`/opt/homebrew/bin/soffice`) rồi OCR như pdf.
- Trang thuvienhoclieu.com đã chặn tạm (Cloudflare 1015) khi mình gọi song song quá nhanh. Sau đó chỉ gọi tuần tự, giãn cách 1,2 đến 2,5 giây, không vượt qua chặn. Tải thêm cần giữ nhịp này.
- Chưa làm: Văn, Anh, Tin chỉ có đề của sở và vài trường; chưa tìm ngoại ngữ khác (Nga, Nhật, Trung, Pháp, Đức, Hàn) và Công nghệ.
