# ASTRA THPT 2026 · Handoff cho UI/UX

Tài liệu này dành cho team UI/UX tiếp tục làm màn hình đề, xem đáp án và tải file
cho năm môn THPT. Backend đã tự xuất cặp JSON sau khi sinh đề thành công. Frontend
đã đọc được cấu trúc mới qua adapter hiện có.

## Bản giao

- Nhánh tích hợp `feat/phutrong-2208/thpt-contract-export`. Commit backend
  `1367ac1` và frontend `4e1001b`. Hai commit đang ở nhánh cục bộ tại thời điểm bàn giao.
- [JSON Schema](../../src/exam_baseline/resources/contracts/ASTRA_THPT_2026_Contract.json)
  định nghĩa student paper và phần `#/$defs/teacherKey`.
- Toán, Lý, V-ACT và job đã tạo trước tích hợp vẫn dùng payload legacy.
  Văn có schema và cần luồng sinh riêng.

| Môn | Gửi trong request | Nhận trong student paper | Số câu |
| --- | --- | --- | ---: |
| Tiếng Anh | `thpt-english` | `thpt_english_2026` | 40 |
| Lịch Sử | `thpt-history` | `thpt_history_2026` | 28 |
| Địa Lý | `thpt-geography` | `thpt_geography_2026` | 28 |
| Hóa Học | `thpt-chemistry` | `thpt_chemistry_2026` | 28 |
| Sinh Học | `thpt-biology` | `thpt_biology_2026` | 28 |

## Luồng UI và API

| Bước | API | Cách dùng |
| --- | --- | --- |
| Chọn mẫu | `GET /api/exam-formats` | Lấy `id`, `version`, tên môn, số câu và thời lượng từ danh mục. |
| Sinh đề | `POST /api/exams/generate` | Gửi `Idempotency-Key` riêng cho mỗi lần xác nhận. Dùng lại cùng key nếu retry chính lần xác nhận đó. API trả `jobId`. |
| Theo dõi | `GET /api/exams/{jobId}/events` hoặc `/status` | Dùng `status`, `stageName`, `completedItems` và `totalItems`. Khi `failed`, thoát trạng thái đang sinh và hiển thị lỗi. |
| Đọc đề | `GET /api/exams/{jobId}` sau `completed` | Ưu tiên `studentPaper` cho nội dung đề. `questions` hiện cung cấp dữ liệu cho màn hình giáo viên và job legacy. |
| Tải hình | `GET /api/exams/{jobId}/assets/{assetId}` | Ghép `figure.assetId` với `studentPaper.assets[].id`. Các hình sinh từ luồng hiện tại có MIME `image/png`. |
| Preview | `POST /api/exams/{jobId}/preview` | Gửi revision và hash, chờ `ready` qua `statusUrl`, rồi mở `pdfUrl` do backend trả. |
| Duyệt và tải | `POST /api/exams/{jobId}/approve`, rồi `GET /api/exams/{jobId}/export` | Gửi revision, hash và `reviewer` khi duyệt. Tải đề với `type=STUDENT_EXAM&format=json`, tải đáp án với `type=TEACHER_KEY&format=json`. Dùng tên file từ `Content-Disposition`. |

Ví dụ body cho preset Hóa.

```json
{
  "formatId": "thpt-chemistry",
  "formatVersion": "1",
  "subject": "Hóa Học",
  "grade": 12,
  "examType": "THPT_STANDARD",
  "durationMinutes": 50,
  "itemCount": 28,
  "prompt": "Tạo đề luyện tập Hóa học lớp 12.",
  "uploadedFiles": []
}
```

## Tệp và phiên bản

- Backend ghi `student-paper.json`, `teacher-key.json` và `assets/` nếu có hình
  dưới `EXAM_UI_OUTPUT_ROOT/<jobId>/`, mặc định là `runs/ui/<jobId>/`.
- Hai file dùng cùng `(examId, revision, contentHash)`. Trong contract, `examId`
  có dạng `exam-<jobId>`. URL API dùng `jobId` nguyên gốc. Ghép câu theo
  `studentPaper.sections[].items[].id` và `teacherKey.entries[].questionId`.
