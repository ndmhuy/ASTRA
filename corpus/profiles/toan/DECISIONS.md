# Kết luận nghiên cứu và quyết định về Toán

Phạm vi: hai đề chính thức và hai mươi đề tỉnh/trường đã chọn trước khi tổng hợp. Đây là bằng chứng nội bộ; hai nhóm nguồn luôn tách. Các kết luận dưới đây không thay ma trận sản phẩm.

## Ma trận

- **P3 thiếu xác suất trong mặc định:** các họ hỏi xác suất trực tiếp có **2/2 đề chính thức, 14/20 đề tỉnh/trường**. Nếu tính thêm bài kỳ vọng/thu ròng trung bình thì hợp rộng là **15/20 đề tỉnh/trường**; bài kỳ vọng giữ riêng vì yêu cầu trả lời và bất định chương trình khác nhau. Các con số lấy hợp paper_id, không cộng các hàng chủ đề gần nhau. [Receipt phạm vi đếm](../../audit/outputs/parent-reviews/toan-probability-scope.json) nêu chính xác các họ và ref. Có cả xác suất cổ điển–tổ hợp, điều kiện, quá trình hữu hạn và kết hợp hình học. Không gộp chúng thành một kỹ thuật duy nhất hoặc suy rằng đề nào cũng phải dùng Bayes.
- **Nền tảng lớp 10–11 có xuất hiện:** bất phương trình, quy hoạch tuyến tính, lượng giác, tổ hợp và quan hệ hình học cần được xem trong các dạng thực tế. Việc xuất hiện không tự tạo hạn ngạch lớp; câu có thể liên kết kiến thức nhiều lớp.
- **Nguyên hàm và tích lũy không đồng nghĩa với diện tích–thể tích:** chỉ dùng tên chương rộng sẽ bỏ mất cách hỏi và thao tác suy luận. Hồ sơ giữ các họ cách dựng riêng, đồng thời giữ liên hệ với chương mặc định.
- **P2 là cả câu bốn ý:** đề xuất chủ đề chính phải được triển khai trên một tình huống nhất quán. Các ý có thể hỏi kiến thức khác nhau nhưng phải giữ dữ kiện dùng chung và không để ý sau tiết lộ ý trước. Số slot mặc định là số câu; bảng đếm ý không được dùng thay số câu.

[Đọc toàn bộ bảng và giới hạn đề xuất](../../audit/matrices/toan.md). Danh sách đề xuất giữ hình dạng P1/P2/P3 hiện tại; vị trí trong danh sách là phương án để chủ app xét. Đổi chủ đề cần rà lại outcome, mức và references của slot, không chỉ đổi chuỗi tên.

## Phân hóa và cách dựng

Bằng chứng chính thức gợi ý các thao tác: tự chọn biểu diễn phù hợp; nối ràng buộc cục bộ thành điều kiện toàn cục; phân biệt cấu hình với nhãn đối tượng; chuyển từ đại lượng trung gian sang đúng đại lượng được hỏi; kiểm tra điều kiện hợp lệ của phép rút gọn. Các thao tác và ref hỗ trợ được nối riêng trong từng chủ đề.

Đề tỉnh bổ sung biến thể như phân miền tích phân, lọc nghiệm khả thi, giữ lịch sử chọn mẫu và trạng thái, mô hình nhiều chặng. Những kỹ thuật chỉ có ở nguồn tỉnh hoặc còn nghi vấn phạm vi chương trình được giữ giới hạn; không tự nâng thành chuẩn chính thức.

Một bài quen thuộc có nhiều phép tính vẫn có thể là TH. Một tình huống thực tế chỉ thay tên đối tượng cũng không tự thành VD. Nhãn nhận thức được xét theo công việc tối thiểu để trả lời đúng; mức phân hóa thấp/vừa/cao là một nhận định khác.

## Prototype

Hai prototype Toán đều có đủ lượt chấm độc lập. Mỗi bản có 22 câu; không bản nào được model nhận định có câu phân hóa cao. Để đối chiếu cùng đơn vị, nguồn chính thức có **5 câu phân biệt trên tổng 44 câu** chứa ít nhất một ý/hàng được nhận định phân hóa cao. Đây là ước lượng từ cấu trúc suy luận, chưa có dữ liệu học sinh.

Cần ưu tiên ba nhóm sửa:

1. Làm rõ giả thiết và quy trình ngẫu nhiên; mô hình liên tục phải được nêu nếu kết quả cần thời điểm giữa các mốc rời rạc. Không tự kết luận khóa sai chỉ vì cách ghi đơn vị khác nhau.
2. Giữ phương án, đồ thị, bảng và các nhận định liên quan cạnh nhau. Đã mở đủ sáu trang bản Haiku và xác nhận ba trường hợp ngắt trang; dữ kiện vẫn hiện diện đầy đủ.
3. Với mục tiêu phân hóa cao, thêm lựa chọn mô hình, ràng buộc hoặc kiểm tra điều kiện đạt có ý nghĩa; không tăng khó bằng số phép tính. Nhiễu phải có cơ chế sai cụ thể và vẫn cần hợp lý sau khi xét dấu hiệu lộ qua lời văn.

Bộ tệp prototype không cung cấp nhãn mức gốc từng câu. Vì vậy chỉ tiêu “gắn VD nhưng thường quy” chưa đánh giá được; số không ở báo cáo thô không chứng minh gán mức đúng. [Audit](../../audit/prototypes/toan.md) và [rà bổ sung bằng bản in](../../audit/prototypes/toan-parent-review.md) phải được đọc cùng nhau.

## Giới hạn còn giữ

Nhãn NB/TH/VD hiện dựa trên khái quát trích xuất, chưa phải rà toàn bộ câu gốc. Chín ý/câu giữ chưa rõ vì thiếu hình/miền/giả thiết hoặc chưa xác định duy nhất đại lượng cần hỏi. Không lấy khóa để suy ngược giả thiết. Mười đề tỉnh chưa có khóa khớp nên không đưa phần nhiễu chưa xác nhận vào mẫu số phương án sai đã kiểm.

Đã rà lại một tên họ dễ gây hiểu nhầm: câu tọa độ trên hình thang dùng Oxyz. Bản đọc và gói chủ đề hiện ghi **tọa độ không gian với cấu hình phẳng**; mã cũ chỉ giữ để truy biên nhận của kế hoạch mẫu đã đóng băng.

Câu mẫu là nội dung mới, không phải nguồn tần suất. Những mẫu còn cờ hoặc bị giữ không nằm trong tập ví dụ đủ kiểm của gói chủ đề. [Kiểm định hiện tại](completion.json) ghi trạng thái thực tế. Chưa có giáo viên duyệt, dữ liệu thử trên học sinh hoặc chạy tích hợp pipeline; đây là các mức xác nhận riêng.

## Đọc tỷ lệ nhiễu đúng mẫu số

Trong hai đề chính thức, MCQ có 67/72 phương án sai đã xét liên hệ được cơ chế nhầm; các nhận định TF có 13/14 mục đã xét. Hai đơn vị này không gộp thành tỷ lệ phương án MCQ. Với tỉnh/trường, MCQ là 329/353 mục đã phán đoán, TF là 48/56; phần chưa xác minh giữ riêng và có thể chứa lựa chọn chưa xác định đúng/sai do chưa có khóa khớp. Đây vẫn là đánh giá của model, không phải tần suất lỗi đo trên học sinh.
