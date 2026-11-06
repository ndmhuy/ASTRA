# Kế hoạch pipeline — 2 người làm lần lượt

**Mục tiêu:** phát triển baseline thành `Composer → Illustrator → Solver → Reviewer`.
Giữ baseline làm đối chứng. Bản đầu chạy tuần tự, chưa có vòng tự sửa hay framework mới.

## 1. Chia đúng 2 đầu việc

| Người | Đầu việc | Bàn giao |
| --- | --- | --- |
| **Người 1: tạo đề và hình** | Composer sinh đề theo ma trận; Illustrator tạo hình khi cần; lưu hình theo mã câu | `ExamDraft`: nội dung câu hỏi, điểm, nhãn, hình và nguồn câu |
| **Người 2: giải và kiểm tra** | Solver giải độc lập; Reviewer tìm lỗi trong đề/hình/lời giải; xuất báo cáo benchmark | `SolutionBook`, `ReviewReport`, bảng so sánh với baseline |

**Người 1 làm xong và bàn giao thì người 2 mới bắt đầu.** Người 1 nối Composer/Illustrator
vào API/CLI; người 2 nối tiếp Solver/Reviewer và phụ trách runner đo kết quả.

## 2. Hợp đồng bàn giao tối thiểu

- **ExamDraft:** `exam_id`, `revision`, `questions[]`.
- **Question:** `id`, `stem`, `choices`, `topic_id`, `difficulty`, `points`, `figure_refs`.
  Giữ các trường mục tiêu học tập và nguồn câu hiện có khi áp dụng.
- **Figure:** `question_id`, `revision`, đường dẫn ảnh và hash nội dung.
- **SolutionBook:** `question_id`, `revision`, đáp án, lời giải, có giải được không.
- **ReviewReport:** đạt/cần sửa, danh sách lỗi, mức nghiêm trọng và câu bị lỗi.

**Quy tắc:** Solver không nhận đáp án có sẵn. Hình bắt buộc bị thiếu phải báo lỗi.
Các output phải cùng revision. Reviewer chỉ nhận xét, chưa tự sửa đề ở phiên bản đầu.
Không cần hình thì Illustrator bỏ qua và không gọi model.

**Đầu ra cuối:** `de_thi.tex` cho học sinh và `dap_an.tex` khi yêu cầu đáp án/lời giải.
JSON vẫn dùng nội bộ để truyền dữ liệu và benchmark. Người 1 bàn giao hình PNG/PDF;
người 2 thêm bước xuất LaTeX sau Reviewer và kiểm tra cuối, hỗ trợ công thức/tiếng Việt.
Hình đi kèm dùng đường dẫn tương đối. Biên dịch PDF là bước riêng, có thể bổ sung sau.

## 3. Thứ tự làm

1. **Người 1:** làm Composer → Illustrator, xác định JSON bàn giao và chạy thử 5 request.
2. **Bàn giao:** code chạy được, lệnh chạy, JSON schema, 5 bộ input/output mẫu kèm hình,
   tests và các hạn chế đã biết. Chưa tính phần Solver/Reviewer là hoàn thành.
3. **Người 2:** nhận output đó, làm Solver → Reviewer và nối thành pipeline đầy đủ.
4. **Người 2:** chạy benchmark 10 request × 2 lần cho mỗi hệ thống; cùng input và model
   phù hợp. Hai người chấm chéo kết quả sau khi pipeline hoàn tất.
5. Chỉ thêm vòng sửa hoặc stage mới sau khi bản này chạy ổn.

## 4. Chỉ đo 6 metrics trước

| Metric | Cách tính |
| --- | --- |
| **Đạt ma trận** | Số đề qua mọi kiểm tra Python / tổng lần chạy |
| **Đáp án đúng** | Số câu được người chấm xác nhận đúng / số câu yêu cầu; câu thiếu/lỗi tính 0 |
| **Hình dùng được** | Hình đúng dữ kiện và đọc được / hình bắt buộc; không cần hình thì N/A |
| **Reviewer bắt lỗi** | Lỗi cài sẵn được phát hiện đúng / tổng lỗi cài sẵn; báo thêm số đề đúng bị báo nhầm |
| **Thời gian** | Median và thời gian lớn nhất mỗi lần chạy; ghi cả lần lỗi/timeout |
| **Chi phí/usage** | Tổng token, calls và chi phí mọi stage; thiếu số liệu ghi unknown |

Dùng thêm 10 câu đúng và 10 câu cố ý sai đã được xác nhận để thử Reviewer.
Hai người chấm chéo kết quả, không dùng chính Reviewer làm đáp án chuẩn.
Chạy lỗi vẫn nằm trong tổng lần chạy; chưa chấm xong thì chưa công bố điểm độ đúng.
Đây là pilot để tìm lỗi, chưa đủ để kết luận thống kê rằng pipeline tốt hơn.

## 5. Điều kiện xong

- Chạy được toàn bộ pipeline, lưu đề/hình/đáp án/review/trace và giữ baseline hoạt động.
- Lỗi stage được trả rõ ràng; không có retry hoặc vòng sửa ngầm.
- Có một bảng so sánh baseline và pipeline bằng 6 metrics trên.
- Xuất được đề LaTeX, tách đáp án khỏi đề học sinh và giữ đủ hình đi kèm.
- So trực tiếp với baseline hiện tại trên đề không hình. Đề có hình báo riêng vì baseline
  hiện tại chưa hỗ trợ hình tương đương; không dùng thiếu sót đó để tuyên bố pipeline thắng.

**Phần mở rộng sau:** interface riêng từng stage, model/prompt trong config; thêm stage
bằng cách bổ sung contract và ghép tại orchestrator, không viết lại bốn stage cũ.
