# Backend lập kế hoạch MAS cho ASTRA

**Self-developed.** The MAS component was developed privately. The ASTRA
handoff publishes the obfuscated wheel, bundled planning data and integration
contract. The implementation source remains private.

Gói tích hợp dành cho ASTRA. Backend đọc yêu cầu, ma trận và tài liệu tham khảo,
gửi prompt qua callback do ASTRA cấp, rồi trả toàn bộ kế hoạch MAS dưới dạng
dữ liệu tuần tự hóa được thành JSON. ASTRA tự chọn model và giữ thông tin xác
thực trong callback. Tiến trình lập kế hoạch chặn kết nối mạng và phân giải
tên miền ở tầng Python. Hai tiến trình trao đổi qua stdin/stdout. Gói dùng
wheel CPython 3.11 cho macOS và Windows.

## Tóm tắt cách đóng gói

- Lấy phần đọc input và lập kế hoạch từ snapshot nguồn nội bộ. Chạy **BLA 3.3.2**
  ở chế độ `bankrupt` trên cả lõi và adapter ASTRA, rồi biên dịch sang bytecode
  CPython 3.11. Bản giao có 0 tệp nguồn Python.
- Wheel `astra-mas` tách riêng khỏi ứng dụng ASTRA. Cài cùng app hiện tại và
  import `astra_mas`. Gói chứa bộ đọc, planner, prompt và 61 tệp dữ liệu lập
  kế hoạch. Các bước sau khi trả plan nằm ngoài phạm vi gói.
- ASTRA gọi `prepare_plan()`, cấp callback LLM và có thể điều chỉnh
  `MasLimits`. Hàm trả toàn bộ kế hoạch cùng `state` và các vướng mắc.
- Thư mục này chứa wheel, bảng phiên bản phụ thuộc, hợp đồng I/O, manifest
  dữ liệu và sơ đồ ingest dưới dạng Mermaid, LaTeX và PDF đã render.

## Cài và tích hợp

Dùng CPython 3.11 trong môi trường ASTRA. Chạy lệnh từ `docs/mas` trong
checkout GitHub hoặc từ thư mục giải nén ZIP. Nếu tải từng tệp, đặt
[wheel](astra_mas-0.1.1-cp311-none-any.whl) và
[`requirements-mas-tested.txt`](requirements-mas-tested.txt) cùng thư mục.

```sh
python -m pip install --upgrade ./astra_mas-0.1.1-cp311-none-any.whl -c requirements-mas-tested.txt
```

Tích hợp tại điểm backend chọn, truyền một hàm async nhận `MasPrompt` và trả
văn bản JSON từ model. `MasPrompt` có `recipe`, `system`, `user` và `images`
(PNG bytes). Adapter LLM của ASTRA tự chuyển sang định dạng nhà cung cấp.

```python
from pathlib import Path

from astra_mas import MasFile, MasInput, MasLimits, MasPrompt, prepare_plan


async def complete(prompt: MasPrompt) -> str:
    return await astra_llm.complete_text(  # Thay bằng adapter LLM của ASTRA.
        system=prompt.system,
        user=prompt.user,
        images=prompt.images,
    )


matrix = Path("ma-tran.csv")
result = await prepare_plan(
    MasInput(
        exam_type="THPTQG",
        subject="Toán",
        grade=12,
        instruction="Chỉ dùng nội dung đạo hàm.",
        matrix=MasFile(filename=matrix.name, data=matrix.read_bytes()),
    ),
    complete,
    limits=MasLimits(max_file_bytes=4 * 1024**2, max_plan_bytes=2 * 1024**2),
)
```

`result["plan"]` là envelope MAS nguyên vẹn, gồm scope, inputs.shape, cells, revisions
và findings. Đọc thêm `result["state"]` và `result["gaps"]` để xử lý các trường
hợp còn thiếu bằng chứng. Khi ô còn thiếu chủ đề hoặc yêu cầu, trạng thái ngoài
là `blocked` và `gaps` ghi từng địa chỉ. Envelope MAS và revision vẫn được
giữ nguyên. Các lỗi đầu vào, callback và giới hạn kích thước có
`MasError.code`; vượt giới hạn đầu ra trả mã lỗi thay vì cắt JSON.


