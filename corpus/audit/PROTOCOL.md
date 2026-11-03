# Cách đếm và giới hạn diễn giải

- Chỉ đề thật đầy đủ/đọc được được vào tập nội dung; loại đề app sinh và đề `reference`. Một đề có nhiều mã hoán vị chỉ lấy một. Nguồn sao bên thứ ba không được đổi thành nguồn Bộ đã xác thực.
- OCR mới: Luna; bản Sol đã chép giữ nguyên provenance. Phân tích chuỗi suy luận, nhiễu, tự giải và đề xuất: Sol. Mỗi môn dùng một model EXTRACT phân tích; model OCR là thông tin riêng. Đếm, nối khóa và kiểm refs bằng code.
- Chính thức và tỉnh có mẫu số riêng, aggregate riêng. Chính thức đặt mốc độ khó; tỉnh có thể khó hơn. Một bản chính thức chỉ cho mô tả, không chứng minh tần suất ổn định. Toán chưa đủ hai mươi đề tỉnh thì không đề xuất đổi ma trận.
- Đơn vị trích là câu; đúng/sai là từng ý. Địa chỉ luôn phần + số trong phần + ý. Hiện diện chủ đề/lớp đếm số đề phân biệt, không cộng các ý thành số đề. Nhánh tự chọn được lưu riêng; không giả định một học sinh làm cả hai nhánh.
- Lớp chưa rõ giữ null. Catalog chương trình chỉ hỗ trợ tên bài/lớp, có thể dở hoặc từ kế hoạch bên thứ ba; không là bằng chứng tần suất. Số không ở một lớp chỉ có nghĩa chưa có nhãn lớp đó, không chứng minh vắng kiến thức khi còn hàng chưa rõ.
- Phân hoá cao là nhận định từ chuỗi quyết định/suy luận, không đo từ điểm học sinh. Nhiều phép tính hay tình huống dài không tự thành câu khó. Khi so số câu cao, một câu TF được tính cao nếu có ít nhất một ý có yêu cầu cao; không so số ý thật với số câu prototype.
- Nhiễu “theo lỗi” chỉ khi nêu được lỗi học sinh cụ thể và hợp lý. Mẫu số tỷ lệ chỉ gồm phương án sai đã phán đoán, có khóa xác định và không bất đồng với lượt tự giải; các phương án chưa xác minh được báo riêng. Tỷ lệ này vẫn là model đánh giá, không thay dữ liệu học sinh.
- Lượt tự giải prototype không thấy khóa, lời giải, filename nguồn hay nhãn level. Hình đề được đưa khi cần. Sau đó code mới nối khóa/nhãn. Bất đồng chỉ là nghi vấn cần giáo viên, không tự đổi key.
- Độ dài phương án tính theo từ và ký tự sau bỏ layout bằng grammar product. Ghi riêng dài nhất kể hoà và dài nhất duy nhất; đây không phải đo chiều rộng in, cũng không chứng minh khả năng đoán đúng.
- Profile được kiểm refs trong đúng lớp bằng chứng, quét trùng mười từ/chữ số. Kiểm chuỗi không chứng minh không sao chép ý nghĩa. Không đưa câu/số liệu/tình huống riêng của đề thật vào báo cáo/profile.
- Lỗi hai lần trong cùng bước thì dừng bước ấy, ghi log và đi phần độc lập. Lỗi quota/auth/transport chung thì dừng các bước model phụ thuộc. Không gọi lại toàn batch chỉ vì một giấy có lỗi JSON; phục hồi envelope chỉ khi không thay giá trị và có bằng chứng raw/hashes.
- Không sửa product, không merge/push, không full suite, không UI cũ, không API key tính phí. Các mẫu ngoại ngữ mới luôn chờ giáo viên duyệt kể cả compile và giải model đều đạt.
