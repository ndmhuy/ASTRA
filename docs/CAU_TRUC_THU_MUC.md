# Tác dụng của từng thư mục

```text
ASTRA/
├── src/exam_baseline/       Mã nguồn backend
│   ├── providers/          Các adapter gọi dịch vụ model và mock offline
│   ├── prompts/            Nội dung prompt theo phiên bản
│   └── fixtures/           Request mẫu và đề mock cố định
├── tests/                  Tests tự động, không gọi model thật
├── scripts/                Script kiểm tra server và file chuẩn bị đưa lên Git
├── docs/                   Tài liệu mô tả cấu trúc thư mục
├── .github/workflows/      Cấu hình CI chạy kiểm tra khi push hoặc tạo pull request
├── inputs/                 JSON đầu vào cá nhân, tạo khi xuất ví dụ
├── runs/                   Kết quả từng lần chạy: đề, phản hồi JSON và báo cáo
└── .venv-win/              Môi trường Python cùng các thư viện đã cài
```

`inputs/`, `runs/` và `.venv-win/` là thư mục local, không đưa lên Git. Chúng có thể chưa
tồn tại trong một bản clone mới. `.git/` do Git quản lý để lưu lịch sử và trạng thái repo.

## Các module chính trong `src/exam_baseline/`

| File | Tác dụng |
| --- | --- |
| `models.py` | Schema ma trận, ngân hàng câu hỏi, đề thi và phản hồi |
| `contracts.py` | Interface cho provider, agent, context loader và recorder |
| `config.py` | Đọc cấu hình môi trường và tạo cấu hình offline |
| `bootstrap.py` | Ghép các thành phần, quản lý vòng đời HTTP client |
| `agent.py` | Gọi model một lần và đọc đề trả về theo schema |
| `prompting.py` | Ghép prompt, dữ liệu đầu vào và schema đầu ra |
| `context.py` | Chuẩn bị dữ liệu JSON và cảnh báo ngân hàng câu hỏi |
| `validation.py` | Kiểm tra đề với ma trận bằng Python |
| `evaluation.py` | Tổng hợp thời gian, token, chi phí ước lượng và kết quả kiểm tra |
| `service.py` | Điều phối toàn bộ quy trình sinh đề |
| `api.py` | Khai báo endpoint và dependency FastAPI |
| `http_status.py` | Chuyển trạng thái kết quả thành HTTP status |
| `main.py` | Điểm khởi động server |
| `cli.py` | Chạy offline hoặc gửi request tới server, lưu kết quả |
| `reporting.py` | Tạo bản kết quả Markdown dễ đọc |
| `samples.py` | Đọc request mẫu dùng chung |

## Các file ở thư mục gốc

| File | Tác dụng |
| --- | --- |
| `README.md` | Các lệnh cài đặt và chạy dự án |
| `pyproject.toml` | Khai báo package, dependencies, CLI và cấu hình công cụ |
| `requirements-tested.txt` | Phiên bản dependencies đã dùng khi kiểm chứng |
| `.env.example` | Mẫu cấu hình không chứa key thật |
| `.env` | Cấu hình và key riêng trên máy, không đưa lên Git |
| `.gitignore` | Loại file riêng tư và file sinh tự động khỏi Git |
| `.gitattributes` | Quy định cách Git xử lý định dạng dòng |
| `.editorconfig` | Quy định encoding, thụt dòng và định dạng khi sửa file |

Các thư mục như `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `build/`, `dist/` có thể
được công cụ tạo lại khi chạy; chúng không thuộc mã nguồn cần commit.