## Toolchain cần cài

Cài các chương trình trên **máy chạy backend ASTRA**. Cấu hình `PATH` của
chính terminal hoặc tiến trình khởi chạy ASTRA phải nhìn thấy các executable.

| Thành phần | Khi cần | MAS dùng để làm gì |
| --- | --- | --- |
| **CPython 3.11 và pip** | Mọi lượt chạy | Cài wheel `cp311` và phụ thuộc Python theo `requirements-mas-tested.txt`. |
| **Poppler** | Đầu vào PDF | `pdfinfo` đếm trang, `pdftotext` trích văn bản, `pdftoppm` tạo ảnh trang, `pdffonts` và `pdfimages` hỗ trợ đánh giá nội dung PDF. |
| **Pandoc** | DOCX có công thức Word | Chuyển nội dung và công thức OMML. Khi máy thiếu Pandoc, trình đọc dùng văn bản gốc và báo phần công thức bị mất. Với tệp `.doc` cũ, lưu lại thành `.docx` trước khi đưa vào. |
| **LLM hỗ trợ ảnh** | Ảnh, hình nhúng hoặc trang quét cần đọc | Callback ASTRA nhận ảnh PNG và gửi chúng sang model có khả năng đọc ảnh. |
| **Tesseract với `vie` và `eng`** | Tùy chọn | OCR cục bộ trên đường đọc ảnh có hỗ trợ dự phòng, với kết quả vẫn được đánh dấu đọc một phần. |
| **XeLaTeX** | Khi biên dịch lại sơ đồ | Tạo lại PDF từ tệp LaTeX và bản vẽ vector đi kèm. |

Với yêu cầu bằng chữ, TXT, CSV hoặc XLSX, cài wheel và các phụ thuộc Python
là đủ cho phần đọc nguồn của các định dạng này. Khi dùng PDF hoặc DOCX có
công thức, cài thêm các công cụ trong bảng.

### macOS

```sh
brew install pandoc poppler
# Tùy chọn OCR cục bộ
brew install tesseract tesseract-lang
```

