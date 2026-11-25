# P0 — API, validation và request/response mẫu

Source ref: `merge-mas-and-uiux@2acb95fbf6a55b7621c786248e10b10ca91a35ab`.
[OpenAPI export thật](BACKEND_AGENT_API_OPENAPI.json) liệt kê method/path/schema;
[53 ví dụ thực chạy](BACKEND_API_SAMPLES_ACTUAL.json) ghi request, HTTP status, body
hoặc excerpt được đánh dấu rõ. Dữ liệu/model/RAG trong ví dụ là fixture tổng hợp;
FastAPI, validator, native engine và TeX compiler chạy thật. Không dùng API key/model live.

## THPT vertical slice

```http
POST /api/exam-formats/evaluate
Content-Type: application/json

{"formatId":"thpt-math","formatVersion":"1","subject":"Toán Học","grade":12,"examType":"THPT_STANDARD","durationMinutes":90,"itemCount":22,"prompt":"Đề luyện tập","uploadedFiles":[]}
```

200 `{status:"validated",formatId:"thpt-math",formatVersion:"1",request:{...},retrievalMatrix:{...}}`.
Full request/response: [request](THPT_GENERATE_REQUEST_VALID.json),
[evaluate response](THPT_EVALUATE_RESPONSE_ACTUAL.json). Cho giáo viên xem cấu hình này;
không coi đây là phê duyệt trên server hoặc xác nhận coverage RAG.

Gửi cùng body tới `POST /api/exams/generate`, header `Idempotency-Key`1..128 ký tự.
202 `{jobId:"<UUID>",status:"queued"}` (gọi lại cùng key/body trả status hiện tại).
Key là global trong SQLite, chưa scope user/workspace. Cùng key/body không tạo job lần hai;
khác body409. Giữ nguyên key khi mất response/start timeout, không tạo key mới để "retry network".

Poll `GET /api/exams/{jobId}/status`: 200 snapshot. Chỉ `status=completed` là đã có đề;
200 `status=failed,error={code,message,details}` là thất bại. `GET .../{jobId}` trước
completed409; khi xong trả examId, revision, contentHash, questions, warnings/gaps/provenance,
preview và visualWarnings. UUID phải hợp lệ; examId bằng jobId; path số câu dùng numeric id,
còn stableId dùng để map ý định từ note. Xem examples open_exam/job_completed_snapshot.

## Sửa và duyệt

```http
PUT /api/exams/{jobId}/questions/1
Content-Type: application/json

{"revision":1,"question":{"stableId":"P1-1","stem":"Tính $2+2$.","choices":{"A":"$4$","B":"$3$","C":"$5$","D":"$6$"},"key":"A","explanation":"Cộng được $4$."}}
```

Chỉ gửi field được hỗ trợ: stem, explanation; MCQ choices/key; P2 statements gồm
text/answer(boolean)/solution; P3 key dạng số, dấu phẩy thập phân, tối đa4 ô.
stableId nếu gửi phải không đổi. question là dict không có typed patch/unknown-field guarantee;
không gửi drawingLatex/level/topic để mong server sửa các trường đó. Validate Question rồi render,
không solve lại khi PUT. Response200 là package revision+1, contentHash mới, approved=false.

`POST .../questions/1/regenerate` body `{revision:2,instruction:"Sửa câu này dễ hiểu hơn"}`:
Composer repair theo slot hiện có, không hứa đổi level ma trận; Solver kiểm lại, không Reviewer lần2.
HTTP response chỉ trả khi sửa xong, không có revision-job ID/progress riêng. Mọi sửa cần xem lại bằng mắt.
Lỗi ProviderError/ContractError ở regenerate chưa có đầy đủ HTTP exception mapping:
có thể thành500 không phải JSON error chuẩn. Agent cần fallback lỗi Backend an toàn,
không parse bắt buộc error.code cho mọi response.

`POST .../approve` body `{revision:<current>,contentHash:"<current64hex>",reviewer:"<teacher label>"}`.
200 package approved=true; không phải xác thực danh tính reviewer. Hash là nội dung đề đã sinh,
không phải hash của draft/request trước generation. Cùng revision mà hash sai409 stale_hash.

## PDF và exports

`POST .../preview` body `{revision,contentHash}` →202 queued/compiling hoặc200 ready cached.
`GET .../preview?revision=...&contentHash=...` trả metadata; dùng nguyên statusUrl/pdfUrl/logUrl.
`GET .../preview.pdf?...` trả inline application/pdf khi ready; đây là draft xem cho giáo viên.
`GET .../preview.log?...` có diagnostics khi đã có log. Chưa có log404.
Preview không gọi model/không đổi source. Cache/source hash được kiểm; revision mới cần preview mới.
Compiler thiếu503; compilation failure thể hiện **status=failed** dù GET status HTTP200.

