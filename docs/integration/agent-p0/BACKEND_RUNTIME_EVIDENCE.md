# P0 — Runtime và bằng chứng

| Trường | Giá trị đã đối chiếu |
|---|---|
| Repo | https://github.com/ndmhuy/ASTRA |
| Generation branch / full SHA | merge-mas-and-uiux / **2acb95fbf6a55b7621c786248e10b10ca91a35ab** |
| Target main / inspected SHA | origin/main / f6b7ea87d1f3f6525c8d10c405578d8da8ac885a |
| Integration | Branch merge-mas-and-uiux chứa merge main/uiux2 từ commit4920945, backend PDF và bộ handoff P0; chưa merge vào main |
| Owner bàn giao | Backend/MAS: Huy; UI và Agent tự tích hợp theo contract; owner/ETA API mới UNDECIDED |
| RAG remote branch / fetched HEAD | origin/feat/ndmhuy/rag-corpus / b34251fcde804cdd2c08918cae3216ce21abead6 |
| RAG thực sự được chọn bởi default runtime | **8b8fb7b09182b3d9d1eee0b95818027f52ab004d**; không tự dùng HEAD RAG mới |
| Merge RAG? | Pinned corpus release không nằm trong ancestry generation; loader đọc Git snapshot hoặc portable pack. Module rag_workflow có trong checkout; không merge toàn bộ branch corpus |
| Server | exam_baseline.main:app → api/app.py:create_app; routes_ui + V1/V2 |
| OpenAPI | BACKEND_AGENT_API_OPENAPI.json export từ create_app(Settings.for_offline()).openapi(); /openapi.json của server tương đương route/model structure |
| Source format | docs/guides/THPT_TOAN.md; docs/guides/VACT.md; resources/templates/PROTO_thptqg_toan_v2.tex và PROTO_vact_vact.tex; kiểm hash trước generation |

Các hướng dẫn format ở trên mô tả code/template và ma trận luyện tập, không thay thế
việc team kiểm tra tài liệu chính thức khi tuyên bố chuẩn kỳ thi/năm.

## Khởi chạy ở đúng ref

Agent teammate chỉ cần fetch/inspect ref; không merge branch Backend vào branch Agent để xem API:

```powershell
git fetch origin merge-mas-and-uiux
git show 2acb95fbf6a55b7621c786248e10b10ca91a35ab:src/exam_baseline/ui/contracts.py
```

Trong checkout runtime đúng SHA, từ repo root:

```powershell
git fetch --no-tags origin 8b8fb7b09182b3d9d1eee0b95818027f52ab004d
.\.venv-win\Scripts\python.exe -m pip install -e ".[dev]" -c requirements-tested.txt
.\.venv-win\Scripts\python.exe scripts/install_latex_compiler.py
.\.venv-win\Scripts\python.exe -m uvicorn exam_baseline.main:app --host 127.0.0.1 --port 8000
```

Giữ `.env` và API key trên server; không đưa key vào tài liệu/Frontend. UI job cần
EXAM_PROVIDER=chat_completions với provider/model hợp lệ; default mock của V1 **không**
tự tạo mock UI job thành công. /api/health providerConfigured chỉ kiểm config loại provider,
không probe key/quota. Một worker, UI root default runs/ui (SQLite + job artifacts),
RAG ref mặc định như bảng, PDF cache runs/latex-cache; không gửi local path làm API file ID.

Export OpenAPI không đọc secret `.env`, không gọi inference:

```powershell
.\.venv-win\Scripts\python.exe -X utf8 -c "import json; from pathlib import Path; from exam_baseline.api.app import create_app; from exam_baseline.config import Settings; Path('runs/openapi.json').write_text(json.dumps(create_app(Settings.for_offline()).openapi(), ensure_ascii=False, indent=2), encoding='utf-8')"
```

## Thực chạy cho lần bàn giao này

