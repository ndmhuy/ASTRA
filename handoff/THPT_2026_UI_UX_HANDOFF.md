# ASTRA THPT 2026 · Handoff cho team UI/UX

Tài liệu này hướng dẫn dựng giao diện đề học sinh, màn hình giáo viên và xem trước PDF theo contract ASTRA THPT 2026. Fixture Tiếng Anh đã được tạo và xác thực. Phần nối API cho contract mới cần được triển khai cùng backend.

## Tệp bàn giao

| Tệp | Dùng để làm gì |
| --- | --- |
| ASTRA_THPT_2026_Contract.json | Schema gốc của đề học sinh. Các schema request, đáp án và preview nằm trong phần `$defs`. |
| student-paper.json | Đề Tiếng Anh lớp 12 tự soạn, 40 câu, 50 phút, thang điểm 10. Dùng trực tiếp cho HTML, mock API và kiểm thử. |
| teacher-key.json | 40 đáp án và giải thích của đề mẫu. Chỉ dùng trong luồng giáo viên. |

Hai JSON mẫu nằm trong `runs/thpt-2026-contract/` của workspace tạo đề. Khi gửi handoff, gửi kèm schema và hai JSON mẫu. Giữ file đáp án trong fixture giáo viên hoặc môi trường kiểm thử có quyền phù hợp.

## Tích hợp với ASTRA

| Điểm nối | Yêu cầu |
| --- | --- |
| Chọn mẫu | Lấy `formatId`, `formatVersion`, số câu và thời lượng từ danh mục API. Chỉ hiển thị mẫu mới khi backend khai báo hỗ trợ. |
| Tạo đề | Mục tiêu là tiếp tục dùng `POST /api/exams/generate` cùng `Idempotency-Key`. Backend nhận request phiên bản mới, ánh xạ sang engine, suy ra số câu và thời lượng theo profile, rồi trả `jobId`. |
| Theo dõi | Giữ các route `GET /api/exams/{jobId}/status` và `/events`. Khi job hoàn tất, lấy package qua `GET /api/exams/{jobId}`. |
| Hiển thị | Khi backend trả `ExamPackage.studentPaper`, dùng schema gốc cho đề học sinh. Luồng legacy tiếp tục dùng package hiện tại. Với fixture, lấy đối tượng ở gốc của `student-paper.json`. |
| Đáp án | Nhận `teacher-key.json` qua luồng được phân quyền giáo viên. Ghép với đề bằng bộ ba `examId`, `revision`, `contentHash`, sau đó ghép từng câu bằng `questionId`. |
| Xem trước và duyệt | Gửi binding hiện tại để yêu cầu preview. Khi `status=ready`, kiểm tra revision/hash rồi hiển thị `pdfUrl`. Đổi phiên bản phải vô hiệu hóa preview và phê duyệt trước. |

Backend hiện dùng các mã như `thpt-english` và request legacy có `subject`, `durationMinutes`, `itemCount`. Mã `thpt_english_2026`, phép ánh xạ request mới, trường `studentPaper` và route key có phân quyền thuộc phần tích hợp cần làm. `jobId` là định danh của job trong URL hiện tại. `examId` là định danh đề do backend cấp cho payload.

Ví dụ dưới đây dùng schema `#/$defs/generationRequest`.

```json
{
  "schemaVersion": "astra-thpt-generate-v1",
  "examType": "THPT_STANDARD",
  "formatId": "thpt_english_2026",
  "formatVersion": "1",
  "grade": 12,
  "prompt": "Tạo đề luyện Tiếng Anh lớp 12 có các bài đọc tự soạn."
}
```

## Các quy tắc cần giữ khi dựng giao diện

