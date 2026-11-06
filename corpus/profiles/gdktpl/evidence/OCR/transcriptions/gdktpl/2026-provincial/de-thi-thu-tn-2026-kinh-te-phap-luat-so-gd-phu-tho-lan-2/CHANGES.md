# CHANGES — gdktpl/2026-provincial/de-thi-thu-tn-2026-kinh-te-phap-luat-so-gd-phu-tho-lan-2

- `de.md`: **giữ nguyên toàn bộ nội dung OCR cũ**, chỉ chèn hai dòng đầu (`status: ocr-draft` và dòng trống). Không tự sửa thuật ngữ, lỗi in, số liệu hay câu chữ.
- `structure.json`: giữ các trường gốc còn hợp lệ, thêm schema `2.0.0`, địa chỉ `(part_id, index_within_part)`, `printed_number`, tất cả 24 lựa chọn A–D, 4 × 4 ý đúng/sai, và 2 nhóm đoạn dẫn chung. Nguồn: `de.md` hiện có, đối chiếu cấu trúc với các trang đề DOCX 1–5.
- `key.json`: giữ nguyên dữ liệu cũ sau khi đối chiếu **từng ô** với bảng đáp án in trong `paper.docx` của đúng mã đề **1025** (24 MCQ + 16 ý đúng/sai), bảng xuất hiện sau phần đề, trang 5 trở đi của bản render. Không giải đề để tạo khóa.
- `source.json`: giữ nguyên. `PRIOR_STATUS.md`: lưu toàn văn ghi chú cũ, không coi là teacher review.
- `images/`: không thêm crop do phần **đề thi** không có hình/công thức nhúng cần trích. DOCX không chứa hình nhúng.
- `issues.json`: 1 mục, gồm cảnh báo về nguồn/dàn trang nếu có; không tự chỉnh số câu hoặc phỏng đoán chữ mờ.

## Kiểm tra dựa trên nguồn

- Nguồn bytes: `originals/official/2026-provincial-gdktpl/de-thi-thu-tn-2026-kinh-te-phap-luat-so-gd-phu-tho-lan-2/paper.docx`, SHA-256 `699bf58ff8f7c46441a518c41f2ff249ba5cf719b5014cdab4c8d48a3fc9bbd8`.
- Các trang **3–4** của bản DOCX đã được render thành PNG và xem trực tiếp; mọi trang đã được render để kiểm kê số trang, nhưng **không khẳng định mọi trang đã được soát từng chữ bằng mắt**.
- Đối chiếu cấu trúc: đủ 24 câu Phần I, 4 câu Phần II, mỗi câu I có A–D và mỗi câu II có a–d; đối chiếu phần đáp án in trong tài liệu bằng bảng Word.
- Mọi điều chỉnh cụ thể về **từng câu**: không có chỉnh sửa văn bản câu hỏi (chỉ tái cấu trúc metadata ở `structure.json`).
