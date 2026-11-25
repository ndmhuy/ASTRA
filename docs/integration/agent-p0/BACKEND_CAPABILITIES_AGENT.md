# P0 — Backend ↔ Conversational Agent

Bản phản hồi handoff ngày 17/11/2026, đối chiếu **code đang triển khai**, không phải roadmap.
Runtime: `merge-mas-and-uiux@2acb95fbf6a55b7621c786248e10b10ca91a35ab`.
[Source](https://github.com/ndmhuy/ASTRA/tree/2acb95fbf6a55b7621c786248e10b10ca91a35ab),
[Branch bàn giao](https://github.com/ndmhuy/ASTRA/tree/merge-mas-and-uiux). Owner bàn giao Backend/MAS: Huy.

**Có thể tích hợp ngay:** Toán THPT, 22 câu, 90 phút; catalog → evaluate → generate
→ job status/SSE → lấy đề hoàn tất → sửa/tạo lại một câu → PDF preview → người dùng duyệt → export.
**BLOCKED:** `TeacherIntakeDraft` và adapter draft → `ExamMatrix`, preset registry,
V-ACT qua UI API, batch revision, upload, auth/quota và ràng buộc một job/workspace.
V-ACT có engine/CLI thật riêng; không ánh xạ `DGNL_DHQG` sang THPT.

## Đọc theo thứ tự

1. [Teacher input và mapping](TEACHER_INTAKE_THPT_VACT.md).
2. [Preset hiện có và giới hạn](BACKEND_PRESETS.md).
3. [Validation, lỗi và ví dụ](BACKEND_VALIDATION_AND_ERRORS.md).
4. [Runtime, commit và bằng chứng](BACKEND_RUNTIME_EVIDENCE.md).
5. [Hiện tại so với đề xuất; P1 và owner](BACKEND_CURRENT_VS_PROPOSED.md).

Machine-readable: [OpenAPI](BACKEND_AGENT_API_OPENAPI.json),
[capability descriptors](BACKEND_CAPABILITIES_AGENT.json),
[53 API examples](BACKEND_API_SAMPLES_ACTUAL.json), [schema/status draft](TEACHER_INTAKE_STATUS.json).
OpenAPI có schema input thật; nhiều response `/api` chưa khai báo Pydantic response model,
nên response schema còn `{}`. Các ví dụ runtime và `JobManager.package/status` bổ sung evidence;
không coi response là typed/versioned chỉ vì có file OpenAPI.

## Danh mục capability

`callableNow=true` nghĩa là có route để adapter gọi; generation vẫn cần provider/RAG/compiler
tùy action. Các ID trong descriptor là **nhãn tài liệu**, không có capability-dispatch endpoint.
Owner dưới đây là nhóm sở hữu; người nhận P1/ETA chưa được thống nhất.

| Chức năng / hành vi | Route/function | Status; callableNow | Owner / evidence tại runtime SHA |
|---|---|---|---|
| Đọc sức khỏe, provider đã cấu hình và compiler được tìm thấy | `GET /api/health` | IMPLEMENTED; true | Backend; `api/routes_ui.py:24` |
| Đọc format THPT hợp lệ, trường khóa/sửa, số câu/điểm | `GET /api/exam-formats` | PARTIAL (catalog, chưa teacher form); true | Backend; `ui/contracts.py:13` |
| Liệt kê preset theo ID/version | Không có route | UNAVAILABLE; false | Backend; catalog chỉ có format |
| Validate THPT request đầy đủ, suy ra slots/RAG matrix | `POST /api/exam-formats/evaluate` | IMPLEMENTED; true | Backend/RAG; `ui/jobs.py:36` |
| Validate draft thiếu trường, trả missing/conflict/unsupported/readiness | Không có route | PROPOSED; false | Backend + Agent |
| Sinh THPT từ cấu hình đã xác nhận ở client | `POST /api/exams/generate` | IMPLEMENTED; true | Backend; `ui/jobs.py:126` |
| Lấy toàn bộ đề hoàn tất bằng job UUID | `GET /api/exams/{job_id}` | IMPLEMENTED; true | Backend; `ui/jobs.py:282` |
| Danh sách đề/search, GET riêng từng câu, câu đang sinh | Không có route | UNAVAILABLE; false | Backend + UI |
| Poll trạng thái thật / nhận SSE snapshot | `GET .../status`, `GET .../events` | IMPLEMENTED stage-level; true | Backend; `routes_ui.py:62,67` |
| Sửa nội dung một câu, tăng exam revision, hủy duyệt cũ | `PUT .../questions/{question_id}` | IMPLEMENTED; true | Backend; `ui/jobs.py:387` |
| Composer tạo lại một câu, Illustrator khi cần, Solver kiểm tra toàn đề | `POST .../questions/{question_id}/regenerate` | IMPLEMENTED; true | Backend; `ui/jobs.py:428` |
| Áp dụng một batch note; đổi số câu/thêm/xóa/reorder | Không có route | PROPOSED; false | Backend; cấu trúc THPT hiện khóa 22 câu |
| PDF preview local đúng source; status/PDF/log theo revision/hash | `POST/GET .../preview`, `GET .../preview.pdf`, `GET .../preview.log` | IMPLEMENTED; true | Backend; `ui/preview.py`, `routes_ui.py:115` |
| Người dùng duyệt đúng revision/hash | `POST .../approve` | IMPLEMENTED; true | Backend; `ui/jobs.py:417` |
| Export student tex/pdf, teacher json sau duyệt | `GET .../export` | IMPLEMENTED; true | Backend; `ui/jobs.py:504` |
| DOCX/teacher PDF | Không có tổ hợp export hợp lệ | UNAVAILABLE; false | Backend |
| RAG Toán THPT trong generation; VDC fallback kèm warning | `JobManager._retrieve`, `encode_thpt_retrieval` | IMPLEMENTED nội bộ; không phải Agent HTTP action | Backend/RAG; `ui/jobs.py:107`, `intake.py:117` |
| Upload PDF/DOCX, reference file ID | Không có route; uploadedFiles chỉ nhận [] | UNAVAILABLE; false | Backend/RAG |
| Lấy lỗi job thất bại | `GET .../status` → error | IMPLEMENTED; true | Backend; `ui/jobs.py:374` |
| Cancel/retry/resume generation job qua UI API | Không có route | UNAVAILABLE; false | Backend |
| V-ACT 120 câu theo template riêng | `python -m exam_baseline.vact.cli` | IMPLEMENTED CLI; false cho HTTP Agent | Backend; `vact/cli.py:8`, `vact/models.py:30` |
| Baseline JSON / generic MAS LaTeX đồng bộ | `POST /v1/exams/generate`, `/v2/exams/generate` | IMPLEMENTED legacy; true, không dùng thay THPT/V-ACT locked engine | Backend; `routes_baseline.py`, `routes_pipeline.py` |

Test evidence: `tests/api/test_ui_jobs.py`, `tests/api/test_ui_preview.py`,
`tests/api/test_baseline.py`, `tests/api/test_pipeline.py`, `tests/thpt/`, `tests/vact/test_vact.py`.
Descriptor JSON trỏ vào request schema OpenAPI và nhãn ví dụ valid/invalid đã chạy.

## Cách Agent bắt đầu mà không giả định tính năng

Hỏi giáo viên có dùng **Toán THPT 22 câu/90 phút** hay không; hiển thị cấu trúc và
ma trận từ evaluate cho giáo viên xác nhận. Nếu đồng ý, adapter dùng nguyên request
đã evaluate để start, giữ một idempotency key cho lần thử đó. UI/executor phải chặn
duplicate workspace và giữ confirmed values; server chưa kiểm request approval hash.
Nếu cần V-ACT HTTP hoặc thay cấu trúc, giải thích chưa hỗ trợ và giữ draft/note chờ,
không âm thầm thay bằng THPT. Chỉ báo hoàn tất khi job `completed`; đề vẫn chờ người duyệt.
