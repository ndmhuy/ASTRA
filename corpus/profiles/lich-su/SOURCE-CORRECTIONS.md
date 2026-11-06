# Nhật ký hiệu chỉnh nguồn OCR

**Lượt tạo hồ sơ 2026-11-04:** không sửa byte nào của các tệp `evidence/OCR/**` và `evidence/originals/**`, không tái OCR. **0 chỉnh sửa mới**.

Các chỉnh sửa có chứng cứ của lượt OCR trước lưu nguyên tại `evidence/OCR/transcriptions/**/CHANGES.md`; không gộp hoặc sửa lại. Điện Biên: trạng thái partial liên quan đối sánh mã đề/khóa, **không phải lỗi văn bản đã được tự ý sửa**.

Đối chiếu hình trực tiếp bổ sung trong lượt này: ảnh gốc chính thức `evidence/originals/official/2026-papers/lich-su/page-03.jpg` cho thấy Phần I câu 20–24 và đầu Phần II; nhãn phần, năm/mốc và câu chữ tương ứng với `de.md` tại khu vực đã đọc. Đây là **kiểm mẫu một trang**, không phải xác minh OCR toàn đề.

### Hash reconciliation (không thay raw)

- `official/2026-paper`: SHA khác vì metadata `status: ocr-draft` (theo `CHANGES.md`); không mặc nhiên xác nhận nội dung câu đã kiểm toàn văn.
- `provincial/An Giang`: SHA khác vì cách biểu diễn bảng P2/3 (gộp 2 đoạn trong một ô, không đổi nội dung theo CHANGES.md), cần đối chiếu cụ thể các nhận định đọc từ bảng nếu dùng làm căn cứ mức.
- 4 đề còn lại có SHA OCR trùng bản được phân tích trước.
