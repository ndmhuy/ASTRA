# P0 — Teacher input và mapping

Runtime/source ref chung tại [capability index](BACKEND_CAPABILITIES_AGENT.md).
**TeacherIntakeDraft: BLOCKED, chưa có schema/version/API hoặc adapter draft → ExamMatrix.**
Owner: Backend + Conversational Agent; cá nhân nhận việc/ETA: UNDECIDED.
[Machine-readable trạng thái](TEACHER_INTAKE_STATUS.json) cố ý có `schema: null`;
đây không phải một schema draft được phê duyệt. Các JSON Schema còn lại export từ model thật.

## Contract có thể dùng ngay

THPT HTTP: `exam_baseline.ui.contracts.GenerateRequest`,
[JSON Schema](schemas/UI_GENERATE_THPT_V1.schema.json). Version hiện có là cặp
`formatId="thpt-math"`, `formatVersion="1"`; **không có `schema_version` trên wire**.
Agent sở hữu draft hội thoại; sau khi người dùng chọn format này, Agent/UI tạo request đầy đủ.
Backend chưa tiếp nhận draft chưa hoàn chỉnh hay confirmed-values metadata.

| Trường / ý nghĩa | THPT HTTP thật | V-ACT CLI thật | Backend derive / preset / lỗi |
|---|---|---|---|
| Family/format | `formatId: thpt-math`, `formatVersion: 1`, `examType: THPT_STANDARD` | `template_id: vact_v1` | THPT format fields có defaults trừ examType; family khác → 422 |
| Môn/phần | subject đúng `Toán Học` | 5 vùng theo template: TV, TA, TO, logic/số liệu, khoa học | THPT derive P1/P2/P3; V-ACT slots phải đúng batch; không có chọn riêng môn V-ACT HTTP |
| Lớp/curriculum/năm | grade đúng 12; không nhận curriculum/textbook/year | Không có grade/curriculum/year trong Request | THPT dùng RAG prerequisite lớp 10–12; năm/mã đề trong template cố định; extra key → 422 |
| Chủ đề/ma trận | `slots: null` hoặc bỏ → derive default; hoặc đủ 22 slots | Bắt buộc đủ 120 slots | Không suy ma trận từ prompt/draft; default là ma trận mẫu luyện tập |
| Thời lượng/số câu | durationMinutes=90, itemCount=22 | Template 150 phút, đúng 120 slots; không có duration/count override | THPT trái giá trị → 422; đổi số câu chưa hỗ trợ |
| Dạng câu | 12 MCQ + 4 đúng/sai × 4 ý + 6 trả lời ngắn | 120 MCQ A/B/C/D | Cố định theo engine/template, không tự map generic difficulty |
| Mức độ/điểm | Slot.level NB/TH/VD/VDC; P2 có 4 statement_levels | Slot.level NB/TH/VD/VDC | THPT tổng10, P1=.25/câu, P2=[0,.1,.25,.5,1], P3=.5/câu từ catalog; chưa có preset độ khó chính thức |
| Reference/RAG | uploadedFiles=[]; backend tự retrieve Toán THPT | reference_material tối đa20 chuỗi | THPT file/reference_material không phải input UI; thiếu coverage → failed retrieval_gap |
| Yêu cầu thêm | prompt mặc định "", tối đa10.000 ký tự | requirements tối đa30 chuỗi, mỗi chuỗi1..30.000 ký tự | Prompt chỉ là yêu cầu cho Composer, không thay hard constraints; không chứng minh đã làm đúng ý |

THPT custom slot: `id`, `part`, `topic`, `objective`, `level`, `statement_levels`.
ID phải đúng thứ tự P1-1..12, P2-1..4, P3-1..6; part khớp ID; P2 đúng bốn mức,
các phần khác không có statement_levels. topic/objective 1..30.000 ký tự, enum mức như trên.
API kiểm cấu trúc; chưa kiểm được mọi mâu thuẫn ngữ nghĩa, tổng tải nội dung hay cam kết RAG trước start.
Không thay thế các enum này bằng easy/medium/hard của baseline.

V-ACT: [schema CLI riêng](schemas/VACT_CLI_REQUEST.schema.json),
request hợp lệ ở `examples/vact/request.json`; q1..q120 và part/batch lấy từ template.
Schema không tự diễn tả hết cross-field validators. `Request.model_validate_json(...)`
là bước kiểm bắt buộc. V-ACT qua `/api/exams/generate` hiện trả 422 khi gửi enum DGNL;
không có public validate/normalize draft V-ACT. Năng lực nội dung cần giáo viên kiểm tra.

## Ba loại matrix cần phân biệt

1. `core.models.ExamMatrix`: generic baseline/mas-intake-v1, gồm topic/type/difficulty/points counts.
   [Schema](schemas/GENERIC_EXAM_MATRIX.schema.json).
2. `thpt.models.Request`: native engine slots + requirements, không phải generic ExamMatrix.
   [Schema](schemas/THPT_ENGINE_REQUEST.schema.json).
3. RAG matrix: dictionary `schema_version=1.0`, `matrix_id`, `questions` với
   question_id/part/topic/learning_objective/level/statement_levels và retrieval knobs.

`POST /api/exam-formats/evaluate` gọi `ui/jobs.py:36 resolve_request`:
GenerateRequest → default/caller slots → native Request **và** RAG matrix.
Response thật: `{status:"validated", formatId, formatVersion, request, retrievalMatrix}`;
[bản đầy đủ](THPT_EVALUATE_RESPONSE_ACTUAL.json). Đây là preview cấu hình,
chưa chạy retrieval, chưa có đề, chưa có requestHash/approval token, chưa xác nhận readiness mọi capability.

Trong generate: RAG retrieve → `encode_thpt_retrieval` kiểm mỗi slot có đúng một
question_context và mas_intake_rag, subject Toán/text không rỗng, nhóm context theo P1/P2/P3.
Solver không thấy evidence/Composer key. Không yêu cầu giáo viên tự nhập full matrix/RAG records.

`mas-intake-v1` vẫn là **contract cũ, khác luồng** (`intake.py:49`), đã đòi full generic
ExamMatrix + thông tin textbook/grade + RAG cùng scope; CLI `python -m exam_baseline.intake`.
[Schema](schemas/LEGACY_MAS_INTAKE_V1.schema.json). Không phải TeacherIntakeDraft adapter
và không dùng để ép prerequisite lớp10/11 thành lớp12.

## Những câu trả lời chưa có API

- Không có missingFields/conflicts/unsupported/readyForConfirmation hoặc messageVi chuẩn.
  422 là lỗi schema; Agent có thể giải thích từ detail.loc, nhưng không tự gọi đó là backend draft readiness.
- Trường khóa được khai báo sai bị reject; input hợp lệ có slots được giữ. Không có workflow
  reconciliation giữa confirmed draft và backend-derived values. Trái prompt ngữ nghĩa có thể chưa bị phát hiện.
- Không có hash của generation configuration được giáo viên duyệt trên server.
  `contentHash` ở package chỉ dùng **sau generation**, cho approve/preview của đề.
- P0 chưa chốt schema draft mới: cần thống nhất enum family/section, nguồn default,
  confirmed values/conflict semantics trước khi Backend và Agent code adapter.
