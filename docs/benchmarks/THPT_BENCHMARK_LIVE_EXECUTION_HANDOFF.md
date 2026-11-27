# Handoff Chạy Thử Nghiệm Live — THPT Math Scientific Benchmark (Gemini 2.5 / 3.1 / 3.8)

Tài liệu bàn giao cho **bên tiếp nhận (thành viên hoặc AI agent tiếp theo)** thực hiện chạy thực nghiệm **Live** trên Google Gemini API, chấm mù (blind grading), và xuất báo cáo + biểu đồ cuối cùng cho **Trọng (`phutrong-2208`)**.

- **Repository:** `https://github.com/ndmhuy/ASTRA`
- **Nhánh làm việc (đã sync `origin/main` và đã push):** `feat/phutrong-2208/thpt-benchmark-suite`
- **Đặc tả kiểm chứng & lịch sử xây dựng (M1–M6):** [THPT_BENCHMARK_CHECKPOINT.md](THPT_BENCHMARK_CHECKPOINT.md)
- **Nguyên tắc bắt buộc (`AGENTS.md`):**
  1. **KHÔNG commit/push lên `main`**, KHÔNG commit `.env`, API key, hay thư mục kết quả `runs/`.
  2. **KHÔNG bịa số liệu**, KHÔNG tự chấm điểm hộ con người, KHÔNG loại các ca lỗi/429/hỏng JSON khỏi mẫu số.
  3. Chế độ `--mode replay` chỉ để kiểm tra đường ống offline; chỉ số liệu từ `--mode live` + CSV chấm tay của Trọng mới được đưa vào kết luận khoa học.
  4. Ghi log phiên AI bằng `tools/agent-log.sh` nếu có chỉnh sửa code/tài liệu trên nhánh.

---

## 1. Phạm vi đã làm xong (Ready to Run)

Toàn bộ hạ tầng benchmark khoa học đã được xây dựng, kiểm thử (`pytest` + `ruff` + `scripts/check_repository.py` + E2E CLI replay 65/65) và đẩy lên nhánh `feat/phutrong-2208/thpt-benchmark-suite`:

1. **Hỗ trợ `EXAM_REASONING_EFFORT` & đơn giá chuẩn Gemini 2.5 / 3.1 / 3.8** (`src/exam_baseline/config.py`, `providers/chat_completions.py`, `thpt/metrics.py`, `thpt/runtime.py`):
   - `gemini-2.5-flash-lite`: `$0.10 / $0.40` per 1M tokens — hỗ trợ `reasoning_effort`: `none`, `low`, `medium`, `high`.
   - `gemini-3.1-flash-lite`: `$0.25 / $1.50` per 1M tokens — hỗ trợ `reasoning_effort`: `low`, `medium`, `high`.
   - `gemini-3.8-flash`: `$0.75 / $3.75` per 1M tokens (giá khuyến mãi đến 31/12/2026) — hỗ trợ `reasoning_effort`: `low`, `medium`, `high` (**không** dùng `none` hay `minimal`).
   - Tự động quy đổi sang VNĐ (`usd_to_vnd_rate = 26,000`), tách riêng `api_compute_seconds` và `rate_limit_wait_seconds`.
2. **Runner OFAT 4 kiến trúc (`exam_baseline.benchmarks.thpt_suite`)** + manifest chuẩn [examples/benchmarks/thpt_gemini_suite.json](../../examples/benchmarks/thpt_gemini_suite.json):
   - **5 đề THPT cố định (`case_01_general` .. `case_05_cognitive_mix`)** dùng chung một bộ RAG/ma trận đóng băng (`_prepared/<case_id>_request.json`) cho mọi kiến trúc có RAG để cô lập tuyệt đối 1 biến (OFAT).
   - **4 kiến trúc:** `naive_chat` (ngu chat), `single_shot_rag` (ngu work), `astra_seq` (tuần tự, `concurrency=1`), `astra_par` (song song, `concurrency=3`).
   - **3 nhóm thí nghiệm:**
     - `E1_architecture`: So 4 kiến trúc trên cùng `gemini-2.5-flash-lite (low)`.
     - `E2_model_reasoning`: Quét `2.5 (none/medium) → 3.1 (low/medium) → 3.8 (low/high)` trên cùng `astra_par`.
     - `E3_hero_comparison`: **Trận đối đầu trọng tâm** — `gemini-2.5-flash-lite (low) + astra_par` vs `gemini-3.8-flash (high) + naive_chat` và `gemini-3.8-flash (high) + single_shot_rag`.
   - **Chống đứt quãng Free Tier:** mỗi lần chạy lưu ngay vào `attempts.jsonl` và thư mục gọn `r/<hash10>/` (tránh lỗi Windows `MAX_PATH` 260 ký tự và chống lộ tên model khi chấm mù); chạy tiếp bằng `--resume` hoặc chạy lại riêng các ca lỗi bằng `--resume --retry-failed`.
