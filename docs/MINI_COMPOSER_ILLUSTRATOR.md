# ASTRA mini — bàn giao người 1

## Trạng thái và ranh giới

Branch gốc `multiagent` tại `42f3244bc886b443aaca795495fb9dcc744a58cd` là baseline một agent. Repo này không chứa schema RAG, truy hồi, exporter LaTeX, `SolutionBook` hay `ReviewReport`. Những phần đó chưa được xác nhận là đã triển khai. Module `exam_baseline.mini` là đường draft-only độc lập; endpoint V1 giữ nguyên.

Contract hiện dùng `GenerationRequest` của baseline cho request/ma trận/bank và `MiniRequest.evidence[]` cho kết quả retrieval đã được chuẩn hóa: mỗi item có `id`, `text`, `role` (`content_support` hoặc `form_example`) và `locator` tùy chọn. Adapter từ JSON RAG thực tế phải ánh xạ các trường này; chưa có spec gốc trong repo nên chưa thể chốt mapping theo field thật. Evidence được đưa vào prompt như dữ liệu, không được coi là chỉ dẫn. `require_evidence=true` làm thiếu evidence thành lỗi. Bằng chứng tham khảo dạng bài không chứng minh nội dung.

`ComposerOutput` chứa `GeneratedExam`, metadata câu hỏi và `VisualSpec`. Validator baseline kiểm số câu, phân bố, điểm, ID và source bank. Validator mini kiểm evidence refs, figure refs, question/revision và hình bắt buộc theo `required_visual_question_ids`. `ExamDraft` version `mini-v1` chứa Student exam đã bỏ answer/solution, figures, hashes và stage results. `student_view.json` chỉ chứa exam cho học sinh; `teacher_private.json` giữ đáp án Composer đề xuất, chưa được Solver/Reviewer xác nhận. Không đưa file private vào gói học sinh.

`VisualSpec` hỗ trợ `line_graph`, `bar_chart`, `geometry_segments` với dữ kiện, nhãn, trục/miền và scaling. Renderer chỉ dùng primitives cố định, không chạy code từ model. `FigureArtifact` ghi đường dẫn `figures/*.png`, SHA-256 của spec/asset, MIME, kích thước, revision và renderer. Cần người kiểm ảnh với dữ kiện gốc, đặc biệt nhãn và tỉ lệ hình học; JSON hợp lệ không chứng minh hình đúng. `geometry_segments` hiện vẽ các điểm theo miền cung cấp nhưng chưa đảm bảo tỉ lệ thực trong mọi miền, nên không dùng nó cho bài cần đo độ dài từ hình.

## Chạy

```powershell
python -m pip install -e ".[dev]" -c requirements-tested.txt
python -m pytest -q
python -m exam_baseline.mini_cli --request path/to/mini_request.json --fixture path/to/composer_output.json --output runs/mini/replay1
```

Bỏ `--fixture` để dùng `EXAM_PROVIDER=chat_completions` và cấu hình provider baseline. Fixture là replay, không phải kết quả model thật. Không có retry hoặc model call của Illustrator. CLI từ chối output dir đã tồn tại.

## Nối exporter cho người 2

Exporter nhận `student_view.json`, `exam_draft.json` và thư mục `figures/`, sau khi Solver/Reviewer chấp thuận cùng `revision`. Xuất `de_thi.tex` từ StudentView, `dap_an.tex` từ `SolutionBook` riêng khi được yêu cầu. Chỉ nhúng asset bằng đường dẫn tương đối. `stem_format=latex` trong metadata câu quy định stem là đoạn LaTeX đã được kiểm, còn `plain` cần escape ký tự đặc biệt; hiện metadata này chưa gắn vào từng lựa chọn. Cần hoàn thiện contract phân đoạn plain/math và thử XeLaTeX với tiếng Việt, công thức và hình trước khi tuyên bố exporter hoạt động. Chưa có exporter để tái sử dụng hay smoke test compile.

## Kiểm chứng còn thiếu

Tests trong `tests/test_mini.py` bao phủ replay text-only, ma trận/provenance sai, thiếu hình bắt buộc, revision, schema và malformed JSON. Còn thiếu năm bộ bàn giao có nội dung chuyên môn được duyệt, live quality, kiểm ảnh thủ công và benchmark. Độ khó chỉ là nhãn dự kiến. Không gọi draft này là đề đã kiểm duyệt.
