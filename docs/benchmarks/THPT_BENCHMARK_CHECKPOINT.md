# THPT Benchmark Suite — Đặc tả Kiểm chứng & Checkpoint Bàn giao

Tài liệu này dành cho **Trọng (`phutrong-2208`)** và bất kỳ thành viên/AI nào tiếp nhận dở dang công việc xây dựng bộ benchmark khoa học cho ASTRA Toán THPT trên bộ 3 model **Google Gemini (`gemini-2.5-flash-lite`, `gemini-3.1-flash-lite`, `gemini-3.8-flash`)**.

- **Nhánh làm việc:** `feat/phutrong-2208/thpt-benchmark-suite` (cắt từ `origin/main` `c9badf5c`)
- **Worktree:** `C:\Users\ADMIN\OneDrive - KonTum01\Desktop\ASTRA.worktrees\phutrong-2208-thpt-benchmark`
- **Nguyên tắc bắt buộc (`AGENTS.md`):** không bao giờ bịa số liệu chạy live; replay chỉ kiểm plumbing/scorer; mọi kiểm chứng hoàn tất phải có bằng chứng lệnh chạy thật.

---

## 1. Bảng yêu cầu cần có để Trọng kiểm chứng kết quả (Acceptance Spec)

| # | Hạng mục yêu cầu | Tiêu chí kiểm chứng (Done = Verified) | Cách kiểm tra |
| :---: | :--- | :--- | :--- |
| **R1** | **Hỗ trợ `reasoning_effort` + bảng giá Gemini 2.5 / 3.1 / 3.8** | `Settings` đọc được `EXAM_REASONING_EFFORT` (`none/minimal/low/medium/high/xhigh`), `ChatCompletionsProvider` gửi đúng trường `reasoning_effort` trong JSON payload khi được bật (bỏ qua khi `None`). `thpt/metrics.py` có đủ đơn giá chuẩn của `gemini-2.5-flash-lite`, `gemini-3.1-flash-lite`, `gemini-3.8-flash` (và hàm quy đổi VND). | Unit tests trong `tests/providers/test_chat_completions.py` và `tests/thpt/test_metrics.py`. |
| **R2** | **Đủ 7 thước đo theo đúng thứ tự ưu tiên** | Báo cáo luôn hiển thị đúng thứ tự: **(1)** Tỉ lệ đúng template (cấu trúc + compile PDF), **(2)** Tỉ lệ tính toán chính xác (`x/34` đơn vị), **(3)** Tỉ lệ trích dẫn nội dung chính xác, **(4)** Tỉ lệ phát hiện lỗi của Validator (`Recall/Precision/False Alarm` + catch rate), **(5)** Compliance tài liệu tham khảo & prompt người dùng, **(6)** Chi phí theo tiền (USD & VND/đề, kèm `cost_coverage`), **(7)** Thời gian generate (median/max, tách `compute_s` và `wait_s`). | Unit tests scorer trong `tests/benchmarks/test_thpt_suite.py` xác nhận schema đầu ra, mẫu số không loại ca fail, thiếu nhãn chấm tay hiển thị `Chưa chấm`. |
| **R3** | **4 kiến trúc đối chứng cô lập 1 biến (OFAT)** | Runner `exam_baseline.benchmarks.thpt_suite` hỗ trợ đủ 4 kiến trúc trên cùng bộ prompt/ma trận cố định: `naive_chat` (ngu chat), `single_shot_rag` (ngu work), `astra_seq` (`composer_concurrency=1`), `astra_par` (`composer_concurrency=3`). | Replay E2E chạy qua cả 4 kiến trúc trên bộ 5 đề cố định trong `examples/benchmarks/thpt_gemini_suite.json`. |
| **R4** | **Trận đối đầu chứng minh tính ưu việt (Hero 2×2) + quét Model & Reasoning Effort** | Manifest mẫu định nghĩa rõ 3 thí nghiệm OFAT: (E1) Architecture trên `gemini-2.5-flash-lite`, (E2) Model (`2.5 → 3.1 → 3.8`) & `reasoning_effort`, (E3) Hero Comparison **`gemini-2.5-flash-lite (none/low) + ASTRA`** vs **`gemini-3.8-flash (high) + naive_chat / single_shot_rag`**. | Kiểm manifest bằng Pydantic schema + chạy dry-run/replay toàn ma trận. |
| **R5** | **Chịu lỗi Free Tier (`--resume` + tách thời gian chờ 429)** | Mỗi attempt lưu ngay vào `attempts.jsonl` và thư mục riêng; chạy lại với `--resume` bỏ qua các attempt đã `completed`/`failed_terminal` và chạy tiếp từ điểm dừng; ghi tách `api_compute_seconds` và `rate_limit_wait_seconds`. | Unit test cho `--resume` và phân tách `retry_after_seconds` trong `tests/benchmarks/test_thpt_suite.py`. |
| **R6** | **Bộ Validator Seeded Defect Suite cho Toán THPT** | Bộ `exam_baseline.benchmarks.thpt_validator` với các đề sạch + đề cố tình cài lỗi (sai đáp án P1/P2/P3, câu lạc chuyên đề, rò đáp án / lỗi cú pháp) mà gold không bao giờ lọt vào prompt; tính tự động `Recall`, `Precision`, `False Alarm`. | Chạy replay `python -m exam_baseline.benchmarks.thpt_validator --mode replay` + unit test anti-leakage. |
| **R7** | **Phiếu chấm mù CSV + Báo cáo Human-Readable + 3 biểu đồ SVG** | Lệnh xuất `grading_sheet.csv` (ẩn tên model/kiến trúc qua `blind_id`, giữ bản đồ đối chiếu riêng ở `blind_key.json`); lệnh tổng hợp đọc lại CSV đã điền để tự sinh `BENCHMARK_REPORT.md` (Executive Verdict, Scorecard 7 cột dạng `x/y (%)`, độ phủ chấm tay, Case Study) và **3 biểu đồ SVG** (Grouped Bar chất lượng, Pareto Chi phí vs Chất lượng, Stacked Bar thời gian/chi phí). | Test end-to-end tạo CSV → nạp CSV chấm giả lập trong test → kiểm tra nội dung Markdown và cả 3 file SVG hợp lệ. |
| **R8** | **Vệ sinh repo & chất lượng mã nguồn** | `pytest` pass, `ruff check` + `ruff format --check` pass, `scripts/check_repository.py` 0 lỗi, có log `tools/agent-log.sh`, không commit `.env` hay kết quả `runs/`. | Chạy trọn bộ kiểm tra trước khi chốt. |

