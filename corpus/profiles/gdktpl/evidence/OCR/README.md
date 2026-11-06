# OCR-gdktpl — corpus đóng gói

- **Phạm vi:** 14 đề Giáo dục Kinh tế và Pháp luật, năm 2026, lớp nguồn `provincial_third_party` theo manifest đầu vào; không có đề `official` hay `format_only` độc lập trong gói đầu vào này.
- **Hoàn thành bản đóng gói OCR draft:** 14 đề. **Partial:** 0. **Blocked:** 0. Không có teacher review; chữ “complete” chỉ nói về sự đầy đủ của nội dung chép theo cấu trúc phát hiện được.
- **Dữ liệu tái sử dụng:** toàn bộ `existing-ocr` được giữ nguyên nội dung chép nguồn; mỗi `de.md` chỉ thêm `status: ocr-draft` ở dòng đầu. Không tạo profile, không sinh câu mẫu, không thay đổi cách viết thuật ngữ của đề gốc.
- **Đáp án:** mỗi `key.json` cũ được đối chiếu đủ 24 đáp án trắc nghiệm và 16 ô đúng/sai trong bảng đáp án in **cùng bản DOCX và đúng mã đề**. Không tạo đáp án bằng cách tự giải; lời giải dài không đưa vào `de.md`.
- **Ảnh/công thức:** phần đề của 14 nguồn không có hình nhúng cần crop hoặc phương trình OOXML; riêng Hải Phòng lần 1 có 11 WMF nằm trong **phần lời giải tham khảo**, không thuộc đề nên không crop thành hình câu hỏi. Thư mục `images/` được giữ rỗng.
- **Cấu trúc:** `structure.json` bổ sung câu theo khóa `(part_id,index_within_part)`, số in riêng, đáp án lựa chọn/ý a-d, và nhóm đoạn dẫn chung; giữ thuộc tính cũ của tệp JSON khi hợp lệ.
- **Xác minh thực tế:** 14 DOCX được render để kiểm kê trang; ảnh trang render 3 và 4 của mỗi nguồn đã được xem trực tiếp, kết hợp đối chiếu câu/nhãn trong OCR và bảng đáp án từ chính Word; không khẳng định mọi ký tự trên mọi trang đã được soát bằng mắt. Chưa có giáo viên kiểm định.
- **Phân trang:** số trang phần đề và số trang DOCX toàn bộ khác nhau vì tài liệu có thêm đáp án và lời giải. Trường `pages_observed` = trang **phần đề theo bản render**, `source_docx_rendered_total_pages` = cả tệp; `pages_expected` = số trang đề được ghi trong tệp nếu có (không đoán khi không ghi). Có cảnh báo reflow khi số trang không khớp trang được in thông báo, không xem đó là bằng chứng thiếu trang.
- **Vấn đề còn lại:** kiểm tra thêm `issues.json` từng đề; có 1 cảnh báo phân trang render ở Phú Thọ và 1 lưu ý số câu in cách bất thường tại Tuyên Quang lần 1. Các nội dung còn lại chưa được teacher review. Không có giả định nào về phân bố nội dung cho thiết kế đề/profile chỉ dựa vào tỷ lệ OCR.

## Cấu trúc thư mục

- `manifest.json`: kiểm kê theo đề, mã đề, SHA-256 từng nguồn và phạm vi kiểm tra.
- `transcriptions/gdktpl/2026-provincial/<slug>/de.md`: bản chép nguồn (`ocr-draft`).
- Cùng thư mục: `structure.json`, `key.json`, `issues.json`, `STATUS.md`, `CHANGES.md`, `PRIOR_STATUS.md`, `source.json`, `images/`.

Không coi bản DOCX đóng dấu “ĐỀ CHÍNH THỨC” là đề **thi tốt nghiệp quốc gia chính thức**: đây là các đề thi thử/khảo sát cấp tỉnh theo nguồn manifest.
