> Tài liệu lịch sử/thiết kế tham khảo. Cấu trúc và policy hiện hành: [Pipeline hiện tại](../architecture/PIPELINE_PLAN_AND_BENCHMARK.md).

# ASTRA mini — bàn giao người 1

> Cập nhật phần người 2: full pipeline dùng `exam_baseline.pipeline.cli`, có Solver,
> Reviewer, Orchestrator và file LaTeX tự chứa hình. Xem
> [pipeline hiện tại](../architecture/PIPELINE_PLAN_AND_BENCHMARK.md). Phần dưới mô tả bàn giao mini cũ;
> các ghi chú “chưa có exporter” đã được thay bằng `latex_export.py` ở commit sau.

## Trạng thái và ranh giới

Branch gốc `multiagent` tại `42f3244bc886b443aaca795495fb9dcc744a58cd` là baseline một agent. Repo này không chứa schema RAG gốc, truy hồi, exporter LaTeX, `SolutionBook` hay `ReviewReport`. Module `exam_baseline.mini` là đường draft-only độc lập; endpoint V1 giữ nguyên. Exporter PDF/DOCX được nối qua file review riêng, không biến draft thành kết quả Solver/Reviewer tự động.

RAG do nhóm khác phụ trách. Contract hiện dùng `GenerationRequest` của baseline cho request/ma trận/bank và `MiniRequest.evidence[]` cho kết quả RAG đã được chuẩn hóa: mỗi item có `id`, `text`, `role` (`content_support` hoặc `form_example`) và `locator` tùy chọn. Adapter ở ranh giới RAG → Composer cần ánh xạ các trường này; chưa có spec RAG gốc trong repo nên chưa thể chốt mapping theo field thật. Evidence được đưa vào prompt như dữ liệu, không được coi là chỉ dẫn. `require_evidence=true` làm danh sách evidence trống thành lỗi trước khi gọi model và yêu cầu mỗi câu có ít nhất một `content_support`; `form_example` đơn lẻ không đủ. Composer có thể trả `{"error":{"code":"missing_evidence","message":"..."}}` khi evidence không đủ. Bằng chứng tham khảo dạng bài không chứng minh nội dung.

`ComposerOutput` chứa `GeneratedExam`, metadata câu hỏi và `VisualSpec`. Validator baseline kiểm số câu, phân bố, điểm, ID và source bank. Validator mini kiểm evidence refs, figure refs, question/revision và hình bắt buộc theo `required_visual_question_ids`. `ExamDraft` version `mini-v1` chứa Student exam đã bỏ answer/solution, figures, hashes và stage results. `student_view.json` chỉ chứa exam cho học sinh; `teacher_private.json` giữ đáp án Composer đề xuất, chưa được Solver/Reviewer xác nhận. Không đưa file private vào gói học sinh.

`VisualSpec` hỗ trợ `line_graph`, `bar_chart`, `geometry_segments` với dữ kiện, nhãn, trục/miền và scaling. Renderer Pillow chỉ dùng primitives cố định, không chạy code từ model. `FigureArtifact` ghi đường dẫn `figures/*.png`, SHA-256 của spec/asset, MIME, kích thước, revision và renderer. `verify_handoff(draft, root)` kiểm StudentView, stage status, spec binding, đường dẫn và hash PNG trước khi người 2 sử dụng. Cần người kiểm ảnh với dữ kiện gốc; JSON hợp lệ không chứng minh hình đúng. `geometry_segments` giữ tỉ lệ hai trục khi `scaling=equal`; sơ đồ chưa có đánh dấu góc vuông hoặc số đo cạnh, nên không dùng hình để tự đo độ dài.

## Chạy

```powershell
python -m pip install -e ".[dev]" -c requirements-tested.txt
python -m pytest -q
python -m exam_baseline.draft.cli --request path/to/mini_request.json --fixture path/to/composer_output.json --output runs/mini/replay1
python scripts/build_mini_fixtures.py
```

Bỏ `--fixture` để dùng `EXAM_PROVIDER=chat_completions` và cấu hình provider baseline. Fixture là replay, không phải kết quả model thật. Không có retry hoặc model call của Illustrator. CLI từ chối output dir đã tồn tại. Năm bộ synthetic trong `examples/mini/01_text` đến `05_mixed` chứa `input.json`, `composer_fixture.json`, `handoff/`; script tái tạo chúng. `teacher_private.json` chỉ là đáp án đề xuất từ fixture và không được gửi cho học sinh.

## Exporter PDF/DOCX đã duyệt

`exam_baseline.exporter` hiện tạo `de_thi` và `dap_an` ở cả PDF/DOCX từ cùng bản draft đã kiểm hash. Nó yêu cầu một file review với đáp án đã sửa và `approved=true`; file `teacher_private` chỉ là đề xuất để chuẩn bị review. Chưa có Solver/Reviewer tự động, nên người duyệt phải chịu trách nhiệm kiểm nội dung. LaTeX trong stem/đáp án được chặn đến khi có bộ render toán học đáng tin cậy. Hướng dẫn đầy đủ và policy đầu vào MAS ở [MAS_INTAKE_AND_EXPORT.md](MAS_INTAKE_AND_EXPORT.md).

## Kiểm chứng còn thiếu

Tests trong `tests/test_mini.py` bao phủ năm gói CLI, ma trận/provenance sai, thiếu hình bắt buộc, revision, asset hash, schema, provider failure và malformed JSON. Đã xem trực tiếp bốn PNG: đồ thị có vạch trục và điểm đúng dữ kiện fixture; tam giác có A(0,0), B(3,0), C(0,4) đúng tỉ lệ; biểu đồ có cột A=3, B=5, C=4 và nhãn tiếng Việt đọc được; bộ mixed có cả câu có hình và không hình. Đây là đối chiếu ảnh với dữ liệu fixture, chưa phải chuyên gia duyệt chất lượng đề. Chưa có live model quality, XeLaTeX compile hay benchmark. Độ khó chỉ là nhãn dự kiến. Không gọi draft này là đề đã kiểm duyệt.
