# ASTRA — Cách chạy

Chạy các lệnh trong PowerShell tại thư mục dự án. Dùng CPython chuẩn 3.10 trở lên.

## Đề Toán THPT — template gốc cố định

Để chạy luồng RAG → MAS với ma trận mẫu 22 câu, tải snapshot corpus và chạy
từ thư mục gốc repo sau khi cấu hình provider trong `.env`:

```powershell
git fetch origin staging/rag
.\.venv-win\Scripts\python.exe -m exam_baseline.thpt.cli --rag --output runs/thpt/rag_01
```

Thêm `--request <file.json>` để dùng ma trận THPT của bạn. Có thể chọn commit corpus
bằng `--rag-corpus-ref <sha>` hoặc dùng gói corpus đã xuất với `--rag-pack-dir <directory>`.
Khi thiếu dẫn chứng bắt buộc, CLI báo `retrieval_gap` và ID câu trước khi gọi model.
Cảnh báo và nguồn theo từng câu nằm trong `_internal/result.json`. Ngữ cảnh đầy đủ nằm
trong `_internal/request.json`. Để tiếp tục một lượt bị gián đoạn, dùng cùng request
và output với `--rag --resume`; CLI sẽ dùng lại ngữ cảnh đã lưu.

Sau khi cấu hình `.env`, chạy:

```powershell
.\.venv-win\Scripts\python.exe -m exam_baseline.thpt.cli --request examples/thpt/request.json --output runs/thpt/de_01
```

Sửa ma trận từng câu trong `examples/thpt/request.json` (NB/TH/VD/VDC).
Đây là ma trận luyện tập tham khảo, cần giáo viên duyệt.
Kết quả: `de_thi.tex`, `loi_giai.md`, đáp án JSON và báo cáo trong `_internal/`.
Đề mới mặc định dùng font Unicode tiếng Việt; compile bằng XeLaTeX hoặc LuaLaTeX.
Composer mặc định tạo ba phần song song. Thêm `--composer-concurrency 1` để chạy
tuần tự hoặc `2` nếu quota thấp. Thời gian/token/chi phí ước tính ở `_internal/result.json`.
Chọn thư mục output mới mỗi lần. Luồng này dùng template THPT gốc được khóa bằng SHA-256.
Đọc [quy ước template và ma trận THPT](docs/guides/THPT_TOAN.md).

## Đề V-ACT — 120 câu theo template riêng

```powershell
.\.venv-win\Scripts\python.exe -m exam_baseline.vact.cli --request examples/vact/request.json --output runs/vact/de_01
```

Kết quả là `de_thi.tex`, `loi_giai.md`, đáp án JSON và `_internal/result.json`.
Nếu lỗi API, thêm `--resume` với cùng request/output. Có thể giới hạn số batch đồng thời
bằng `--composer-concurrency 1` và `--solver-concurrency 1` ngay từ lần chạy đầu.
Đọc [quy ước VACT](docs/guides/VACT.md).

## 1. Cài đặt lần đầu

Nếu đã có môi trường `.venv-win` hoạt động thì bỏ qua bước tạo môi trường.

```powershell
python -m venv .venv-win
.\.venv-win\Scripts\python.exe -m pip install -e ".[dev]" -c requirements-tested.txt
```

Nếu chưa có `.env`, sao chép `.env.example` thành `.env`. Không ghi đè file cấu hình đang dùng.

## 2. Chạy mẫu không cần API key

```powershell
.\.venv-win\Scripts\python.exe -m exam_baseline.baseline.cli --offline
```

Mở `ket_qua.md` theo đường dẫn terminal in ra để xem đề, đáp án và báo cáo.
Kết quả nằm trong `runs/offline/`. Đây là đề mẫu cố định, không gọi model thật.

## 3. Chạy với model thật

Điền provider, model, key và endpoint vào `.env`. Ví dụ cấu hình Gemini:

```dotenv
EXAM_PROVIDER=chat_completions
EXAM_MODEL=gemini-3.5-flash-lite
EXAM_API_KEY=DIEN_KEY_GOOGLE_CUA_BAN
EXAM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
EXAM_TOKEN_LIMIT_FIELD=max_tokens
EXAM_RESPONSE_FORMAT=json_object
EXAM_MAX_OUTPUT_TOKENS=8192
EXAM_TIMEOUT_SECONDS=120
```

Quyền truy cập và hạn mức phụ thuộc tài khoản. Khởi động lại server sau khi sửa `.env`.

