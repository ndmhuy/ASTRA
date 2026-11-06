# Câu mẫu mới — toan / Quá trình xác suất hữu hạn

Câu do Sol viết mới, không phải đề thật hoặc bằng chứng tần suất. Chưa giáo viên duyệt. Nhãn mục tiêu dựa trên phân loại khái quát; xem LEVELS.md. Một mẫu cho mỗi ô chủ đề/phần/mức có căn cứ, chưa bảo đảm phủ mọi dạng trong cùng ô.

Đã xuất 1/1 mẫu dự kiến; các mẫu có cờ không được coi là sẵn dùng.

## Quá trình xác suất hữu hạn / P3 / VD

Đã qua kiểm bằng model; chờ giáo viên rà.

Một thiết bị mô phỏng bắt đầu ở mức năng lượng 2. Sau mỗi lượt, mức năng lượng tăng 2 đơn vị với xác suất 1/3 hoặc giảm 1 đơn vị với xác suất 2/3. Kết quả các lượt độc lập. Thiết bị dừng ngay khi mức năng lượng đạt ít nhất 5 hoặc bằng 0; trường hợp đạt ít nhất 5 được gọi là thành công. Gọi P là xác suất thiết bị thành công đúng ở lượt thứ sáu. Tính 729P.


Đáp án: 32

Lời giải: Đặt p = 1/3, q = 2/3. Chỉ theo dõi các trạng thái chưa dừng. Sau lượt 1, các trạng thái là 4 với xác suất p và 1 với xác suất q. Sau lượt 2, trạng thái chưa dừng duy nhất là 3, có xác suất pq + qp = 2pq. Sau lượt 3, trạng thái chưa dừng duy nhất là 2, có xác suất 2pq². Sau lượt 4, trạng thái 4 có xác suất 2p²q² và trạng thái 1 có xác suất 2pq³. Sau lượt 5, trạng thái chưa dừng duy nhất là 3, có xác suất 2p²q³ + 2p²q³ = 4p²q³. Muốn thành công ở lượt 6, từ trạng thái này thiết bị phải tăng 2 đơn vị. Do đó P = 4p³q³ = 32/729, suy ra 729P = 32. Các nhánh đã chạm mức dừng đều bị loại ngay, kể cả khi tổng biến thiên của một chuỗi kéo dài giả định cho kết quả phù hợp.

Lỗi tạo nhiễu:

Mức dự kiến: Học sinh phải xây dựng mô hình trạng thái có hấp thụ, xác định những nhánh còn được phép tiếp tục và kết nối xác suất qua các lượt. Chỉ xét mức năng lượng cuối cùng mà bỏ điều kiện dừng sớm sẽ không xác định đúng biến cố.

Tiên quyết: Tính độc lập của các kết quả; Quy tắc cộng và quy tắc nhân xác suất; Phân loại biến cố theo trạng thái trung gian; Điều kiện dừng của một quá trình hữu hạn

Neo bằng chứng của dạng: chưa có quan sát chính thức cho ô này; nguồn tỉnh chỉ bổ sung dạng.

Bất định của mẫu: Định hướng cấu trúc chỉ dựa trên quan sát cấp tỉnh do bên thứ ba cung cấp; chưa có điểm neo đề chính thức. Đây là câu hỏi minh họa tổng hợp, không phải bằng chứng đề thi.

Biến thể: Có thể thay mức xuất phát, hai độ biến thiên và thời điểm thành công. Cần kiểm tra lại toàn bộ các nhánh dừng sớm và chọn hệ số chuẩn hóa phù hợp với xác suất mới.

Đối chiếu khóa: khớp. Đối chiếu mức: khớp.

Mức do lượt tự giải nhận định: VD. Phải xây dựng mô hình xác suất có trạng thái dừng, loại những đường đi đã kết thúc và nối các trạng thái qua sáu lượt; đây là chuỗi suy luận phụ thuộc có nội dung.

Cờ lượt tự giải: không có cờ nội dung; xem riêng đối chiếu mức ở trên

## Khoảng thiếu và giới hạn

[]