3. **Validator Seeded Defect Suite (`exam_baseline.benchmarks.thpt_validator`)** + dataset [examples/benchmarks/thpt_validator_suite.json](../../examples/benchmarks/thpt_validator_suite.json):
   - 5 câu sạch + 5 lỗi cài sẵn (`wrong_p1_key`, `wrong_p2_statement`, `wrong_p3_calculation`, `scope_drift`, `answer_leakage`). `gold` không bao giờ lọt vào prompt của Blind Solver hay Reviewer.
4. **Phiếu chấm mù CSV + Báo cáo 7 tiêu chí + 3 biểu đồ SVG (`exam_baseline.benchmarks.thpt_report`)**:
   - Xuất `grading_sheet.csv` (UTF-8-SIG mở trực tiếp trong Excel/Google Sheets, đúng 34 đơn vị/đề = 12 P1 + 16 ý P2 + 6 P3, ẩn hoàn toàn tên model & kiến trúc bằng `blind_id`, bảng giải mã giữ riêng ở `blind_key.json`).
   - Tổng hợp `BENCHMARK_REPORT.md` theo đúng **7 tiêu chí ưu tiên** + **3 biểu đồ SVG** (`hero_quality_bars.svg`, `pareto_cost_vs_quality.svg`, `latency_cost_breakdown.svg`).

---

## 2. Chuẩn bị môi trường trước khi chạy Live

### Bước 2.1 — Checkout nhánh mới nhất

```powershell
git fetch --all
git switch feat/phutrong-2208/thpt-benchmark-suite
git pull --ff-only
```

Nếu dùng worktree mới cạnh repo gốc:

```powershell
git worktree add ../ASTRA.worktrees/benchmark-live feat/phutrong-2208/thpt-benchmark-suite
```

### Bước 2.2 — Cài Python & kiểm tra trình biên dịch LaTeX (để chấm Metric #1 — compile PDF)

```powershell
# Kích hoạt venv của máy (hoặc tạo venv và pip install -e ".[dev]")
python -c "import exam_baseline.benchmarks.thpt_suite as s; print(s.__file__)"

# Kiểm tra đã có XeLaTeX / LuaLaTeX / Tectonic chưa (nếu chưa, cài Tectonic portable)
python -c "from exam_baseline.pipeline.rendering.compiler import find_compiler; print(find_compiler())"
# Nếu in None:
python scripts/install_latex_compiler.py
```

### Bước 2.3 — Cấu hình `.env` (TUYỆT ĐỐI KHÔNG COMMIT)

Tạo hoặc cập nhật `.env` ở thư mục chạy lệnh với khóa Google AI Studio của Trọng:

```env
EXAM_PROVIDER=chat_completions
EXAM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
EXAM_API_KEY=<GEMINI_API_KEY_CUA_TRONG>
EXAM_MODEL=gemini-2.5-flash-lite
EXAM_TOKEN_LIMIT_FIELD=max_tokens
EXAM_MAX_OUTPUT_TOKENS=8192
EXAM_TIMEOUT_SECONDS=120
EXAM_RESPONSE_FORMAT=json_object
EXAM_RAG_CORPUS_REF=8b8fb7b09182b3d9d1eee0b95818027f52ab004d
```

> **Lưu ý về RAG Corpus:** Đảm bảo máy có `git` trên `PATH` (hoặc truyền `--rag-pack-dir <path>` nếu chạy từ release pack) và commit corpus `8b8fb7b09182b3d9d1eee0b95818027f52ab004d` tồn tại trong git object store (`git cat-file -e 8b8fb7b09182b3d9d1eee0b95818027f52ab004d`).

---

## 3. Quy trình chạy thử nghiệm Live (Theo đúng thứ tự tiết kiệm quota nhất)

> **Mẹo kiểm soát Free Tier / RPM:** Luôn chạy từ nhỏ đến lớn (`Bước 0 → 1 → 2 → 3`). Nếu gặp HTTP 429 hoặc hết quota ngày, **không xóa thư mục `--output`** — chỉ cần chạy lại đúng lệnh cũ thêm `--resume --retry-failed`.

### Bước 0 — Kiểm tra nhanh đường ống offline (0 đồng, ~5 giây)

```powershell
python -m exam_baseline.benchmarks.thpt_suite `
  --manifest examples/benchmarks/thpt_gemini_suite.json `
  --experiment E3_hero_comparison `
  --output runs/smoke-check `
  --mode replay `
  --compile auto
