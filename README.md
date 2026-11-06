# ASTRA — Cách chạy

Chạy các lệnh trong PowerShell tại thư mục dự án. Dùng CPython chuẩn 3.10 trở lên.

## 1. Cài đặt lần đầu

Nếu đã có môi trường `.venv-win` hoạt động thì bỏ qua bước tạo môi trường.

```powershell
python -m venv .venv-win
.\.venv-win\Scripts\python.exe -m pip install -e ".[dev]" -c requirements-tested.txt
```

Nếu chưa có `.env`, sao chép `.env.example` thành `.env`. Không ghi đè file cấu hình đang dùng.

## 2. Chạy mẫu không cần API key

```powershell
.\.venv-win\Scripts\python.exe -m exam_baseline.cli --offline
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
.\.venv-win\Scripts\python.exe -m exam_baseline.cli --live
```

Mở `ket_qua.md` trong thư mục `runs/live/` theo đường dẫn được in ra.
`--live` sử dụng provider mà server đang chạy; kiểm tra model trong báo cáo.

Hoặc mở [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs), chọn
**POST /v1/exams/generate → Try it out → Execute**. Xem kết quả tại **Response body**.
Dừng server bằng **Ctrl+C**.

## 4. Dùng đầu vào riêng

Xuất JSON mẫu ra một file mới:

```powershell
.\.venv-win\Scripts\python.exe -m exam_baseline.cli --export-example inputs/request.json
```

Sửa file đó rồi gửi đến server:

```powershell
.\.venv-win\Scripts\python.exe -m exam_baseline.cli --live --request inputs/request.json
```

## 5. Pipeline Composer → Illustrator → Solver → Reviewer

Chạy thử offline, nhận một file đề `runs/pipeline/demo/de_thi.tex`:

```powershell
.\.venv-win\Scripts\python.exe -m exam_baseline.pipeline_cli --request examples/pipeline/text_01/input.json --fixture-dir examples/pipeline/text_01 --output runs/pipeline/demo
```

Để gọi model thật, bỏ `--fixture-dir` và dùng `.env` ở mục 3. Không cần khởi động server
khi chạy CLI. Thư mục output phải chưa tồn tại. Cả bốn vai trò là agent riêng;
Illustrator sinh code **TikZ/PGFPlots**, ghép trực tiếp với đề vào một file `.tex`.
Reviewer gửi phản hồi về Composer tối đa **một lần**, sau đó dừng để bạn kiểm tra bằng mắt.
Solver đọc LaTeX/code hình, không cần bật vision. Dùng **XeLaTeX hoặc LuaLaTeX**;
thêm `--compile` nếu máy đã cài compiler. JSON/đáp án/review/trace nằm trong `_internal/`,
cùng `human_review.md` liệt kê những điểm cần kiểm tra.
Qua API, `POST /v2/exams/generate` trả trực tiếp file LaTeX khi đạt kiểm tra.

[Điều phối, vòng sửa, cấu hình và benchmark](docs/PIPELINE_PLAN_AND_BENCHMARK.md).

## 6. Chạy tests

```powershell
.\.venv-win\Scripts\python.exe -m pytest -q
```

[Tác dụng của từng thư mục](docs/CAU_TRUC_THU_MUC.md).

[ASTRA mini draft-only Composer → Illustrator và contract bàn giao](docs/MINI_COMPOSER_ILLUSTRATOR.md).

[Khung đề ĐGNL HCM 120 câu theo đề tham chiếu 11](docs/HCM_DE11_FORMAT.md).

[Nhập mẫu LaTeX/kho đề và xuất đề, đáp án, phiếu tô LaTeX](docs/LATEX_PIPELINE.md).
