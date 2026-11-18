# ASTRA — Hướng dẫn chạy

Hướng dẫn chạy ASTRA trên Windows bằng PowerShell cho nhóm phát triển. Luồng web tạo đề Toán THPT gồm 22 câu, thời lượng làm bài 90 phút, lấy dữ liệu từ RAG và xuất bản nháp theo mẫu LaTeX.

## 1. Cài đặt lần đầu

Cần Git, CPython 3.10 trở lên (repo ghim phiên bản 3.11.1) và Node.js 22.12 trở lên. Nếu chưa có mã nguồn, clone nhánh tích hợp.

```powershell
git clone --branch merge-mas-and-uiux https://github.com/ndmhuy/ASTRA.git
cd ASTRA
```

Từ thư mục ASTRA, tạo môi trường Python và tải snapshot RAG. Nếu đã có `.venv-win`, bỏ qua dòng tạo môi trường.

```powershell
python -m venv .venv-win
.\.venv-win\Scripts\python.exe -m pip install -e ".[dev]" -c requirements-tested.txt
git fetch --no-tags origin 8b8fb7b09182b3d9d1eee0b95818027f52ab004d
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Để xem trước PDF, cài Tectonic trên Windows x64. Nếu máy đã có XeLaTeX, LuaLaTeX hoặc Tectonic trong `PATH` thì có thể dùng trình biên dịch đó. Lần biên dịch đầu có thể cần mạng để tải gói TeX.

```powershell
.\.venv-win\Scripts\python.exe scripts/install_latex_compiler.py
```

## 2. Cấu hình Gemini

Sửa các dòng tương ứng trong `.env` ở thư mục gốc. Điền khóa Google vào `EXAM_API_KEY` và giữ khóa trong file này. [Lấy API key trong Google AI Studio](https://aistudio.google.com/apikey).

```dotenv
EXAM_PROVIDER=chat_completions
EXAM_MODEL=gemini-3.1-flash-lite
EXAM_API_KEY=<GOOGLE_API_KEY>
EXAM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
EXAM_TOKEN_LIMIT_FIELD=max_tokens
EXAM_RESPONSE_FORMAT=json_schema
EXAM_SCHEMA_AS_TOOL=false
EXAM_STRUCTURED_OUTPUT_STRICT=false
EXAM_MAX_OUTPUT_TOKENS=8192
EXAM_TIMEOUT_SECONDS=120
```

Khởi động lại backend sau khi đổi `.env`. Nếu bật trần chi phí `EXAM_SPEND_LIMIT_USD`, đặt cả hai đơn giá theo model đang dùng. Trần của ASTRA tính theo sổ chi phí cục bộ và được giữ qua các lần khởi động. [Cấu hình mẫu](.env.example) · [Bảng giá Gemini](https://ai.google.dev/gemini-api/docs/pricing).

## 3. Mở backend và frontend

**Terminal 1** — tại thư mục ASTRA, chạy một tiến trình backend và giữ terminal mở.

```powershell
.\.venv-win\Scripts\python.exe -m uvicorn exam_baseline.main:app --host 127.0.0.1 --port 8000
```

Kiểm tra [trạng thái backend](http://127.0.0.1:8000/api/health) hoặc mở [trang API](http://127.0.0.1:8000/docs).

**Terminal 2** — cũng bắt đầu tại thư mục ASTRA. Chạy `npm.cmd ci` lần đầu hoặc khi lockfile đổi.

```powershell
cd astra-frontend
npm.cmd ci
npm.cmd run dev -- --host 127.0.0.1
```

Mở URL Vite in ra, thường là [http://127.0.0.1:5173](http://127.0.0.1:5173). Frontend chuyển yêu cầu `/api` đến backend ở cổng 8000.

## 4. Tạo đề, xem PDF và tải xuống

1. Chọn **Soạn từ mẫu**, chọn Toán THPT và bắt đầu tạo đề.
2. Khi đề xong, mở **Xem trước PDF** để kiểm tra bố cục, công thức và hình. Kiểm tra đáp án trong tab **Xem đáp án**.
3. Bấm **Đã kiểm tra, phê duyệt bản này** để tải PDF, LaTeX hoặc đáp án JSON. Sau khi sửa câu, mở PDF của bản mới và duyệt lại.

Đề đã lưu nằm ở `runs/ui/<job-id>/de_thi.tex`. Báo cáo lượt tạo nằm ở `_internal/result.json` trong cùng thư mục job.

| Hiện tượng | Cách kiểm tra |
| --- | --- |
| `WinError 10048` | Cổng 8000 đã có tiến trình lắng nghe. Dùng backend đang chạy hoặc dừng backend cũ trước khi mở lại. |
| `spend_limit_exceeded` | Kiểm tra trần và sổ chi phí ASTRA trong `.env`. Request mới cần đủ ngân sách dự phòng trước khi được gửi. |
| `latex_compile_failed` | Mở `compile.log` trong tab **Xem trước PDF**, xem dòng báo lỗi đầu tiên rồi bấm **Thử biên dịch lại PDF** sau khi xử lý. Biên dịch lại dùng đề đã lưu. |

## Chạy CLI và kiểm tra nhanh

Chạy tại thư mục gốc ASTRA. Chọn thư mục đầu ra mới cho mỗi đề.

```powershell
.\.venv-win\Scripts\python.exe -m exam_baseline.baseline.cli --offline
.\.venv-win\Scripts\python.exe -m exam_baseline.thpt.cli --request examples/thpt/request.json --output runs/thpt/de_01
.\.venv-win\Scripts\python.exe -m exam_baseline.vact.cli --request examples/vact/request.json --output runs/vact/de_01
```

Lệnh đầu chạy dữ liệu mẫu. Hai lệnh còn lại dùng provider trong `.env` và lưu LaTeX, đáp án cùng báo cáo. [CLI Toán THPT](docs/guides/THPT_TOAN.md) · [CLI V-ACT](docs/guides/VACT.md) · [Tích hợp frontend và API](docs/integration/CONNECTED_THPT_UI.md) · [Cấu trúc thư mục](docs/CAU_TRUC_THU_MUC.md).
