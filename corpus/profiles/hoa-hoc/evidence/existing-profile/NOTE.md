# Hồ sơ hoa-hoc

**Hồ sơ ra đề chưa được nghiệm thu đầy đủ. Tình trạng từng thành phần được ghi bên dưới; có tệp kết quả không đồng nghĩa đã hoàn chỉnh.**

Trích xuất và aggregate đã qua kiểm kỹ thuật; nhận định vẫn chờ giáo viên rà.

Đọc cách hỏi theo từng chủ đề (tham chiếu corpus cũ; dùng OCR/ và baseline/ trong gói này để kiểm tra)

**Các phần của hồ sơ:**

- Audit ma trận: đang bổ sung, chưa nghiệm thu.
- Audit prototype: đang bổ sung, chưa nghiệm thu.
- NB/TH/VD: đang bổ sung, chưa nghiệm thu.
- Câu mẫu mới: đang bổ sung, chưa nghiệm thu.

**Bằng chứng:** chính thức 2 đề; tỉnh/trường 6 đề; 320 câu/ý được gắn nhãn. Model EXTRACT: gpt-6.1-sol. Hai nguồn được tổng hợp riêng.
Khóa khớp đã chấp nhận: chính thức 2/2, tỉnh/trường 5/6.

**Lớp kiến thức xuất hiện — số đề phân biệt:**

| Nguồn / phần | Lớp 10 | Lớp 11 | Lớp 12 | Chưa rõ |
|---|---:|---:|---:|---:|
| Chính thức / P1 | 2/2 | 2/2 | 2/2 | 2/2 |
| Chính thức / P2 | 0/2 | 2/2 | 2/2 | 1/2 |
| Chính thức / P3 | 1/2 | 1/2 | 2/2 | 1/2 |
| Tỉnh/trường / P1 | 1/6 | 1/6 | 1/6 | 6/6 |
| Tỉnh/trường / P2 | 0/6 | 0/6 | 1/6 | 6/6 |
| Tỉnh/trường / P3 | 0/6 | 1/6 | 1/6 | 6/6 |

Một đề có thể chứa nhiều lớp; không cộng các cột thành tổng đề. Nhãn lớp và độ phân hóa do model nhận định.

**Cách dựng câu và phân hóa:**

- Chính thức: Đặt đặc tính có vẻ phù hợp cùng điều kiện làm phát sinh phản ứng cần xét; chỉ kết luận sau khi kiểm tra tác dụng mong muốn và tương thích môi trường.
- Tỉnh/trường: Buộc xét tác nhân cạnh tranh, chất dư và phản ứng tiếp thay vì dừng ở phương trình tạo sản phẩm ban đầu. Những hàng cùng một đề không tự tạo bằng chứng lặp liên đề.

**Mức phân hóa do model nhận định:**

| Nguồn | Thấp | Vừa | Cao | Chưa phán đoán |
|---|---:|---:|---:|---:|
| Chính thức | 50 | 26 | 3 | 1 |
| Tỉnh/trường | 123 | 106 | 9 | 2 |

Đếm theo câu/ý đã gắn nhãn; đây là độ phức tạp suy luận được nhận định, chưa phải độ phân hóa đo từ bài làm học sinh. Các cách dựng ở trên không mặc nhiên đều đạt mức cao.

**Dữ kiện thuộc lòng được dùng thế nào:**

| Nguồn | Hỏi trực tiếp | Cho làm gợi ý | Cần trong suy luận | Không dùng |
|---|---:|---:|---:|---:|
| Chính thức | 5 | 28 | 40 | 7 |
| Tỉnh/trường | 6 | 60 | 147 | 27 |

Các cột đếm câu/ý trong mẫu đã phân tích, không phải tần suất học sinh nhớ hoặc quên.

**Phương án nhiễu:**

- Chính thức: liên hệ được một kiểu nhầm cụ thể ở 113/120 phương án đã phán đoán (94.2%); chưa xác minh 5.
- Tỉnh/trường: liên hệ được một kiểu nhầm cụ thể ở 298/304 phương án đã phán đoán (98.0%); chưa xác minh 79.

Chưa phán đoán được mức phân hóa ở chính thức 1, tỉnh/trường 2 slot. Xem evidence_uncertainty trong từng hàng để biết ngữ cảnh/hình/bảng còn thiếu.

Đây là độ hợp lý của lỗi do model đánh giá, chưa phải lỗi thường gặp được đo trên học sinh. Không suy rộng tỷ lệ của phần đã xác nhận khóa sang các đề chưa có khóa. Mục chưa xác minh có thể chứa lựa chọn chưa biết đúng/sai, không phải số phương án sai đã xác nhận.

**Câu chùm và thứ tự:**

Đã đọc cấu trúc 8/8 đề; có chùm nhiều câu/xuyên phần được quan sát ở chính thức 2, tỉnh/trường 1. Các ý TF trong một câu được giữ riêng với chùm nhiều câu.
- Chính thức: P1 → P2 → P3, quan sát ở 2 đề.
- Tỉnh/trường: P1 → P2 → P3, quan sát ở 6 đề.

Thứ tự quan sát không tự trở thành luật cố định. Xem [audit cấu trúc](../../audit/block-structure.md) để phân biệt canonical, hoán vị và vị trí tự do.

**Truy nguyên:** [rows](rows.json), [phân bố](distributions.json), [compact](profile.compact.json), [cấu trúc từng đề](paper-structures.json), [kiểm định](verification.json).