- Duyệt `sections[].items` theo thứ tự mảng. Hiển thị `number` theo từng phần, lưu selection theo `id`. Giữ nguyên số 0 đầu của `examCode` và đáp án `digit_sequence`.
- In một nhóm theo đúng `sectionId` và `questionRange`. Với Tiếng Anh, thứ tự là sắp xếp 1–5, điền khuyết 6–10, đọc 11–20, đọc 21–28, điền khuyết 29–34 và 35–40. Một nhóm sắp xếp có thể có `blocks: []`, mỗi câu khi đó có các mẩu riêng trong `stem`.
- Với câu điền khuyết có `stem: []`, vẫn hiển thị số câu và bốn lựa chọn. Render `blank.label` ngay trong đoạn đọc. Giữ gạch chân, xuống dòng, marker I–IV và vị trí chú thích.
- Render rich text theo `type`. Hiển thị `text` dưới dạng text node, dùng renderer đã giới hạn lệnh cho `math` và `chem`, lấy ảnh từ manifest `assets`. Hình, bảng gộp ô, footnote và rubric là các ca contract cần fixture riêng.
- Mỗi câu đúng/sai giữ bốn ý a–d. Câu số hiển thị đơn vị và quy tắc làm tròn, còn chuỗi chữ số được render như văn bản. Trạng thái `FLAGGED` và lý do kiểm lại chỉ hiện trong trải nghiệm giáo viên. Mẫu đã soát đáp án bằng tay và giữ `PENDING` vì chưa chạy Solver.
- Khi tính `contentHash`, backend chuẩn hóa toàn bộ student paper đã bỏ trường `contentHash` theo RFC 8785 rồi tính SHA-256. Giao diện dùng hash từ server để kiểm binding. Sửa đề hoặc đáp án làm tăng revision, nên hash đổi kể cả khi nội dung in giữ nguyên. [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785)

## Kiểm thử trước khi bật tính năng

1. Nạp fixture vào màn hình đề. Phải thấy đủ 40 câu và 6 nhóm, đúng thứ tự. Các nhóm điền khuyết in một lần và đủ số blank. Mục đọc đầu có 4 marker và từ gạch chân.
2. Mở dữ liệu student và đoạn trao đổi mạng của vai trò học sinh. Chỉ student paper được tải. Key và lời giải chỉ xuất hiện sau khi lấy dữ liệu bằng quyền giáo viên.
3. Với dữ liệu giáo viên, kiểm thử cùng hash nhưng sai revision và cùng revision nhưng sai hash. Hai ca đều phải từ chối ghép key và thay preview cũ.
4. Trong hồ sơ tích hợp đầy đủ, thử table có ô gộp, asset thiếu, key lệch loại, câu trả lời chuỗi có số 0 đầu, và rubric tự luận có nhiều mức điểm.
5. Thử chatbot với câu “Tạo đề luyện Tiếng Anh 12 theo mẫu THPT 2026”. Xác nhận đúng `formatId`, 40 câu và 50 phút. Khi bấm tạo, chỉ phát một request cho cùng lần xác nhận.

## Phạm vi của mẫu lần này

Đã xác thực student paper và teacher key bằng JSON Schema Draft 2020-12. Kiểm tra bổ sung gồm số thứ tự, tham chiếu nhóm/nguồn, blank, số mục đáp án, thang điểm và hash. Đề và ngữ liệu do ASTRA tự soạn, dùng cấu trúc mẫu 1116 làm tham chiếu bố cục. Việc cân chỉnh độ khó theo đề thi thật và kiểm thử renderer PDF của contract mới là các bước tiếp theo. [Mẫu tham chiếu 1116](https://xaydungchinhsach.chinhphu.vn/thi-tot-nghiep-thpt-2026-de-thi-tieng-anh-va-goi-y-dap-an-119260612132828853.htm)

Contract liệt kê Văn, Anh, Sử, Địa, Hóa và Sinh. Vật lí có mẫu legacy riêng trong ASTRA. Việc hỗ trợ Văn trong app cần được chốt trước khi bật mẫu này trong UI. Fixture bàn giao ở đây là một đề Tiếng Anh đầy đủ.

Các vị trí code để team bắt đầu gồm `src/exam_baseline/ui/contracts.py`, `src/exam_baseline/api/routes_ui.py`, `astra-frontend/src/types/exam.ts`, `astra-frontend/src/services/examService.ts` và `astra-frontend/src/components/Workspace/LiveCanvas/ExamPaperView.tsx`.
