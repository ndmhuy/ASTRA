# P0 — Hiện tại, blocker và trách nhiệm P1

Mọi trạng thái dưới đây tại runtime SHA `2acb95fbf6a55b7621c786248e10b10ca91a35ab`.
Chưa triển khai thì `callableNow=false`; owner là nhóm đề xuất nhận việc, không phải
cam kết cá nhân/ETA. Assignee và lịch P1: **UNDECIDED**.

| Phần | Hiện có | Còn thiếu / owner |
|---|---|---|
| TeacherIntakeDraft | Agent sở hữu hội thoại/draft; THPT GenerateRequest đã validate | BLOCKED: versioned draft schema, partial validation, missing/conflict/readiness, draft→matrix; Backend + Agent |
| Preset | Một format catalog và default THPT matrix | Registry, preset ID/version, official/practice metadata; Backend + RAG |
| Generation plan approval | Client phải xác nhận ý định; idempotency tránh lặp request | Server kiểm confirmed request hash/version; Backend + Agent + UI |
| V-ACT | CLI/engine/template 120 câu | Teacher-facing API/catalog/RAG integration; Backend + RAG |
| Persistent job | UUID, SQLite receipt/state, queued/running/completed/failed | Durable/distributed executor, cancellation/retry API; Backend |
| Progress | Real stage callbacks + polling/SSE snapshot | Per-question events/preview, event ID/replay; Backend + UI |
| Workspace constraint | UI/executor có thể chặn start trùng | Chưa có workspaceId/ownership, server chưa enforce 1 active/workspace; Backend + UI |
| Revision | Single-question edit/regenerate; exam revision/hash; hủy duyệt cũ | Batch revision, per-question revision, typed receipts/partial failure; Backend |
| Change question count | Fixed THPT22/VACT120 | Restructure matrix/template, preview delete/add và xác nhận; Backend + RAG |
| Notes while generating | Agent có thể giữ note ngoài pipeline | Server note storage/batch apply chưa có; Agent quản lý note, UI hiển thị; Backend nhận revision sau này |
| PDF | Local draft preview + approved export | Frontend viewer theo handoff PDF; UI/UX |
| Auth/quota/upload | Chưa có user/workspace auth, quota/file API | Production gate + server policies; Backend, UI giữ secrets ngoài client |

## Job, progress và chat (P1 requirement; trạng thái P0)

- Generation request là JSON input; job là UUID bền vững trong SQLite; preview câu
  không phải job progress. `POST /api/exams/generate` trả 202 `{jobId,status}`.
- `GET .../status`: stage, stageName, percent, estimatedSecondsLeft, completedItems,
  totalItems, statusMessage, jobId, status, error. Percent là mốc stage cố định
  0/5/20/50/65/85/100, không phải ước tính theo token/câu. estimatedSecondsLeft luôn0.
  completedItems là0 trong khi chạy và22 khi xong; không được báo "đã sinh 8/22".
- `GET .../events`: `data: <snapshot JSON>\n\n`; server so nội dung snapshot để giảm
  duplicate trên cùng connection, poll nội bộ .3s, terminal thì đóng. Không có `id:`,
  event sequence, Last-Event-ID replay hoặc heartbeat. Reconnect lấy snapshot hiện tại;
  client thay thế state, không cộng dồn counter hay coi event là exactly-once.
- `GET .../{jobId}` chỉ dùng khi completed; chưa xong trả409 exam_not_ready.
  Một worker, tối đa2 job chạy pipeline toàn process; queue chưa có giới hạn user/workspace.
- Restart: queued/running → failed server_restarted; shutdown có thể server_stopped.
  Không resume API. Muốn start mới sau failed, dùng idempotency key mới; cùng key trả job cũ.
  CLI THPT/V-ACT có `--resume` cùng request/output, không tương đương retry UI job.
- Chat không dùng lock generation: Agent/UI có thể giữ hội thoại/note khi job đang chạy.
  Backend không lưu chat/note và không cung cấp conversational endpoint.

