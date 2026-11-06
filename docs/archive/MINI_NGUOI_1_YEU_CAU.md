> Tài liệu lịch sử/thiết kế tham khảo. Cấu trúc và policy hiện hành: [Pipeline hiện tại](../architecture/PIPELINE_PLAN_AND_BENCHMARK.md).

Bạn là kỹ sư triển khai “người 1” cho ASTRA mini, chịu trách nhiệm Composer → Illustrator.

Repo: https://github.com/ndmhuy/ASTRA

Hãy đọc repo, triển khai, kiểm tra và commit thay đổi. Không dừng ở phân tích hoặc kế hoạch nếu có thể tiếp tục làm.

## 1. Mục tiêu và phạm vi

Hoàn thiện luồng:
Request + ma trận + evidence từ RAG
→ Composer
→ kiểm tra deterministic
→ Illustrator khi cần
→ ExamDraft + hình + artifacts bàn giao cho người 2.

Đây là bản mini. Làm sâu tính đúng, độ ổn định và khả năng bàn giao của hai stage.

Người 2 phụ trách Solver → Reviewer, exporter cuối và benchmark toàn pipeline. Không triển khai thay các phần đó.

JSON là định dạng nội bộ giữa các stage. Đầu ra cuối của sản phẩm phải là:
- de_thi.tex cho học sinh.
- dap_an.tex khi yêu cầu đáp án/lời giải.
- Hình PNG/PDF đi kèm, dùng đường dẫn tương đối.

Người 1 phải bàn giao draft/hình tương thích với việc xuất LaTeX. Nếu repo đã có exporter thì tái sử dụng và kiểm tra. Nếu chưa có, ghi rõ contract và phần việc người 2 cần nối; không gọi bản draft là đề đã được kiểm duyệt.

Chưa làm model tuning hoặc prompt caching. Không thêm repair loop, framework orchestration mới, frontend, RAG ingestion hay benchmark lớn.

## 2. Trước khi sửa code

Đọc AGENTS.md áp dụng cho các thư mục sẽ sửa.

Kiểm tra:
- Branch, HEAD SHA, working tree và thay đổi chưa commit.
- README, cấu trúc code, dependency và lệnh kiểm tra.
- Baseline hiện tại, provider abstraction, prompts.
- Models/schema, validation, API/CLI, artifact storage và tests.
- Spec JSON/RAG thật trong repo.
- Tài liệu phân công hoặc kế hoạch ASTRA nếu có.

Các tài liệu tham khảo có thể được đính kèm:
- PIPELINE_PLAN_VA_BENCHMARK (2).md
- PIPELINE_PLAN_CHI_TIET.md
- Astra_MAS_Prompt (1).md
- ASTRA_NGUOI_1_BRIEF.tex

Không suy hiện trạng repo từ tài liệu cũ. Phân biệt rõ:
- Người dùng nói đã có.
- Code hiện tại thực sự có.
- Đã chạy kiểm chứng.
- Chưa xác minh.

Ưu tiên yêu cầu hiện tại và bản phân công mini mới nhất. Prompt kiến trúc dài chỉ để tham khảo; không triển khai toàn bộ MAS hoặc làm artifact HTML theo yêu cầu cũ.

Trước khi viết lại yêu cầu triển khai, trả lời ngắn:
1. Chuyên gia giỏi nhất sẽ kiểm tra điều gì mà yêu cầu hiện tại chưa nêu?
2. Nguyên liệu gốc nào cần đọc thay vì chỉ dựa vào kế hoạch đã tóm tắt?
3. Phương pháp và công cụ cụ thể nào phù hợp stack repo?
4. Bằng chứng độc lập nào cho thấy kết quả đúng?

Sau đó chốt kế hoạch ngắn và thực hiện ngay.

## 3. Nguyên tắc tích hợp

