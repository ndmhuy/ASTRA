> **Quyết định sử dụng hiện hành (06/11/2026):** [USABILITY-REVIEW](USABILITY-REVIEW.md) thay thế nhãn chờ giáo viên trong các ghi nhận lịch sử bên dưới. 116 mẫu được giữ và dùng theo giả thiết nêu trong từng câu; 4 mẫu đã sửa ngữ nghĩa/nhiễu. Prototype hiện hành đã giải độc lập đủ40câu/ý,40khớpkhóa. Không yêu cầu giáo viên review; không gán teacher-approved hoặc độ khó thực nghiệm.

# QA — Hóa học research dossier

## Trạng thái dữ liệu hiện hành

- Source rows: **320**; source papers: **2 official + 6 provincial/third-party**.
- Topic guides retained and indexed: **25/25** (T01–T25).
- Accepted synthetic samples: **116**; held: **0**; teacher-approved: **no**.
- Exact coverage cells: **124/124** covered; missing/hold: **0**.
- Source-level unknowns: **3**, with the per-item reason recorded in [LEVELS.md](LEVELS.md) and `completion.json`.
- Prototype compile/layout QA: **pass**; xem [PDF](prototype-revised/prototype.pdf) và [verification receipt](prototype-revised/verification.json). Runtime integration: **not tested**.

## Limits

- Source rows are current OCR/figure-based annotations, not exhaustive proof against every original page.
- Source answer keys are not all independently validated.
- Coverage means at least one accepted example at the exact topic–part–level cell; it does not exhaust variants or establish empirical difficulty.
- Current agent review solved all 40 atomic prototype units and matched all keys; no teacher review is required. Runtime integration is untested, and empirical difficulty is not measured.
- Synthetic samples are separate from source-frequency evidence.
