# CHANGES — 2026-11-04

- `de.md` — giữ nguyên toàn bộ đề bài, lựa chọn A–D, các ý a–d và trích dẫn, ngoại trừ những thay đổi được ghi cụ thể dưới đây.
- `structure.json` — chuyển `ma_de` từ ghi chú văn bản sang `null` vì bản in Điện Biên không có mã đề; giữ giá trị cũ ở `legacy/structure.previous.json`.
- `structure.json` — thêm nhóm tư liệu chung Phần I Câu 22–24; đoạn dẫn vẫn nằm nguyên ở `de.md`, không gộp vào câu trước.
- `structure.json` — giữ các field cũ hợp lệ; bổ sung schema v2.0, địa chỉ câu theo từng phần, lựa chọn A–D/ý a–d, thứ tự phần và liên kết tư liệu chung khi có.
- `key.json` — chưa xuất khóa xác nhận cho Điện Biên; bản dữ liệu cũ giữ nguyên tại `legacy/key.unverified.json` do nguồn không in mã đề.

## Bằng chứng và giới hạn

- Nguồn chính: các ảnh gốc (đề chính thức) hoặc `paper.docx` (đề tỉnh); đã mở xem trực tiếp trang 3–4 mỗi đề.
- Kiểm tra metadata/nhãn câu/ý/đáp án và hàng bảng bằng công cụ; không tuyên bố rà từng chữ toàn đề hoặc duyệt bởi giáo viên.
- Không thêm kết quả giải hay sửa lịch sử theo suy luận.
