# Corpus OCR Lịch sử — gói kiểm tra 2026-11-04

Chỉ kiểm kê, tái sử dụng OCR, đối chiếu nguồn và đóng gói; **không** tạo profile hay câu mẫu. Đây là dữ liệu riêng tư trong cuộc hội thoại.

Đã xử lý 6 đề theo đúng thứ tự manifest: **5 complete, 1 partial, 0 blocked**. Hoàn thành OCR không đồng nghĩa teacher-checked, approved hay hoàn thành profile.

| Đề | Lớp nguồn | Mã đề | Trạng thái | Trang đề |
|---|---|---|---|---|
| `2026-paper` | official | 0825 | complete | 4/4 |
| `de-thi-thu-tot-nghiep-2026-lich-su-so-gd-an-giang` | provincial_third_party | 0807 | complete | 4/4 |
| `de-thi-thu-tot-nghiep-2026-lich-su-so-gd-bac-ninh-lan-2` | provincial_third_party | 0806 | complete | 4/4 |
| `de-thi-thu-tot-nghiep-2026-lich-su-so-gd-can-tho` | provincial_third_party | 0501 | complete | 4/4 |
| `de-thi-thu-tot-nghiep-2026-lich-su-so-gd-dien-bien` | provincial_third_party | không in | partial | 4/4 |
| `de-thi-thu-tot-nghiep-2026-lich-su-so-gd-gia-lai` | provincial_third_party | 0810 | complete | 4/4 |

## Phạm vi và vấn đề còn lại

- Bản OCR cũ được dùng làm nền; `de.md` chỉ thay đổi tại các vị trí ghi trong từng `CHANGES.md`.
- Đã kiểm từng tài liệu đủ 24 câu Phần I, 4 câu Phần II và 4 ý đúng/sai/câu; bảng/tư liệu chung được đưa vào schema mới.
- Ảnh gốc 2026 mã 0825 có 4 trang; 5 DOCX tỉnh có 4 trang đề, cộng thêm các trang đáp án và lời giải, tổng cộng 8 hoặc 9 trang/tài liệu. Không chép lời giải.
- Không có hình đồ họa cần crop từ các nguồn đã kiểm tra: DOCX gốc không có media; bảng nguồn vẫn chép dưới dạng bảng Markdown. Thư mục `images/` được giữ để tương thích schema.
- Phần II Câu 1 c–d Điện Biên nối từ trang 3 sang 4 đã xác minh có đủ trong `de.md`. Tuy nhiên đề Điện Biên không in mã đề: chưa thể xác nhận khóa đáp án cho một mã đề cụ thể. Bản key cũ nằm riêng tại `legacy/key.unverified.json`, không phải `key.json`.
- Bảng ĐÁP ÁN THAM KHẢO của bốn DOCX có một mã đề được in trong phần đề; các ô đáp án được đối chiếu với DOCX. Bảng đáp án không in lại mã đề; mức liên kết là theo cùng tài liệu.
- Đề ảnh chính thức không in đáp án; bản `solved.json` trước đây chỉ lưu như dữ liệu chưa xác nhận tại `legacy/solved.unverified.json`.
- Chỉ kiểm trực tiếp chi tiết trang 3–4 của từng đề và đối chiếu cấu trúc toàn tài liệu; chưa rà lại từng chữ trang 1–2 trong phiên hiện tại. Chưa có teacher review.

## Cấu trúc

- `manifest.json`: từng nguồn, SHA256 theo bytes nguồn, lớp và trạng thái, phạm vi xác minh.
- `transcriptions/lich-su/.../de.md`: chữ gốc, với dòng đầu `status: ocr-draft`.
- `structure.json`: schema v2.0, địa chỉ (`part_id`, `index_within_part`, `printed_number`), `stimulus_groups`.
- `key.json`: chỉ dành cho bảng đáp án in được liên kết với một mã đề trong nguồn; `issues.json`, `STATUS.md`, `CHANGES.md` đi kèm mỗi đề.
- `legacy/`: status/audit/structure cũ và dữ liệu đáp án chưa xác nhận, giữ để có thể truy xuất nguồn gốc thay đổi.

**Không được suy diễn tỷ lệ đặc trưng nội dung hoặc tỷ lệ profile từ tỷ lệ hoàn thành OCR.**