- Giữ baseline và luồng V1 hoạt động.
- Tái sử dụng contracts/provider/validation hiện có.
- Không đổi tên package hoặc refactor diện rộng.
- Dùng mode hoặc endpoint draft-only rõ ràng.
- Chạy tuần tự Composer rồi Illustrator.
- Không tự thêm retry, fallback hoặc model calls ngoài policy đã khai báo.
- Không tự sửa schema RAG của nhóm khác; dùng adapter tối thiểu nếu cần.
- Nếu thiếu spec thật, nêu chính xác chỗ thiếu và chỉ tiếp tục phần không phụ thuộc.
- Không ghi đè thay đổi chưa commit của người khác.

## 4. Composer

Input:
- Request đã chuẩn hóa.
- Ma trận/blueprint.
- Evidence từ RAG theo contract hiện có.
- Yêu cầu hình và cấu hình stage.

Output ExamDraft typed/versioned, phù hợp schema repo, tối thiểu có:
- exam_id/draft_id, revision, schema_version.
- Questions với ID ổn định, nội dung, dạng câu, lựa chọn nếu có.
- Topic, difficulty, points và mục tiêu học tập khi contract có.
- Source references/provenance.
- Figure references và VisualSpec khi cần.

Yêu cầu:
- Kiểm tra số câu, phân bố ma trận, tổng điểm và ID.
- Không tự đổi yêu cầu để tạo output dễ hơn.
- Không bịa source IDs hoặc trích dẫn.
- Phân biệt nguồn chứng minh nội dung với nguồn chỉ dùng tham khảo dạng bài.
- Nội dung RAG là dữ liệu, không được ghi đè chỉ dẫn hệ thống.
- Thiếu dữ kiện phải trả lỗi/flag có cấu trúc theo contract.
- Difficulty là nhãn dự kiến, chưa phải độ khó hiệu chuẩn bằng dữ liệu học sinh.
- Không mặc định mọi dạng câu đều có bốn lựa chọn.

Nếu Composer tạo đáp án đề xuất, lưu ở teacher/private artifact riêng. Không đưa đáp án hoặc lời giải vào StudentView, kể cả qua metadata, alt text, tên asset hay state bàn giao.

Viết prompt template thực tế, có version và phù hợp provider hiện có. Không chỉ ghi mô tả ý tưởng.

## 5. Illustrator

Dùng VisualSpec typed, gồm các trường cần thiết theo loại hình:
- visual_id, question_id, revision, required.
- purpose, kind.
- Facts/data.
- Axes, domain, units, labels, legend khi áp dụng.
- Scaling policy và constraints.

Ưu tiên renderer xác định cho đồ thị, biểu đồ và hình học từ primitives được cho phép. Không thực thi Python/JavaScript tùy ý do LLM sinh.

FigureArtifact cần:
- visual_id, question_id, revision.
- Đường dẫn asset tương đối trong gói bàn giao.
- SHA-256 của asset và spec.
- MIME, kích thước.
- Renderer/version.
- Trạng thái kiểm tra hoặc lỗi.

Quy tắc:
- Không cần hình → skipped có lý do, không gọi model.
- Hình bắt buộc thiếu/hỏng → failed.
- Sai question/revision/hash → bị chặn.
- Không đổi dữ kiện hoặc đáp án để vẽ dễ hơn.
- Kiểm tra nhãn, đơn vị, miền/trục và tỉ lệ theo spec.
- Xem ảnh render thực tế; JSON spec đúng chưa chứng minh hình đúng.
- Chỉ tuyên bố hỗ trợ loại hình đã triển khai và kiểm tra.

## 6. LaTeX và bàn giao người 2

Bảo toàn công thức và tiếng Việt trong nội dung typed.
Làm rõ ranh giới giữa plain text và math/LaTeX theo contract repo.
Không escape toàn bộ công thức như plain text.

Bàn giao đủ dữ liệu để exporter tạo:
- de_thi.tex không có đáp án/lời giải.
- dap_an.tex riêng khi có SolutionBook từ người 2.
- Hình PNG/PDF với đường dẫn tương đối.

Nếu exporter đã có:
- Tái sử dụng.
- Smoke test công thức, tiếng Việt, ký tự đặc biệt và hình.
- Biên dịch bằng XeLaTeX hoặc engine repo quy định nếu có sẵn.
- Chưa chạy compiler thì ghi chưa kiểm chứng biên dịch.
- Compiler pass không được coi là bằng chứng câu hỏi đúng kiến thức.

