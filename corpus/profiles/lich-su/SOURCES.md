# Nguồn, kiểm kê và độ tin cậy

| Đề (ID cuối) | Lớp nguồn | Mã đề | Trang đề | OCR | Khóa active | SHA hồ sơ cũ ↔ OCR mới |
|---|---|---|---|---|---|---|
| 2026-paper | official | 0825 | 4/4 | complete | Không có khóa active | không khớp/thiếu |
| de-thi-thu-tot-nghiep-2026-lich-su-so-gd-an-giang | provincial_third_party | 0807 | 4/4 | complete | Có nhưng chưa xác nhận độc lập | không khớp/thiếu |
| de-thi-thu-tot-nghiep-2026-lich-su-so-gd-bac-ninh-lan-2 | provincial_third_party | 0806 | 4/4 | complete | Có nhưng chưa xác nhận độc lập | khớp |
| de-thi-thu-tot-nghiep-2026-lich-su-so-gd-can-tho | provincial_third_party | 0501 | 4/4 | complete | Có nhưng chưa xác nhận độc lập | khớp |
| de-thi-thu-tot-nghiep-2026-lich-su-so-gd-dien-bien | provincial_third_party | unknown | 4/4 | partial | Không có khóa active | khớp |
| de-thi-thu-tot-nghiep-2026-lich-su-so-gd-gia-lai | provincial_third_party | 0810 | 4/4 | complete | Có nhưng chưa xác nhận độc lập | khớp |

Cả 6 đề có 4 trang đề. DOCX tỉnh có thêm trang đáp án/lời giải: **không đếm vào số trang đề**. Đề chính thức là ảnh JPG, nguồn gốc tại `evidence/originals/official/2026-papers/lich-su/`. Các dấu khoanh trên trang in **không** được dùng làm khóa. Với Điện Biên, bảng đáp án tham khảo tồn tại trong DOCX nhưng không khớp được mã đề; không tự xác nhận. Đề chính thức không có key.json active. Các nhãn “matched key” trong hồ sơ cũ chỉ là phát biểu lịch sử phải kiểm lại, không được nâng thành xác nhận mới.

Tệp OCR raw được giữ y nguyên ở `evidence/OCR/`, kể cả `CHANGES.md` trước đó. `originals/` được giữ để đối chiếu khi cần, không OCR lại. Nội dung mô tả từng câu trong hồ sơ cũ chỉ tái sử dụng trong mức phù hợp với SHA kiểm tra; không giả định đã đọc trực tiếp mọi trang ở lượt này.

Các tệp kiểm kê máy và hash: [data/sources.json](data/sources.json). Cờ theo nguồn: `evidence/OCR/manifest.json`. Prototype là lớp riêng **không cộng mẫu số**.

### Đối chiếu SHA cũ–mới có ngoại lệ

Đề chính thức (0825) và An Giang (0807) **không trùng SHA** với đường nguồn của hồ sơ cũ. Theo `CHANGES.md` hiện có, đề chính thức thêm metadata `status: ocr-draft`, An Giang sửa cách biểu diễn một ô bảng Phần II Câu 3. Do đó, phân tích cũ chỉ dùng như quan sát có điều kiện; câu/ý chịu ảnh hưởng trình bày phải đối chiếu lại với ảnh/DOCX trước khi dùng chấm hoặc rút kết luận. Bốn đề còn lại trùng SHA. Không được ghi “tất cả OCR đã xác minh” chỉ từ thống kê cấu trúc.


## Bổ sung — nguồn góp ý giáo viên

- **Loại**: nhận xét chuyên môn về prototype v4, không phải nguồn đề thi/corpus.
- **Tệp gốc bảo toàn**: [LichSu_v4_De_GOP-Y.docx](evidence/teacher-feedback/LichSu_v4_De_GOP-Y.docx) (SHA-256 `72e23b0fef711c2ca9537eb16d8168385fc3fdb0a0cfc958c789eac1c294d4d3`).
- **Phần nhận xét**: 5 ý đầu tài liệu; **Word comments**: 2, trực tiếp neo vào `P1/3`, `P1/8`.
- **Dữ liệu đọc dẫn xuất**: [data/teacher-feedback.json](data/teacher-feedback.json). Biên tập thành tiêu chí tại [Bổ sung](BO-SUNG.md); không sửa file nhận xét gốc.
- **Giới hạn**: một người phản biện, không có quyết định thông qua ma trận hoặc kết quả kiểm định thực nghiệm. Không tăng mẫu số official/provincial.
