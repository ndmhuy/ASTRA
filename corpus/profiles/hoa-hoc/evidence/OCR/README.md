# OCR corpus — Hóa học

- **Đầu vào:** `hoa-hoc`, 8 đề trong MANIFEST.json; 2 `official`, 6 `provincial_third_party`. Không có đề `format_only` trong ZIP này.
- **Kết quả đóng gói:** 5 complete, 3 partial, 0 blocked.
- **Mục đích:** Chỉ OCR/kiểm tra và đóng gói. Chưa sinh profile hay câu hỏi mẫu. Không suy diễn tỉ lệ profile từ trạng thái OCR.
- **Tư liệu:** Dùng `existing-ocr/` làm nền, giữ nguyên cấu trúc `transcriptions/hoa-hoc/...`; originals/ chỉ dùng đối chiếu. `source_sha256` được tính từ byte của tài liệu gốc đọc được.
- **Câu hỏi:** Giữ nguyên câu chữ bản OCR cũ trừ các ghi chú/hình được sửa có chứng cứ. Các địa chỉ câu trong `structure.json` là `(part_id,index_within_part)`, `printed_number` là số in. Không gộp mã đề hoặc đánh số toàn đề.
- **Hình:** Mọi ảnh mới là crop PNG trực tiếp từ JPG gốc, không vẽ lại; hình cũ được tái sử dụng và kiểm tra liên kết.
- **Đáp án:** Chỉ giữ `key.json` khi bản DOCX đi kèm có đáp án tương ứng được ghi nhận; khóa ngoài ZIP lưu `unverified-existing-key.json` riêng; không dựa vào dấu khoanh thí sinh hoặc tự giải.
- **Phạm vi xác minh:** Đọc trực tiếp trang gốc/rendered có công thức, hình và bảng tại các trang đã ghi trong `verification_scope`; giữ lại audit trước đó nhưng **không** khẳng định đã làm một lượt kiểm tra độc lập toàn diện. Không có teacher review.

## Tồn đọng

- Quảng Ninh: chưa có bảng khóa được xác minh khớp mã đề, không tạo `key.json`.
- Quảng Trị và Nghệ An: số trang phần câu hỏi khi render DOCX vượt số trang ghi ở đầu đề; chưa thể kết luận đây là lỗi phân trang Word hay sai nguồn.
- Đề chính thức 2025: khóa cũ xuất phát từ nguồn ngoài ZIP và được giữ riêng, chưa nâng thành verified.
- Xem `issues.json`, `STATUS.md`, `CHANGES.md` từng đề. Bản gốc DOCX có thể chứa lời giải nhiều trang không được nhập làm câu hỏi.

## Tình trạng máy móc

JSON, ZIP, đếm câu và liên kết ảnh được kiểm thử khi đóng gói. Đây không phải xác nhận chính xác nội dung bởi giáo viên hoặc biên tập viên chuyên môn.