`GET .../export?type=STUDENT_EXAM&format=tex|pdf` và `type=TEACHER_KEY&format=json`:
phải có approval hiện tại; PDF còn cần preview ready. Tổ hợp teacher/pdf422 unsupported_export;
format=docx422 validation. `preview.pdf` không phải publication/approval receipt.

## Lỗi hiện có và cách Agent giải thích

Thông điệp tiếng Việt dưới đây là **gợi ý adapter**, server chưa có messageVi chuẩn.
Không gán mọi lỗi thành câu hỏi thiếu input của giáo viên.

| HTTP / location | Code / hình dạng | Diễn giải / hành động |
|---|---|---|
| 422 validation body/path/header/query | `{detail:[{type,loc,msg,input,...}]}` | Thiếu/sai field theo loc; ví dụ itemCount15: literal_error, loc=[body,itemCount], expected22 |
| 422 native Pydantic handler | `{error:{code:"invalid_contract",message,fields:[{location,type}]}}` | Nội dung/shape không hợp lệ; cho sửa input câu hỏi, không tự bịa lỗi ngữ nghĩa |
| 404 job_not_found / question_not_found | `{error:{code,message,details}}` | Không tìm thấy job/câu; kiểm jobId/mapping |
| 409 exam_not_ready | same error envelope | Đề chưa hoàn tất; đọc status |
| 409 idempotency_conflict | `{error:{code,message}}` | Key đã dùng cho body khác; không retry như request cũ |
| 409 stale_revision / stale_hash | UI error envelope | Tải lại package và xin xác nhận bản mới trước thao tác có tác động |
| 422 invalid_question_id / 409 invalid_repair | UI error envelope | Không đổi binding câu; invalid_repair là lỗi repair Backend/model, không hỏi teacher nhập lại API metadata |
| 409 artifact_changed | UI error envelope | Source ngoài revision đã thay đổi/mất; dừng duyệt/export, báo Backend |
| 409 approval_required | UI error envelope | Đề hiện tại cần giáo viên duyệt |
| 422 unsupported_export | UI error envelope | Tổ hợp xuất chưa hỗ trợ |
| 503 latex_compiler_unavailable | UI error envelope | Thiếu compiler server; lỗi setup, không regenerate đề |
| 409 preview_not_ready | error.details chứa preview state | Request/poll preview; không dùng PDF cũ |
| failed job / GET status200 | retrieval_gap + details gap list | Thiếu evidence hoặc scope/corpus không hợp; hiển thị gaps, chuyển RAG/Backend; chỉ hỏi giáo viên khi gap cụ thể nói scope cần làm rõ |
| failed job / GET status200 | provider_not_configured; provider_auth_error/access_denied/not_found | Lỗi cấu hình/key/model Backend; không hỏi giáo viên API key |
| failed job / GET status200 | provider_timeout/rate_limited/unavailable/unreachable/... | Lỗi provider/quota/hạ tầng, báo đúng lỗi; chưa có job retry API |
| failed job / GET status200 | generation_failed; server_restarted/server_stopped | Lỗi pipeline/interrupted, giữ job lỗi để tra; không nói đã tạo đề |
| preview status failed / GET200 | latex_compile_failed/latex_compile_timeout/preview_interrupted/preview_artifact_changed | Hiện diagnostics và tùy lỗi retry preview, không tự khẳng định sửa nội dung |
| Route chưa tồn tại | 404 `{detail:"Not Found"}`, có thể405 với sai method | Chưa có UNSUPPORTED_CAPABILITY server envelope; adapter allowlist chặn trước |

V-ACT gửi examType=DGNL_DHQG tới evaluate/generate422; không có valid HTTP V-ACT request
ở namespace UI này. Valid CLI: `examples/vact/request.json`; invalid thiếu slots →
CLI exit1 `{error:"invalid_contract",fields:[...]}`. Xem schema CLI và tests/vact.

## Legacy APIs có hành vi khác

`POST /v1/exams/generate`: generic GenerationRequest có full core ExamMatrix;
JSON GenerationResponse.status phải kiểm riêng. **HTTP200 có thể constraint_failure**,
validation.passed=false (`tests/api/test_baseline.py:101`). Provider failure503/504,
schema failure502, context too large413. Fixture default offline trả mock cố định;
không phải chứng nhận baseline sinh THPT/V-ACT đúng template.

`POST /v2/exams/generate`: generic PipelineRequest (workflow_version=cisr-v3), đồng bộ;
200 application/x-tex kèm X-Run-ID/X-Human-Review-Required, không phải persistent UI job.
422 cấu hình/nội dung; không có final_latex thì409/502/504 theo result. Đây là draft generic
download trước review theo contract cũ; không thay thế approval/export guard của UI THPT.
V1 format_profile=hcm_dgnl_de11 là profile JSON cũ, không chứng minh V-ACT locked-template UI API.

Legacy `exam_baseline.exporter.export` có PDF/DOCX từ draft + ExportReview qua Python/CLI,
không phải `/api` DOCX export và không tái tạo locked THPT/V-ACT template. Agent chưa có HTTP action đó.