- `python -m pytest tests/api tests/thpt tests/vact -q`: **115 passed**.
- `python -m pytest tests/test_intake_exporter.py -q`: **7 passed**.
- 53 request/response trong BACKEND_API_SAMPLES_ACTUAL.json được gọi qua TestClient
  của app thật, bao gồm PDF compilation/preview/export thật từ TeX đã lưu. Assertions kiểm
  HTTP status và terminal ready; câu hỏi/RAG/teacher identity là fixture, không phải đề thực tế.
- `python -m rag_workflow.eval --acceptance --corpus-ref 8b8fb7b09182b3d9d1eee0b95818027f52ab004d --out runs/agent-handoff-rag-acceptance.json`:
  **8/8 passed**; kiểm RAG snapshot thật, không gọi model. Bundle vẫn teacher_approved=false,
  runtime_compatibility_verified=false trong metadata nguồn; acceptance không tự đổi các cờ đó.
- OpenAPI, 5 JSON Schema và default evaluate output export từ code cùng SHA; schema giữ
  nguyên cross-field giới hạn của Pydantic chỉ ở runtime, không thêm enum/preset tự nghĩ.
- Bộ full Python ở lượt fix trước cùng SHA:355 passed,1 skipped; real TikZ PDF smoke đã
  qua và kiểm tra trực quan4 trang; frontend8 tests/lint/build qua. Đây là evidence lượt trước,
  không phải rerun frontend hay benchmark model trong lần viết P0.
- Repo-wide verify.py có91 lint errors có sẵn ở rag_workflow; lần này không sửa runtime/lint đó.

**Phân biệt thật/mock:** local server production wiring dùng RAG release + provider cấu hình;
test đã inject Scripted provider và synthetic retrieval để đo contract an toàn. V1 default
mock và generic V2 offline fixtures không được trình bày như model live. Không chạy thêm
live generation và không đưa raw corpus/private teacher data vào bộ bàn giao.

## Định vị source chính xác tại SHA trên

Prefix source link: `https://github.com/ndmhuy/ASTRA/blob/2acb95fbf6a55b7621c786248e10b10ca91a35ab/`.

| Path:line | Nội dung |
|---|---|
| src/exam_baseline/ui/contracts.py:18 | GenerateRequest/formatVersion/input limits |
| src/exam_baseline/thpt/models.py:27 | Native22 slots + part/statement validation |
| src/exam_baseline/vact/models.py:30 | V-ACT120 slots theo batch template |
| src/exam_baseline/ui/jobs.py:36 | THPT request → native slots + RAG matrix |
| src/exam_baseline/ui/jobs.py:126 | Start/idempotency/task lifecycle |
| src/exam_baseline/ui/jobs.py:155 | Stage progress, không phải per-question |
| src/exam_baseline/ui/jobs.py:282 | ExamPackage teacher view/status/key/metadata |
| src/exam_baseline/ui/jobs.py:387 | Edit, exam revision và hủy approval |
| src/exam_baseline/ui/jobs.py:428 | Targeted regenerate + Solver |
| src/exam_baseline/ui/storage.py:27 | Atomic key/receipt persistence |
| src/exam_baseline/ui/storage.py:56 | Restart recovery policy |
| src/exam_baseline/ui/preview.py:15 | Local revision/source-bound PDF service |
| src/exam_baseline/api/routes_ui.py:67 | SSE snapshot wire |
| src/exam_baseline/api/app.py:72 | UI error handlers; không có auth dependency |
| src/exam_baseline/intake.py:49 | Legacy mas-intake-v1 |
| src/exam_baseline/intake.py:117 | Current THPT rich RAG handoff |
| rag_workflow/matrix_retriever.py:94 | Default sample matrix factory |
| rag_workflow/profile_pack.py:43 | Load/verify pinned Git release |

Code là nguồn chuẩn khi tài liệu và schema khác nhau; snapshot response của runtime
có timestamp/UUID chỉ có nghĩa minh họa contract, không dùng làm job ID trên server khác.