Nguồn cài đặt. [Pandoc](https://pandoc.org/installing.html#macos) ·
[Poppler](https://formulae.brew.sh/formula/poppler) ·
[Ngôn ngữ OCR](https://formulae.brew.sh/formula/tesseract-lang)

### Windows

1. Cài Pandoc bằng MSI chính thức hoặc lệnh PowerShell
   `winget install --source winget --exact --id JohnMacFarlane.Pandoc`.
   [Hướng dẫn Pandoc](https://pandoc.org/installing.html#windows)
2. Giải nén Poppler cho Windows và thêm thư mục chứa `pdfinfo.exe` cùng các
   công cụ Poppler khác vào `PATH`. [Bản Poppler cho Windows](https://github.com/oschwartz10612/poppler-windows)
3. Nếu dùng OCR cục bộ, cài Tesseract cùng dữ liệu `vie` và `eng` vào
   `tessdata` của bản cài, rồi thêm thư mục chứa `tesseract.exe` vào `PATH`.
   [Hướng dẫn Tesseract](https://tesseract-ocr.github.io/tessdoc/Installation.html#windows)

Mở lại terminal hoặc tiến trình ASTRA sau khi đổi `PATH`.

### Kiểm tra trong môi trường chạy ASTRA

Chạy các lệnh tương ứng với loại tệp sẽ dùng, trên terminal chạy backend.

```text
python --version
pandoc --version
pdfinfo -v
pdftotext -v
pdftoppm -v
pdffonts -v
pdfimages -v
tesseract --list-langs
```

Python phải trả về phiên bản 3.11. Khi bật OCR, danh sách ngôn ngữ cần có
`vie` và `eng`.

## Hợp đồng I/O

Điểm vào là `await prepare_plan(input: MasInput, complete: MasCompletion, *, limits: MasLimits | None = None) -> MasResult`.

### Đầu vào từ ASTRA

| Trường `MasInput` | Kiểu | Ý nghĩa |
| --- | --- | --- |
| `exam_type` | `str` | Mã định dạng trong registry MAS, ví dụ `THPTQG` |
| `subject` | `str` | Tên môn học, ví dụ `Toán` |
| `grade` | `int` | Lớp từ 1 đến 12 |
| `instruction` | `str` | Phạm vi và yêu cầu. Mặc định là chuỗi rỗng |
| `matrix` | `MasFile \| None` | Ma trận tùy chọn. Mặc định là `None` |
| `materials` | `tuple[MasFile, ...]` | Các tài liệu tham khảo. Mặc định là tuple rỗng |

`MasFile.filename` là tên tệp có phần mở rộng. `MasFile.data` là nội dung
`bytes` gốc. Nếu ASTRA nhận tải lên ở dạng Base64, giải mã trước khi gọi.
Ma trận có thể là một bảng CSV, XLSX hoặc DOCX đọc được bởi MAS. Đầu vào tham
khảo có thể là văn bản, tài liệu Office, PDF hoặc ảnh trong các định dạng mà
bộ chuyển đổi MAS hỗ trợ.

### I/O của callback LLM

| Trường `MasPrompt` | Kiểu | Ý nghĩa |
| --- | --- | --- |
| `recipe` | `str` | Tên tác vụ MAS để ASTRA theo dõi hoặc chọn model |
| `system` | `str` | Chỉ dẫn của tác vụ |
| `user` | `str` | Payload dữ liệu đã được MAS đóng khung |
| `images` | `tuple[bytes, ...]` | Ảnh PNG theo thứ tự prompt, hoặc tuple rỗng |

`MasCompletion = Callable[[MasPrompt], Awaitable[str]]`. Trả nguyên văn JSON
do model sinh theo schema trong prompt. Một kế hoạch có thể phát sinh nhiều
lượt gọi, chẳng hạn đọc ảnh, tóm tắt nguồn, xác định phạm vi và lập các phần.

### Đầu ra về ASTRA

| Trường `MasResult` | Kiểu | Ý nghĩa |
| --- | --- | --- |
| `schema_version` | `"astra-mas-plan-v1"` | Phiên bản hợp đồng của gói |
| `state` | `"ready" \| "blocked"` | `ready` khi planner sẵn sàng và các ô có chủ đề, yêu cầu cần đạt. `blocked` giữ bản ứng viên và các mục cần xử lý. Cảnh báo nguồn có thể đi kèm `ready`. |
| `plan` | `dict` | Toàn bộ envelope MAS v2 với `inputs.shape`, `scope`, `cells`, `groups`, `delivery` và revision |
| `gaps` | `list[dict]` | Cảnh báo của MAS, cùng mã `mas_unfilled_cells` và địa chỉ khi còn ô thiếu nội dung |

Mỗi ô có địa chỉ `(part_id, idx, sub)`. Dùng `plan.plan_revision` để gắn kết
quả với đúng phiên bản. Khi cần lưu dạng chuỗi, dùng
`json.dumps(result, ensure_ascii=False)`.

### Lỗi có kiểu

- Đầu vào hoặc giới hạn nguồn: `mas_file_count_limit`, `mas_file_bytes_limit`,
  `mas_total_bytes_limit`, `mas_instruction_limit` và mã `small_input_*` từ MAS.
- Callback: `mas_llm_failed` hoặc `mas_llm_reply_invalid`.
- Kích thước và thời gian: `mas_prompt_chars_limit`, `mas_reply_chars_limit`,
  `mas_plan_bytes_limit`, `mas_timeout`.
- Cài đặt và tiến trình: `mas_bundle_missing`, `mas_bundle_invalid`,
  `mas_python_version_mismatch`, `mas_runtime_failed`, `mas_protocol_error`.

## Giới hạn theo lượt

| Cấu hình | Mặc định | Đơn vị |
| --- | ---: | --- |
| `max_files`, `max_pages`, `max_images` | 10 mỗi loại | Số lượng |
| `max_file_bytes`, `max_total_bytes` | 8 MiB, 16 MiB | Byte |
| `max_source_chars`, `max_total_source_chars` | 30.000, 60.000 | Ký tự |
| `max_instruction_chars` | 20.000 | Ký tự |
| `max_prompt_chars` | 200.000 | Ký tự system + user mỗi lượt gọi |
| `max_reply_chars` | 400.000 | Ký tự phản hồi mỗi lượt gọi |
| `max_plan_bytes` | 4 MiB | Byte UTF-8 của kết quả JSON |
| `max_run_seconds` | 600 | Giây |

Các giới hạn nguồn chỉnh được trong phạm vi bộ đọc MAS hiện hành, với giá trị
mặc định ở mức trần của bộ đọc.

## Minh chứng công việc ngoài repo ASTRA

| Phạm vi đo | Số liệu |
| --- | --- |
| Lõi lập kế hoạch và các phụ thuộc thực sự đóng gói | Khoảng **25.700 dòng nguồn** trước BLA |
| Adapter nhận input, trao đổi prompt và trả plan | Khoảng **400 dòng nguồn** trước BLA |
| Lịch sử phát triển lõi trong repo riêng | **100 commit** chạm 16 mô-đun trung tâm về đọc tệp, ma trận, xác định phạm vi và lập kế hoạch |
| Tích hợp riêng cho ASTRA | **5 commit** về adapter, build, tài liệu, kiểm thử và đóng gói wheel 0.1.1 |

Số dòng đếm các dòng nguồn không trống, gồm chú thích, trước khi BLA chèn mã
làm rối. Số commit loại merge và đếm mỗi commit một lần trong từng phạm vi.
Con số của lõi phản ánh lịch sử phát triển đã có. PR này ghi lại phần tích hợp
dùng cho bài nộp.

## Phạm vi bàn giao

Wheel chứa bytecode làm rối bằng BLA và 61 tệp dữ liệu phiên bản hóa.
[`DATA-MANIFEST.json`](DATA-MANIFEST.json) ghi SHA-256 từng tệp dữ liệu trong wheel.
Bytecode có thể dịch ngược, prompt có thể đọc từ callback và dữ liệu JSON có
thể trích xuất.

SHA-256 của wheel

```text
66fe85d7fd231c7f54dff5c29c1e6707d5d5e5c18adfbc378dec0c1210ef9205
```

## Đặc tả luồng ingest

[Sơ đồ luồng MAS](ASTRA_MAS_INGEST_FLOW.md) mô tả ba chặng của wheel 0.1.1.
Chặng A kiểm tra giới hạn đầu vào và đọc ma trận, tài liệu. Chặng B xác định
phạm vi, lập kế hoạch theo địa chỉ ô và kiểm tra đầu ra. Chặng C mô tả từng
lượt callback LLM, kết quả `ready` hoặc `blocked` và lỗi có mã.

- `ASTRA_MAS_INGEST_FLOW.md` chứa ba sơ đồ Mermaid.
- [`ASTRA_MAS_INGEST_SPEC.pdf`](ASTRA_MAS_INGEST_SPEC.pdf) là bản đặc tả ba trang.
- [`ASTRA_MAS_INGEST_SPEC.tex`](ASTRA_MAS_INGEST_SPEC.tex) dùng hình vector ba trang
  [`ASTRA_MAS_INGEST_CHART.pdf`](ASTRA_MAS_INGEST_CHART.pdf). Có thể biên dịch bằng
  `xelatex ASTRA_MAS_INGEST_SPEC.tex` trong thư mục chứa hai tệp này.