- `contentHash` do server cấp. Khi lưu hoặc tạo lại câu, lấy revision và hash
  mới trước khi hiện preview hoặc duyệt lại. Với `stale_revision` hoặc
  `stale_hash`, tải lại đề.
- File học sinh chỉ chứa nội dung đề. Giữ `teacher-key.json` và package legacy
  có đáp án trong luồng giáo viên. Màn hình chia sẻ cho học sinh cần dùng bản
  đề đã duyệt và cơ chế phân quyền riêng phía backend.

Trích hai file cùng phiên bản. Các trường còn lại lấy từ schema.

| File | Trường định danh | Dữ liệu câu 1 |
| --- | --- | --- |
| `student-paper.json` | `schemaVersion: astra-thpt-paper-v1`, `examId: exam-<jobId>`, `revision: 1`, `contentHash: <hash của đề>` | `sections[0].items[0]` có `id: p1-1`, `type: mcq`, `stem` và `choices`. |
| `teacher-key.json` | `schemaVersion: astra-thpt-teacher-key-v1`, cùng `examId`, `revision` và `contentHash` | `entries[0]` có `questionId: p1-1`, `type: mcq`, `answer: A` và `explanation`. |

## Việc UI/UX làm tiếp

1. **Render theo block và run.** Adapter hiện chuyển nhiều run thành chuỗi để
   dùng lại UI. Khi nâng renderer, giữ định dạng đậm, nghiêng, gạch chân, xuống
   dòng và chỉ số hóa học. Bổ sung ca bảng gộp ô, marker và chú thích nếu UI nhận
   các block đó. Duyệt `sections[].items` theo thứ tự và dùng `number` để hiển thị.
2. **Rà hiển thị ngữ liệu và phần trả lời ngắn.** Mỗi ngữ liệu hiện một lần
   trước nhóm câu. Đề Anh có sáu nhóm theo thứ tự sắp xếp 1–5, điền khuyết
   6–10, đọc 11–20, đọc 21–28, điền khuyết 29–34 và 35–40. Giữ chỗ trống đánh
   số và hỗ trợ `stem: []`. Phần trả lời ngắn điền vào phiếu riêng. Giữ đáp
   án dạng chuỗi như `023` khi contract khai báo `digit_sequence`. Engine
   hiện tại xuất câu trả lời ngắn live ở dạng `numeric`.
3. **Hoàn thiện thao tác tải.** Thêm nút tải đề JSON cho job có `studentPaper`
   và đã duyệt. Nút tải đáp án hiện dùng endpoint export. Sau khi sửa câu, ẩn
   trạng thái duyệt cũ và yêu cầu mở bản PDF của revision mới.
4. **Hiển thị tiến độ và lỗi.** Dùng trạng thái từ API. Kiểm các ca
   `provider_timeout`, `provider_unavailable`, `invalid_contract` và
   `thpt_contract_export_failed`. Giữ nguyên bản nháp ở các phiên khác.

## Kiểm thử và vị trí code

Đã chạy Edge với provider replay trên cả năm môn để kiểm câu hỏi, ô trống đề
Anh, ảnh PNG trong đề Hóa và đọc đáp án sau khi duyệt. Bộ test frontend có 21
ca qua. Lượt kiểm này dùng dữ liệu replay.

```powershell
.\.venv-win\Scripts\python.exe -m pytest -q tests/api/test_ui_subjects.py
npm.cmd --prefix astra-frontend test
```

- Backend [trình xuất JSON](../../src/exam_baseline/thpt/contract_artifacts.py),
  [job và export](../../src/exam_baseline/ui/jobs.py), [route API](../../src/exam_baseline/api/routes_ui.py).
- Frontend [adapter](../../astra-frontend/src/services/contractPaper.ts),
  [API client](../../astra-frontend/src/services/examService.ts),
  [QuestionCard](../../astra-frontend/src/components/Workspace/LiveCanvas/QuestionCard.tsx).
- [Cách chạy ASTRA](../../README.md) và [quy trình preview PDF](FRONTEND_PDF_PREVIEW_HANDOFF.md).
