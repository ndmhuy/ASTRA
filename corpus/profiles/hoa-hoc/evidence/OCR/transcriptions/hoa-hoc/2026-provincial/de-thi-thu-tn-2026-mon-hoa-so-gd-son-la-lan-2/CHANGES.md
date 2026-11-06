# CHANGES — hoa-hoc

- `key.json`: giữ nguyên từ OCR cũ; nguồn đối chiếu: Đáp án in cùng tệp DOCX (trang render 5). Chỉ làm đối chiếu khả dụng, không suy luận đáp án mới.
- `structure.json`: giữ metadata nguồn hợp lệ và bổ sung schema 2.0 gồm địa chỉ câu theo phần, các lựa chọn/ý và ảnh tham chiếu; tạo từ tiêu đề/câu đã có trong `de.md`, không chỉnh nội dung đề.
- `images/*.png` có sẵn: giữ nguyên tệp của OCR cũ; nguồn hình và vị trí crop chi tiết xem `structure.json` và audit cũ (nếu có).

Không có chỉnh sửa nội dung nào dựa trên việc tự giải đề.
