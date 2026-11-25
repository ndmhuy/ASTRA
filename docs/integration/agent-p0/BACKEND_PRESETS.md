# P0 — Preset được Backend công nhận

**Preset registry/API: NOT_IMPLEMENTED.** Không có presetId, presetVersion, GET /presets
hay lookup/approval hash cho preset. Không trả một danh sách preset giả để Agent gợi ý.
Đường dẫn giả `/api/presets` không tồn tại (404), không có response `[]` được quy ước.

Có **format catalog** thật: `GET /api/exam-formats`, schemaVersion
`exam-format-catalog-v1`. [Response thực](BACKEND_FORMAT_CATALOG_ACTUAL.json),
source `src/exam_baseline/resources/exam_formats/thpt_math_v1.json` tại
`2acb95fbf6a55b7621c786248e10b10ca91a35ab`.

| Thuộc tính | Giá trị có thể gợi ý |
|---|---|
| Format ID/version | thpt-math / 1 |
| Tên | Toán THPT; subject wire = Toán Học, grade=12, examType=THPT_STANDARD |
| Cấu trúc | 90 phút; 12 MCQ, 4 đúng/sai, 6 ngắn; tổng22 câu/10 điểm |
| Editable | prompt, slots (đúng cấu trúc khóa) |
| Fixed | subject, grade, durationMinutes, itemCount, sections, template |
| Default matrix | `rag_workflow.matrix_retriever.default_toan_thpt_matrix()`; matrix_id = toan-thpt-2026-default-22q |
| Default rationale | Ma trận mẫu luyện tập từ code; cần giáo viên chấp thuận và RAG coverage |
| Official status | Khung được cố định theo template người dùng; không chứng minh ma trận chủ đề/mức độ là ma trận chính thức của cơ quan thi |

[Request mẫu hợp lệ](THPT_GENERATE_REQUEST_VALID.json) dùng default slots; không có presetId.
Đọc [evaluate response](THPT_EVALUATE_RESPONSE_ACTUAL.json) để lấy đúng default matrix
và hiển thị chủ đề/mức độ trước khi người dùng chấp thuận. `formatVersion=1` chưa
đóng dấu version riêng của default matrix; pin code SHA nếu cần tái lập cấu hình.

Khi giáo viên sửa prompt/slots, gọi evaluate lại **toàn bộ request** rồi trình bản mới.
Cross-field validation kiểm đủ ID, phần, mức enum; retrieval chỉ được kiểm trong job.
Không diễn giải `status=validated` thành "đã đủ tài liệu" hay "đã duyệt".

V-ACT: không có format catalog/preset HTTP. `examples/vact/request.json` là request mẫu
CLI 120 slots theo template, **không phải preset registry** và không được chuyển thành
THPT khi thiếu API. Nội dung luyện tập và phân bố mức độ không phải cam kết chính thức.

Owner preset registry/phiên bản ma trận: Backend + RAG; assignee/ETA UNDECIDED.