```

Xác nhận `completed_attempts == 15` và nếu đã cài Tectonic/XeLaTeX thì kiểm `pdf_compile_status == "passed"` cho các ca ASTRA.

### Bước 1 — Chạy kiểm định Validator (10 câu đơn, tốn rất ít token)

Nên chạy trước trên cả 3 model (hoặc tối thiểu `gemini-2.5-flash-lite` ở `low`) để có ngay số liệu **Metric #4 (Recall / Precision / False Alarm)**:

```powershell
python -m exam_baseline.benchmarks.thpt_validator `
  --dataset examples/benchmarks/thpt_validator_suite.json `
  --output runs/live-validator-25-low `
  --mode live `
  --model gemini-2.5-flash-lite `
  --reasoning-effort low

# (Tùy chọn đối chiếu thêm 3.1 và 3.8)
python -m exam_baseline.benchmarks.thpt_validator `
  --dataset examples/benchmarks/thpt_validator_suite.json `
  --output runs/live-validator-31-low `
  --mode live `
  --model gemini-3.1-flash-lite `
  --reasoning-effort low

python -m exam_baseline.benchmarks.thpt_validator `
  --dataset examples/benchmarks/thpt_validator_suite.json `
  --output runs/live-validator-38-high `
  --mode live `
  --model gemini-3.8-flash `
  --reasoning-effort high
```

### Bước 2 — Chạy trận đối đầu trọng tâm `E3_hero_comparison` (15 đề = 3 cấu hình × 5 đề)

Chứng minh giả thuyết chính: **`gemini-2.5-flash-lite (low) + ASTRA Song song`** vượt **`gemini-3.8-flash (high) + Ngu chat`** (và **`Ngu work`**):

```powershell
python -m exam_baseline.benchmarks.thpt_suite `
  --manifest examples/benchmarks/thpt_gemini_suite.json `
  --experiment E3_hero_comparison `
  --output runs/live-thpt-suite `
  --mode live `
  --compile auto `
  --inter-attempt-sleep 15
```

- Nếu bị ngắt giữa chừng (429 / timeout / hết quota ngày), tiếp tục từ điểm dừng bằng:

```powershell
python -m exam_baseline.benchmarks.thpt_suite `
  --manifest examples/benchmarks/thpt_gemini_suite.json `
  --experiment E3_hero_comparison `
  --output runs/live-thpt-suite `
  --mode live `
  --compile auto `
  --inter-attempt-sleep 15 `
  --resume `
  --retry-failed
```

### Bước 3 — Chạy nối tiếp `E1_architecture` và `E2_model_reasoning` vào CÙNG thư mục `runs/live-thpt-suite`

Dùng chung `--output runs/live-thpt-suite --resume` để mọi đề trong `E1`, `E2`, `E3` dùng **đúng cùng bộ RAG đóng băng `_prepared/`** và gộp thẳng vào một bảng `BENCHMARK_REPORT.md` duy nhất:

```powershell
# E1: Cô lập 4 kiến trúc trên gemini-2.5-flash-lite (low)
python -m exam_baseline.benchmarks.thpt_suite `
  --manifest examples/benchmarks/thpt_gemini_suite.json `
  --experiment E1_architecture `
  --output runs/live-thpt-suite `
  --mode live `
  --compile auto `
  --inter-attempt-sleep 15 `
  --resume

# E2: Cô lập Model (2.5 -> 3.1 -> 3.8) & Reasoning Effort trên ASTRA Song song
python -m exam_baseline.benchmarks.thpt_suite `
  --manifest examples/benchmarks/thpt_gemini_suite.json `
  --experiment E2_model_reasoning `
  --output runs/live-thpt-suite `
  --mode live `
  --compile auto `
  --inter-attempt-sleep 15 `
  --resume
```

*(Mẹo: Có thể lọc từng cấu hình lẻ bằng `--run-id <id>` lặp lại nhiều lần nếu muốn chia nhỏ theo từng ngày quota).*

---

## 4. Quy trình Chấm mù (Blind Grading) & Xuất Báo cáo cuối

### Bước 4.1 — Xuất phiếu chấm mù CSV cho Trọng

```powershell
python -m exam_baseline.benchmarks.thpt_report export-grading-sheet `
  --suite-dir runs/live-thpt-suite
