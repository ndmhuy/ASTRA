# Hồ sơ toan

**Hồ sơ ra đề chưa được nghiệm thu đầy đủ. Tình trạng từng thành phần được ghi bên dưới; có tệp kết quả không đồng nghĩa đã hoàn chỉnh.**

Trích xuất và aggregate đã qua kiểm kỹ thuật; nhận định vẫn chờ giáo viên rà.

[Đọc cách hỏi theo từng chủ đề](TOPICS.md)

**Các phần của hồ sơ:**

- [Hồ sơ tích hợp và mục lục từng chủ đề](PROFILE.md) — đã có bản, còn chờ rà.
- [Audit ma trận](../../audit/matrices/toan.md) — đã có bản, còn chờ rà.
- [Audit prototype](../../audit/prototypes/toan.md) — đã có bản, còn chờ rà.
- [NB/TH/VD](LEVELS.md) — đã có bản, còn chờ rà.
- [Câu mẫu mới](SAMPLES.md) — đã có bản, còn chờ rà.
- [Kiểm tra bổ sung bằng số học và bản in](../../audit/prototypes/toan-parent-review.md) — đã có bản, còn chờ rà.

**Bằng chứng:** chính thức 2 đề; tỉnh/trường 20 đề; 748 câu/ý được gắn nhãn. Model EXTRACT: gpt-6.1-sol. Hai nguồn được tổng hợp riêng.
Khóa khớp đã chấp nhận: chính thức 2/2, tỉnh/trường 10/20.

**Lớp kiến thức xuất hiện — số đề phân biệt:**

| Nguồn / phần | Lớp 10 | Lớp 11 | Lớp 12 | Chưa rõ |
|---|---:|---:|---:|---:|
| Chính thức / P1 | 1/2 | 2/2 | 2/2 | 0/2 |
| Chính thức / P2 | 2/2 | 2/2 | 2/2 | 0/2 |
| Chính thức / P3 | 2/2 | 2/2 | 2/2 | 1/2 |
| Tỉnh/trường / P1 | 4/20 | 19/20 | 20/20 | 0/20 |
| Tỉnh/trường / P2 | 14/20 | 16/20 | 20/20 | 1/20 |
| Tỉnh/trường / P3 | 16/20 | 20/20 | 20/20 | 2/20 |

Một đề có thể chứa nhiều lớp; không cộng các cột thành tổng đề. Nhãn lớp và độ phân hóa do model nhận định.

**Cách dựng câu và phân hóa:**

- Chính thức: Buộc người giải tự chọn tọa độ, hình chiếu, lớp số học hoặc tập vị trí; biểu diễn mới phải làm bài toán đơn giản hơn nhưng vẫn bảo toàn điều kiện.
- Tỉnh/trường: Chọn biến, tọa độ, hình phụ, thiết diện, hình khai triển hoặc quỹ tích; dùng điều kiện gián tiếp khôi phục quan hệ trước khi tính. Đọc cấu trúc phương trình, hướng và điểm xuất phát trước khi thao tác.

**Mức phân hóa do model nhận định:**

| Nguồn | Thấp | Vừa | Cao | Chưa phán đoán |
|---|---:|---:|---:|---:|
| Chính thức | 39 | 23 | 6 | 0 |
| Tỉnh/trường | 402 | 209 | 63 | 6 |

Đếm theo câu/ý đã gắn nhãn; đây là độ phức tạp suy luận được nhận định, chưa phải độ phân hóa đo từ bài làm học sinh. Các cách dựng ở trên không mặc nhiên đều đạt mức cao.

**Dữ kiện thuộc lòng được dùng thế nào:**

| Nguồn | Hỏi trực tiếp | Cho làm gợi ý | Cần trong suy luận | Không dùng |
|---|---:|---:|---:|---:|
| Chính thức | 0 | 0 | 63 | 5 |
| Tỉnh/trường | 0 | 101 | 543 | 36 |

Các cột đếm câu/ý trong mẫu đã phân tích, không phải tần suất học sinh nhớ hoặc quên.

**Phương án nhiễu:**

- Chính thức / phương án MCQ: liên hệ được một kiểu nhầm cụ thể ở 67/72 mục đã phán đoán (93.1%); chưa xác minh 0.
- Chính thức / nhận định TF: liên hệ được một kiểu nhầm cụ thể ở 13/14 mục đã phán đoán (92.9%); chưa xác minh 0.
- Tỉnh/trường / phương án MCQ: liên hệ được một kiểu nhầm cụ thể ở 329/353 mục đã phán đoán (93.2%); chưa xác minh 487.
- Tỉnh/trường / nhận định TF: liên hệ được một kiểu nhầm cụ thể ở 48/56 mục đã phán đoán (85.7%); chưa xác minh 169.

Các mẫu số trên tách MCQ và TF. Chỉ tiêu distractors gộp trong bản aggregate lịch sử chứa cả hai, không được đọc như tỷ lệ riêng của phương án MCQ.

Chưa phán đoán được mức phân hóa ở chính thức 0, tỉnh/trường 6 slot. Xem evidence_uncertainty trong từng hàng để biết ngữ cảnh/hình/bảng còn thiếu.

Đây là độ hợp lý của lỗi do model đánh giá, chưa phải lỗi thường gặp được đo trên học sinh. Không suy rộng tỷ lệ của phần đã xác nhận khóa sang các đề chưa có khóa. Mục chưa xác minh có thể chứa lựa chọn chưa biết đúng/sai, không phải số phương án sai đã xác nhận.

**Câu chùm và thứ tự:**

Đã đọc cấu trúc 22/22 đề; có chùm nhiều câu/xuyên phần được quan sát ở chính thức 0, tỉnh/trường 0. Các ý TF trong một câu được giữ riêng với chùm nhiều câu.
- Chính thức: P1 → P2 → P3, quan sát ở 2 đề.
- Tỉnh/trường: P1 → P2 → P3, quan sát ở 20 đề.

Thứ tự quan sát không tự trở thành luật cố định. Xem [audit cấu trúc](../../audit/block-structure.md) để phân biệt canonical, hoán vị và vị trí tự do.

**Truy nguyên:** [rows](rows.json), [phân bố](distributions.json), [compact](profile.compact.json), [cấu trúc từng đề](paper-structures.json), [kiểm định](verification.json).
