# HH-F-5c8b7da5d316 — T11

Phần P3; dạng short_answer. Mẫu synthetic, không thuộc corpus nguồn. Trạng thái: agent_reviewed_usable_with_stated_assumptions; chưa giáo viên duyệt.

## Đề bài

Một nguyên tố giả định X chỉ có hai đồng vị bền với khối lượng danh định 20 và 22 u. Một phổ kế khảo sát phân tử X2 tạo do ghép ngẫu nhiên hai nguyên tử độc lập từ cùng một mẫu. Ba đỉnh có khối lượng danh định 40, 42, 44 u, bỏ qua sai khác đáp ứng. Tổng cường độ đỉnh 40 và 44 gấp 13/6 lần cường độ đỉnh 42. Phép đo độc lập cho biết khối lượng nguyên tử trung bình nhỏ hơn 21 u. Tính phần trăm số nguyên tử đồng vị 22 trong mẫu. Ghi giá trị phần trăm, làm tròn 1 chữ số thập phân.

## Khóa, lời giải và mức nhận thức

- Đáp án: **19.7**; mức **VD**. Gọi p là tỉ phần đồng vị 22. Ba đỉnh 40, 42, 44 tỉ lệ (1−p)^2, 2p(1−p), p^2. Đặt r=p(1−p), điều kiện (1−2r)/(2r)=13/6 cho r=3/19. Hai nghiệm p=(1±sqrt(7/19))/2; khối lượng trung bình 20+2p<21 buộc p<0,5. Suy ra p≈0,19651, tương ứng 19,7%.

Gọi p là tỉ phần đồng vị 22. Ba đỉnh 40, 42, 44 tỉ lệ (1−p)^2, 2p(1−p), p^2. Đặt r=p(1−p), điều kiện (1−2r)/(2r)=13/6 cho r=3/19. Hai nghiệm p=(1±sqrt(7/19))/2; khối lượng trung bình 20+2p<21 buộc p<0,5. Suy ra p≈0,19651, tương ứng 19,7%.

**Căn cứ nhận thức:** VD: phải dựng mô hình ghép ngẫu nhiên tạo đỉnh hỗn hợp và dùng phép đo thứ hai loại một nhánh nghiệm; không thể đọc trực tiếp tỉ phần nguyên tử từ một đỉnh phân tử.

## Nhiễu và cách làm tương đương


Chấp nhận lập luận hóa học tương đương, bảo toàn và đổi đơn vị nhất quán; kết quả phải thỏa toàn bộ điều kiện đề.

## Tiêu chí chấm và biến thể

- 1 điểm minh họa: Gọi p là tỉ phần đồng vị 22. Ba đỉnh 40, 42, 44 tỉ lệ (1−p)^2, 2p(1−p), p^2. Đặt r=p(1−p), điều kiện (1−2r)/(2r)=13/6 cho r=3/19. Hai nghiệm p=(1±sqrt(7/19))/2; khối lượng trung bình 20+2p<21 buộc p<0,5. Suy ra p≈0,19651, tương ứng 19,7%.

Tiêu chí là minh họa nghiên cứu, không thay biểu điểm của đề đích. Với TF, không mặc định chia đều điểm từng ý. Xem [CRITERIA](../CRITERIA.md).

- Dễ hơn: Cho sẵn tỉ phần đồng vị 22 rồi hỏi khối lượng nguyên tử trung bình.
- Khó hơn: Thêm đồng vị thứ ba và sử dụng nhiều đỉnh phân tử để xác định tính khả định của thành phần.

## Giải lại và trạng thái

**agent_reviewed_usable_with_stated_assumptions**. Hồ sơ không gọi lượt kiểm tra là teacher-approved.

Phải xây mô hình ghép ngẫu nhiên: với p phần đồng vị 22, cường độ là (1−p)^2:2p(1−p):p^2. Tỉ lệ cho p(1−p)=3/19; trung bình<21 buộc p<1/2, chọn p=0,196511.

Chi tiết: [ngân hàng hiện hành](../data/samples-current.json).