**Terminal 1:** chạy server và giữ terminal mở:

```powershell
.\.venv-win\Scripts\python.exe -m uvicorn exam_baseline.main:app --host 127.0.0.1 --port 8000
```

**Terminal 2:** gửi yêu cầu mẫu và lưu kết quả:

```powershell
.\.venv-win\Scripts\python.exe -m exam_baseline.baseline.cli --live
```

Mở `ket_qua.md` trong thư mục `runs/live/` theo đường dẫn được in ra.
`--live` sử dụng provider mà server đang chạy; kiểm tra model trong báo cáo.

Hoặc mở [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs), chọn
**POST /v1/exams/generate → Try it out → Execute**. Xem kết quả tại **Response body**.
Dừng server bằng **Ctrl+C**.

## 4. Dùng đầu vào riêng

Xuất JSON mẫu ra một file mới:

```powershell
.\.venv-win\Scripts\python.exe -m exam_baseline.baseline.cli --export-example inputs/request.json
```

Sửa file đó rồi gửi đến server:

```powershell
.\.venv-win\Scripts\python.exe -m exam_baseline.baseline.cli --live --request inputs/request.json
```

## 5. Pipeline Composer → Illustrator → Solver → Reviewer

Chạy thử offline, nhận một file đề `runs/pipeline/demo/de_thi.tex`:

```powershell
.\.venv-win\Scripts\python.exe -m exam_baseline.pipeline.cli --request examples/pipeline/text_01/input.json --fixture-dir examples/pipeline/text_01 --output runs/pipeline/demo
```

Để gọi model thật, bỏ `--fixture-dir` và dùng `.env` ở mục 3. Không cần khởi động server
khi chạy CLI. Thư mục output phải chưa tồn tại. Cả bốn vai trò là agent riêng;
Illustrator sinh code **TikZ/PGFPlots**, ghép trực tiếp với đề vào một file `.tex`.
Reviewer gửi phản hồi về Composer tối đa **một lần**, sau đó dừng để bạn kiểm tra bằng mắt.
Solver đọc LaTeX/code hình, không cần bật vision. Dùng **XeLaTeX hoặc LuaLaTeX**;
thêm `--compile` nếu máy đã cài compiler. JSON/đáp án/review/trace nằm trong `_internal/`,
cùng `human_review.md` liệt kê những điểm cần kiểm tra.
Qua API, `POST /v2/exams/generate` trả trực tiếp file LaTeX khi đạt kiểm tra.

[Điều phối, vòng sửa, cấu hình và benchmark](docs/architecture/PIPELINE_PLAN_AND_BENCHMARK.md).

## 6. Chạy tests

```powershell
.\.venv-win\Scripts\python.exe -m pytest -q
```

[Tác dụng của từng thư mục và vị trí sửa code](docs/CAU_TRUC_THU_MUC.md).

Các lệnh cũ `exam_baseline.cli`, `exam_baseline.mini_cli`, `exam_baseline.pipeline_cli`
vẫn chạy được qua launcher tương thích. Uvicorn vẫn dùng `exam_baseline.main:app`.

[ASTRA mini draft-only Composer → Illustrator và contract bàn giao](docs/archive/MINI_COMPOSER_ILLUSTRATOR.md).

[Khung đề ĐGNL HCM 120 câu theo đề tham chiếu 11](docs/guides/HCM_DE11_FORMAT.md).

[Nhập mẫu LaTeX/kho đề và xuất đề, đáp án, phiếu tô LaTeX](docs/guides/LATEX_PIPELINE.md).

[MAS intake và xuất PDF/DOCX sau khi duyệt](docs/MAS_INTAKE_AND_EXPORT.md).

## RAG workflow và bàn giao MAS

Chạy workbench truy hồi tại thư mục repo:

```powershell
python -m rag_workflow.app
```

Mở http://127.0.0.1:8765. Module `rag_workflow` hỗ trợ BM25, embedding và hybrid,
truy xuất ma trận và Topic Pack qua `retrieve_exam_context()` và `get_topic_pack()`.
Adapter `mas-intake-v1` cung cấp dữ liệu cho luồng tạo đề. Nguồn corpus được đọc
từ snapshot `origin/staging/rag`; cần `git fetch origin staging/rag` trước khi chạy
với corpus thật. Xem [hướng dẫn RAG](docs/rag-workflow.md) và
[bộ đánh giá](eval/README.md).

```powershell
python scripts/verify.py
python -m rag_workflow.eval --acceptance
```
