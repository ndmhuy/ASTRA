# Hồ sơ lich-su

**Hồ sơ ra đề chưa được nghiệm thu đầy đủ. Tình trạng từng thành phần được ghi bên dưới; có tệp kết quả không đồng nghĩa đã hoàn chỉnh.**

Trích xuất và aggregate đã qua kiểm kỹ thuật; nhận định vẫn chờ giáo viên rà.

[Đọc cách hỏi theo từng chủ đề](/Users/huynguyen/Lecturing_Lab/wt-corpus-merged/profiles/lich-su/TOPICS.md)

**Các phần của hồ sơ:**

- [Audit ma trận](/Users/huynguyen/Lecturing_Lab/wt-corpus-merged/audit/matrices/lich-su.md) — đã có bản, còn chờ rà.
- [Audit prototype](/Users/huynguyen/Lecturing_Lab/wt-corpus-merged/audit/prototypes/lich-su.md) — đã có bản, còn chờ rà.
- [NB/TH/VD](/Users/huynguyen/Lecturing_Lab/wt-corpus-merged/profiles/lich-su/LEVELS.md) — đã có bản, còn chờ rà.
- Câu mẫu mới: đang bổ sung, chưa nghiệm thu.

**Bằng chứng:** chính thức 1 đề; tỉnh/trường 5 đề; 240 câu/ý được gắn nhãn. Model EXTRACT: gpt-6.1-sol. Hai nguồn được tổng hợp riêng.
Khóa khớp đã chấp nhận: chính thức 1/1, tỉnh/trường 5/5.

**Lớp kiến thức xuất hiện — số đề phân biệt:**

| Nguồn / phần | Lớp 10 | Lớp 11 | Lớp 12 | Chưa rõ |
|---|---:|---:|---:|---:|
| Chính thức / P1 | 0/1 | 1/1 | 1/1 | 0/1 |
| Chính thức / P2 | 1/1 | 1/1 | 1/1 | 0/1 |
| Tỉnh/trường / P1 | 0/5 | 5/5 | 5/5 | 0/5 |
| Tỉnh/trường / P2 | 0/5 | 0/5 | 5/5 | 0/5 |

Một đề có thể chứa nhiều lớp; không cộng các cột thành tổng đề. Nhãn lớp và độ phân hóa do model nhận định.

**Cách dựng câu và phân hóa:**

- Chính thức: Cho một giai đoạn, yêu cầu xác định đặc điểm phát triển; phải phân biệt khởi đầu quan hệ với mở rộng và nâng cao quan hệ, đồng thời loại nhiệm vụ thuộc giai đoạn trước. (Đối sánh trong mẫu; chưa khẳng định là dạng lặp giữa nhiều đề.)
- Tỉnh/trường: Nối những hiện tượng có liên hệ nhưng thay đổi trình tự hoặc vị trí điều kiện và kết quả; yêu cầu kiểm tra cả thời gian lẫn cơ chế.

Nguồn chính thức ít: mô tả quan sát, chưa suy ra quy luật tần suất phổ quát.

**Mức phân hóa do model nhận định:**

| Nguồn | Thấp | Vừa | Cao | Chưa phán đoán |
|---|---:|---:|---:|---:|
| Chính thức | 22 | 18 | 0 | 0 |
| Tỉnh/trường | 121 | 79 | 0 | 0 |

Đếm theo câu/ý đã gắn nhãn; đây là độ phức tạp suy luận được nhận định, chưa phải độ phân hóa đo từ bài làm học sinh. Các cách dựng ở trên không mặc nhiên đều đạt mức cao.

**Dữ kiện thuộc lòng được dùng thế nào:**

| Nguồn | Hỏi trực tiếp | Cho làm gợi ý | Cần trong suy luận | Không dùng |
|---|---:|---:|---:|---:|
| Chính thức | 0 | 21 | 9 | 10 |
| Tỉnh/trường | 6 | 118 | 45 | 31 |

Các cột đếm câu/ý trong mẫu đã phân tích, không phải tần suất học sinh nhớ hoặc quên.

**Phương án nhiễu:**

- Chính thức: liên hệ được một kiểu nhầm cụ thể ở 71/81 phương án đã phán đoán (87.7%); chưa xác minh 0.
- Tỉnh/trường: liên hệ được một kiểu nhầm cụ thể ở 358/390 phương án đã phán đoán (91.8%); chưa xác minh 2.

Chưa phán đoán được mức phân hóa ở chính thức 0, tỉnh/trường 0 slot. Xem evidence_uncertainty trong từng hàng để biết ngữ cảnh/hình/bảng còn thiếu.

Đây là độ hợp lý của lỗi do model đánh giá, chưa phải lỗi thường gặp được đo trên học sinh. Không suy rộng tỷ lệ của phần đã xác nhận khóa sang các đề chưa có khóa. Mục chưa xác minh có thể chứa lựa chọn chưa biết đúng/sai, không phải số phương án sai đã xác nhận.

**Câu chùm và thứ tự:**

Đã đọc cấu trúc 6/6 đề; có chùm nhiều câu/xuyên phần được quan sát ở chính thức 0, tỉnh/trường 5. Các ý TF trong một câu được giữ riêng với chùm nhiều câu.
- Chính thức: P1 → P2, quan sát ở 1 đề.
- Tỉnh/trường: P1 → P2, quan sát ở 5 đề.

Thứ tự quan sát không tự trở thành luật cố định. Xem [audit cấu trúc](../../audit/block-structure.md) để phân biệt canonical, hoán vị và vị trí tự do.

**Truy nguyên:** [rows](rows.json), [phân bố](distributions.json), [compact](profile.compact.json), [cấu trúc từng đề](paper-structures.json), [kiểm định](verification.json).