```

File đầu ra:
- `runs/live-thpt-suite/grading_sheet.csv`: Mở bằng Excel hoặc Google Sheets (không hề có tên model hay kiến trúc).
- `runs/live-thpt-suite/blind_key.json`: **Không mở trước khi chấm xong** để giữ tính khách quan khoa học.

### Bước 4.2 — Quy ước điền `grading_sheet.csv` (chỉ điền `1` hoặc `0`)

Mỗi đề có đúng **34 dòng đơn vị** (12 câu P1 + 16 ý `a/b/c/d` của 4 câu P2 + 6 câu P3):
- `math_ok`: `1` nếu đề hợp lệ, không mơ hồ và đáp án/lời giải tính đúng; `0` nếu sai phép tính, thiếu điều kiện hoặc vô nghiệm sai.
- `citation_ok`: `1` nếu nội dung đúng kiến thức/nguồn SGK được trích dẫn; `0` nếu bịa nguồn hoặc trích dẫn sai.
- `scope_ok`: `1` nếu đúng chuyên đề/phạm vi prompt của giáo viên & không chép nguyên văn câu mẫu; `0` nếu lạc chuyên đề hoặc vi phạm yêu cầu đề bài.
- `defect_caught_by_validator`: (tùy chọn trên các ca có sửa lỗi) `1` nếu Validator bắt trúng lỗi cần sửa, `0` nếu bỏ lọt lỗi nghiêm trọng.
- `note`: Ghi chú ngắn lỗi nổi bật (nếu có) để trích vào Case Study.

> Để đọc bài làm tương ứng với `BLIND-001`, mở file trong cột `stem_preview` (hoặc tra thư mục `r/<hash10>/de_thi.pdf`, `loi_giai.md`, `raw_response.txt`).

### Bước 4.3 — Tổng hợp Báo cáo Human-Readable + 3 Biểu đồ SVG

Sau khi lưu file CSV đã chấm (ví dụ `runs/live-thpt-suite/grading_sheet_filled.csv`):

```powershell
python -m exam_baseline.benchmarks.thpt_report build-report `
  --suite-dir runs/live-thpt-suite `
  --grading-csv runs/live-thpt-suite/grading_sheet_filled.csv `
  --blind-key runs/live-thpt-suite/blind_key.json `
  --validator-metrics runs/live-validator-25-low/validator_metrics.json
```

Sản phẩm tự sinh ra trong `runs/live-thpt-suite/`:
- `BENCHMARK_REPORT.md` — Executive Verdict (Hero Test), Scorecard 7 cột đúng thứ tự ưu tiên dạng `x/y (%)`, tách riêng E1/E2/E3, kết quả Validator Seeded Suite, Case Study từ artifact thật.
- `charts/hero_quality_bars.svg` — Biểu đồ cột nhóm 5 thước đo chất lượng ưu tiên.
- `charts/pareto_cost_vs_quality.svg` — Biểu đồ Pareto Chi phí (VNĐ/đề) vs Chất lượng tổng hợp (có đường mục tiêu `≤ 2,000 VNĐ`).
- `charts/latency_cost_breakdown.svg` — Biểu đồ cột chồng tách `API Compute (s)` vs `Chờ 429 (s)` + chi phí VNĐ.
- `report_summary.json` — Số liệu tổng hợp dạng JSON cho slide/báo cáo nhóm.

---

## 5. Xử lý sự cố thường gặp khi chạy Live

1. **`HTTP 400 provider_bad_request` với `gemini-3.8-flash`:** Kiểm tra không truyền `reasoning_effort=none` hoặc `minimal` cho `gemini-3.8-flash` (manifest mẫu đã cấu hình đúng `low`/`high`).
2. **`HTTP 429 provider_rate_limited` liên tục:** Tăng `--inter-attempt-sleep 20` hoặc `30`. Thời gian chờ 429 được tự động tách vào `rate_limit_wait_seconds`, không làm méo `api_compute_seconds`.
3. **`retrieval_gap` khi lập kế hoạch RAG:** Kiểm tra `git` đã nằm trong `PATH` chưa, hoặc chạy thử `git cat-file -e 8b8fb7b09182b3d9d1eee0b95818027f52ab004d`. Nếu thiếu object RAG, fetch từ remote chứa corpus hoặc truyền `--rag-pack-dir`.
4. **`pdf_compile_status: skipped_no_compiler`:** Cài Tectonic portable bằng `python scripts/install_latex_compiler.py` hoặc truyền `EXAM_LATEX_COMPILER` trong `.env`, rồi chạy với `--compile require` nếu muốn bắt buộc có PDF.

---

## 6. Checklist nghiệm thu kết quả Live (Trước khi trình bày / gộp báo cáo)

- [ ] `BENCHMARK_REPORT.md` ghi rõ `Chế độ chạy: LIVE` (không còn cảnh báo `REPLAY OFFLINE`).
- [ ] Mẫu số giữ nguyên toàn bộ số lần chạy thực tế (`completed + failed`), không xóa ca fail.
- [ ] Độ phủ chấm tay mù ghi rõ `x/y đơn vị (%)`, ưu tiên đạt 100% cho trận `E3_hero_comparison`.
- [ ] Có đầy đủ 3 biểu đồ SVG mở xem rõ chữ, đúng đường mục tiêu `≤ 2,000 VNĐ/đề`.
- [ ] Có số liệu `validator_metrics.json` live (Recall / Precision / False Alarm) ít nhất trên `gemini-2.5-flash-lite`.
- [ ] Thư mục `runs/` và `.env` **không** được commit vào Git (`python scripts/check_repository.py` trả `0 issues`).