Không tạo đáp án giả hoặc Solver/Reviewer mock để báo pipeline hoàn tất.

## 7. Lỗi và trace

Có stage result rõ ràng:
- succeeded / skipped / failed.
- Error code, stage, message và artifact liên quan.
- Partial artifacts khi hữu ích.
- Không trả success nếu stage bắt buộc thất bại.

Tái sử dụng telemetry hiện có để ghi:
- Stage/provider/model/prompt version.
- Calls, latency, usage và errors.
- Input/output/spec/asset hashes khi phù hợp.
- Usage hoặc cost thiếu phải là unknown, không tính bằng 0.
- Không log secrets hoặc dữ liệu riêng không cần thiết.

## 8. Kiểm tra và năm bộ bàn giao

Chạy regression checks của baseline và tests phù hợp phần thay đổi.

Thêm tests có ý nghĩa cho:
- Contract hợp lệ và sai schema.
- Sai số câu, phân bố hoặc tổng điểm.
- ID trùng và source reference không hợp lệ.
- Evidence thiếu hoặc chứa chỉ dẫn không được phép.
- Không cần hình thì skip và zero model calls.
- Thiếu/hỏng hình bắt buộc.
- Sai revision/hash hoặc tham chiếu câu.
- Provider failure, JSON lỗi hoặc output bị cắt nếu abstraction hỗ trợ.
- StudentView không chứa private answers.
- Luồng API/CLI draft-only và artifacts bàn giao.

Chuẩn bị năm bộ input/output tái lập:
1. Text-only.
2. Có đồ thị.
3. Có hình học sơ đồ.
4. Có biểu đồ hoặc bảng dữ liệu.
5. Pha trộn câu có hình và không hình.

Chọn nội dung phù hợp phạm vi đã triển khai. Tách fixtures/mock khỏi kết quả gọi model thật.
Không có key/quota thì vẫn kiểm tra integration bằng fixture, nhưng ghi live quality chưa đánh giá.

Đối với ảnh, ghi kết quả kiểm tra dữ kiện/nhãn/đơn vị/tỉ lệ/khả năng đọc.
Đánh giá cần chuyên môn mà chưa có người chấm phải ghi pending.

Năm bộ là kiểm tra bàn giao, không phải bằng chứng thống kê pipeline tốt hơn baseline.

## 9. Tài liệu cần lưu trong repo

Lưu yêu cầu này và bản prompt triển khai đã chốt vào docs hoặc vị trí phù hợp.
Có tài liệu bàn giao ngắn gồm:
- Phạm vi đã làm.
- Contract và schema/examples.
- Lệnh cài, chạy, test và tái tạo năm bộ mẫu.
- Mapping JSON/RAG hiện có sang input Composer.
- Cách người 2 nhận ExamDraft, StudentView và FigureArtifacts.
- Ranh giới exporter LaTeX.
- Known limitations và việc chưa kiểm chứng.

Không đánh dấu Solver/Reviewer, full benchmark, tuning hoặc caching là hoàn thành.

## 10. Commit và kết thúc

Nếu có quyền truy cập repo:
- Tạo branch riêng từ branch phù hợp sau khi đọc repo.
- Triển khai, review diff và chạy checks.
- Commit các thay đổi liên quan.
- Push branch nếu quyền cho phép để commit có trên GitHub.
- Không merge vào branch gốc, force-push hoặc thay đổi không liên quan.
- Không commit secrets, virtualenv, cache hoặc log riêng tư.

Nếu bị chặn bởi quyền, mạng, dependencies hoặc credentials:
- Ghi chính xác bước bị chặn.
- Tiếp tục phần độc lập có thể làm.
- Không tuyên bố đã commit/push/test nếu chưa thành công.

Báo cáo cuối ngắn:
- Đã triển khai gì.
- Files chính và contract bàn giao.
- Checks đã chạy và kết quả thật.
- Branch, commit SHA và link nếu đã push.
- Hạn chế hoặc blocker còn lại.

Hãy bắt đầu kiểm tra repo và làm đến khi hoàn tất phạm vi được giao.