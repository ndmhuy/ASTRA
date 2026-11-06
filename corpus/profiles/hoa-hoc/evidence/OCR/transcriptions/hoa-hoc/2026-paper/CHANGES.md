# CHANGES — hoa-hoc

- `de.md`: thêm dòng metadata `status: ocr-draft` ở đầu; không thay đổi nội dung câu hỏi; đối chiếu với bản OCR cũ, không phải chỉnh từ đề gốc.
- `de.md`, câu I.1: thay mô tả placeholder không có crop bằng ảnh `images/part1_q1_amino_acids.png` lấy trực tiếp từ `originals/official/2026-papers/hoa-hoc/page-01.jpg` (trang 1, crop pixel (180, 470, 1350, 595)); giữ câu hỏi và đáp án nguyên văn.
- `de.md`, câu I.9: thay mô tả placeholder không có crop bằng ảnh `images/part1_q9_lab_apparatus.png` lấy trực tiếp từ `originals/official/2026-papers/hoa-hoc/page-01.jpg` (trang 1, crop pixel (970, 1483, 1490, 1715)); giữ câu hỏi và đáp án nguyên văn.
- `de.md`, câu I.12: thay mô tả placeholder không có crop bằng ảnh `images/part1_q12_galvanic_cell.png` lấy trực tiếp từ `originals/official/2026-papers/hoa-hoc/page-02.jpg` (trang 2, crop pixel (1300, 72, 1720, 435)); giữ câu hỏi và đáp án nguyên văn.
- `de.md`, câu II.3: thay mô tả placeholder không có crop bằng ảnh `images/part2_q3_triglyceride_hydrolysis.png` lấy trực tiếp từ `originals/official/2026-papers/hoa-hoc/page-03.jpg` (trang 3, crop pixel (310, 1360, 1820, 1700)); giữ câu hỏi và đáp án nguyên văn.
- Không có `key.json` xác minh; không giải đề hoặc tự tạo khóa đáp án.
- `structure.json`: giữ metadata nguồn hợp lệ và bổ sung schema 2.0 gồm địa chỉ câu theo phần, các lựa chọn/ý và ảnh tham chiếu; tạo từ tiêu đề/câu đã có trong `de.md`, không chỉnh nội dung đề.
- `images/*.png` có sẵn: giữ nguyên tệp của OCR cũ; nguồn hình và vị trí crop chi tiết xem `structure.json` và audit cũ (nếu có).

Không có chỉnh sửa nội dung nào dựa trên việc tự giải đề.
