# Hồ sơ sinh-hoc

**Hồ sơ ra đề chưa được nghiệm thu đầy đủ. Tình trạng từng thành phần được ghi bên dưới; có tệp kết quả không đồng nghĩa đã hoàn chỉnh.**

Trích xuất và aggregate đã qua kiểm kỹ thuật; nhận định vẫn chờ giáo viên rà.

[Đọc cách hỏi theo từng chủ đề](TOPICS.md)

**Các phần của hồ sơ:**

- [Audit ma trận](../../audit/matrices/sinh-hoc.md) — đã có bản, còn chờ rà.
- [Audit prototype](../../audit/prototypes/sinh-hoc.md) — đã có bản, còn chờ rà.
- [NB/TH/VD](LEVELS.md) — đã có bản, còn chờ rà.
- [Câu mẫu mới](SAMPLES.md) — đã có bản, còn chờ rà.

**Bằng chứng:** chính thức 1 đề; tỉnh/trường 5 đề; 240 câu/ý được gắn nhãn. Model EXTRACT: gpt-6.1-sol. Hai nguồn được tổng hợp riêng.
Khóa khớp đã chấp nhận: chính thức 1/1, tỉnh/trường 5/5.

**Lớp kiến thức xuất hiện — số đề phân biệt:**

| Nguồn / phần | Lớp 10 | Lớp 11 | Lớp 12 | Chưa rõ |
|---|---:|---:|---:|---:|
| Chính thức / P1 | 1/1 | 1/1 | 1/1 | 0/1 |
| Chính thức / P2 | 0/1 | 1/1 | 1/1 | 0/1 |
| Chính thức / P3 | 1/1 | 1/1 | 1/1 | 0/1 |
| Tỉnh/trường / P1 | 5/5 | 5/5 | 5/5 | 0/5 |
| Tỉnh/trường / P2 | 1/5 | 5/5 | 5/5 | 0/5 |
| Tỉnh/trường / P3 | 1/5 | 0/5 | 5/5 | 0/5 |

Một đề có thể chứa nhiều lớp; không cộng các cột thành tổng đề. Nhãn lớp và độ phân hóa do model nhận định.

**Cách dựng câu và phân hóa:**

- Chính thức: Cho dữ liệu phân tử có định hướng và quy ước xử lí sản phẩm; yêu cầu liên kết mạch khuôn, bản phiên mã, khung đọc và sản phẩm hoàn chỉnh. Điểm phân hóa nằm ở sự nhất quán của cả chuỗi suy luận.
- Tỉnh/trường: Cho dữ liệu quan sát thay mô hình hoàn chỉnh; yêu cầu suy trạng thái trung gian, kiểm tra mô hình cạnh tranh rồi mới dùng cho bước tiếp theo. Không mặc định quy luật quen thuộc khi trái dữ kiện.

Nguồn chính thức ít: mô tả quan sát, chưa suy ra quy luật tần suất phổ quát.

**Mức phân hóa do model nhận định:**

| Nguồn | Thấp | Vừa | Cao | Chưa phán đoán |
|---|---:|---:|---:|---:|
| Chính thức | 21 | 11 | 3 | 5 |
| Tỉnh/trường | 100 | 71 | 19 | 10 |

Đếm theo câu/ý đã gắn nhãn; đây là độ phức tạp suy luận được nhận định, chưa phải độ phân hóa đo từ bài làm học sinh. Các cách dựng ở trên không mặc nhiên đều đạt mức cao.

**Dữ kiện thuộc lòng được dùng thế nào:**

| Nguồn | Hỏi trực tiếp | Cho làm gợi ý | Cần trong suy luận | Không dùng |
|---|---:|---:|---:|---:|
| Chính thức | 0 | 24 | 2 | 14 |
| Tỉnh/trường | 1 | 57 | 86 | 56 |

Các cột đếm câu/ý trong mẫu đã phân tích, không phải tần suất học sinh nhớ hoặc quên.

**Phương án nhiễu:**

- Chính thức: liên hệ được một kiểu nhầm cụ thể ở 54/59 phương án đã phán đoán (91.5%); chưa xác minh 4.
- Tỉnh/trường: liên hệ được một kiểu nhầm cụ thể ở 306/313 phương án đã phán đoán (97.8%); chưa xác minh 12.

Chưa phán đoán được mức phân hóa ở chính thức 5, tỉnh/trường 10 slot. Xem evidence_uncertainty trong từng hàng để biết ngữ cảnh/hình/bảng còn thiếu.

Đây là độ hợp lý của lỗi do model đánh giá, chưa phải lỗi thường gặp được đo trên học sinh. Không suy rộng tỷ lệ của phần đã xác nhận khóa sang các đề chưa có khóa. Mục chưa xác minh có thể chứa lựa chọn chưa biết đúng/sai, không phải số phương án sai đã xác nhận.

**Câu chùm và thứ tự:**

Đã đọc cấu trúc 6/6 đề; có chùm nhiều câu/xuyên phần được quan sát ở chính thức 0, tỉnh/trường 0. Các ý TF trong một câu được giữ riêng với chùm nhiều câu.
- Chính thức: P1 → P2 → P3, quan sát ở 1 đề.
- Tỉnh/trường: P1 → P2 → P3, quan sát ở 5 đề.

Thứ tự quan sát không tự trở thành luật cố định. Xem [audit cấu trúc](../../audit/block-structure.md) để phân biệt canonical, hoán vị và vị trí tự do.

**Truy nguyên:** [rows](rows.json), [phân bố](distributions.json), [compact](profile.compact.json), [cấu trúc từng đề](paper-structures.json), [kiểm định](verification.json).

## Rà danh pháp

[Danh pháp và ghi chú của môn](TERMINOLOGY.md) · [Báo cáo Luna và quy tắc chung](../../audit/terminology/REPORT.md).