---

## 2. Trạng thái Checkpoint (Cập nhật sau mỗi Milestone)

| Milestone | Mô tả | Trạng thái | Commit SHA | Bằng chứng kiểm tra |
| :---: | :--- | :---: | :---: | :--- |
| **M1** | Tạo worktree + Đặc tả kiểm chứng & file Checkpoint | **DONE** | `a459f2d` | Worktree tạo từ `origin/main` `c9badf5c` |
| **M2** | Thêm `EXAM_REASONING_EFFORT` & đơn giá Gemini 2.5 / 3.1 / 3.8 | **DONE** | *(pending commit)* | `pytest` 60/60 pass (`test_chat_completions`, `test_metrics`, `test_runtime`); Ruff check & format pass |
| **M3** | Xây dựng `thpt_suite` (4 kiến trúc + 5 đề cố định + `--resume` + template PDF check) | PENDING | — | — |
| **M4** | Xây dựng `thpt_validator` (Seeded Defect Suite cho Toán THPT) | PENDING | — | — |
| **M5** | Xây dựng bộ xuất phiếu chấm mù CSV + `BENCHMARK_REPORT.md` + 3 biểu đồ SVG | PENDING | — | — |
| **M6** | Chạy toàn bộ test, Ruff, `check_repository.py`, ghi `agent-log.sh` | PENDING | — | — |

---

## 3. Hướng dẫn tiếp nhận ngay nếu dừng giữa chừng

```powershell
# Di chuyển vào worktree riêng
cd "C:\Users\ADMIN\OneDrive - KonTum01\Desktop\ASTRA.worktrees\phutrong-2208-thpt-benchmark"
git status -sb
git log -n 8 --oneline --decorate
```

Đọc bảng **Mục 2** phía trên, tiếp tục từ Milestone đầu tiên có trạng thái `PENDING` hoặc `IN_PROGRESS`. Không chỉnh sửa worktree gốc `ASTRA`.