## Revision và ghi chú đã xác nhận

Giữ đúng yêu cầu sản phẩm: đang sinh → ghi note chưa áp dụng; xong → trình tất cả
note để giáo viên thêm/sửa/xóa → xác nhận → mới gọi action Backend hỗ trợ.

Hiện **không có revise_exam/batch_revision API**. Không gọi nhiều PUT rồi báo "batch applied"
như một transaction. Nếu cần dùng tạm các thao tác lẻ, phải thống nhất riêng với giáo viên,
đọc package sau từng lần và dùng exam revision mới; có thể bị áp dụng một phần khi lỗi.

- Mapping do package cung cấp: numeric id1..22 là path address; stableId=P1-1..12,
  P2-1..4, P3-1..6. Mỗi phần đều có "câu3", nên note phải kèm part + stableId + exam revision.
- `question.examRevision` là exam revision, **không có question revision độc lập**.
  Không có reorder/add/delete. Muốn20→15 hiện unsupported; Agent không tự chọn câu bỏ.
- Edit/regenerate chỉ khi completed; cả hai trả package revision+1, contentHash mới,
  approved=false. Không có receipt accepted/applied/partially_applied chuẩn hóa.
- PUT: validate format/shape, render lại; không chạy Solver/Reviewer, chưa xác minh toán/độ khó.
  Regenerate: Composer một câu, Illustrator nếu cần, Solver toàn đề; không chạy lại Reviewer.
  Luôn chờ người dùng xem/duyệt. VERIFIED trong package nghĩa là **đã có human approval
  của exam**, không phải independent automatic per-question certification.
- Approval hiện tin reviewer string do client gửi, không có authenticated identity.
  Package là teacher view, có private answers/solutions; không expose như student API công khai.

## Ranh giới input/auth/upload (giới hạn P0)

THPT prompt≤10.000 ký tự, regenerate instruction≤4.000; không có global HTTP body byte limit
hoặc teacher token budget. Native Text1..30.000 ký tự; reference_material≤20, requirements≤30
ở CLI; max_prompt_chars mặc định200.000 được dùng trong baseline/generic pipeline,
chưa được enforce như tổng prompt limit trong native THPT/V-ACT. Không phải giới hạn HTTP request.
Top-level extra fields bị reject. Bên trong EditRequest.question là dict: không phải typed patch,
unknown keys có thể bị bỏ qua; chỉ gửi các trường đã mô tả trong error/API guide.

uploadedFiles chỉ []: không có MIME/size/pages/file-count policy dùng được, file ID,
retention, extract API hay permissions. RAG server riêng `rag_workflow.app` nhận JSON
body≤2.000.000 bytes; query_text≤2.000 ký tự, top_k≤20; **không áp dụng như upload policy ASTRA**.

Chưa có auth/roles/ACL/workspace quotas/rate limiter/spending cap. Job IDs không phải quyền
truy cập. Runtime này chỉ phù hợp tích hợp local/trusted, chưa phải boundary multi-tenant.
Provider/model/key do server config `.env`; HTTP timeout mặc định90s/call (có thể override),
max_output_tokens8192, THPT Composer concurrency3, UI generation2, PDF compile1/process.
Regenerate chỉ có per-job lock, không dùng generation semaphore toàn process.
Không có fallback model tự động. Cost phụ thuộc model/usage, không có teacher quota API.

Evidence được nhắc là untrusted trong agent prompt; content/TikZ có validation, compiler tắt
shell escape/untrusted. Đây không phải đầy đủ prompt-injection/content-safety middleware.
Không gửi secrets trong draft/prompt, không để Agent tự nhận quyền tool từ reference documents.

P1 đề xuất lỗi `UNSUPPORTED_CAPABILITY` tại capability adapter; backend hiện **chưa** có
error đó. Route không tồn tại trả404/405, input sai enum422, export sai422 unsupported_export.
Adapter nên chặn action ngoài allowlist và trả receipt local ghi rõ chưa gọi Backend.
