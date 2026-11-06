# Mức nhận thức theo level-scheme

Baseline [level-scheme](evidence/baseline/level-scheme.json), revision `de8c614ada6e3ae9f9072cedb7521fb96c1d13e5`, mặc định v2. **NB:** gọi tên/nhớ một đơn vị kiến thức. **TH:** giải thích, phân biệt, đọc và diễn giải niên biểu/tư liệu theo quan hệ quen thuộc. **VD:** thiết kế, kiểm định hoặc sửa một giải thích lịch sử bằng chuỗi lập luận, kết hợp các mảnh kiến thức và giới hạn nhân quả/phạm vi. Bối cảnh thực tế, số mốc dài hay số phép suy luận thường quy không đủ để tự gắn VD.

Độ khó/phân hóa **thực nghiệm** cần dữ liệu bài làm; chữ “low/medium” trong phân tích cũ là nhận định model và KHÔNG quy đổi sang NB/TH/VD.

| Lớp nguồn | Phần | NB | TH | VD | Unknown | Đơn vị |
|---|---|---:|---:|---:|---:|---|
| official | P1 | 10 | 14 | 0 | 0 | câu |
| official | P2 | 0 | 3 | 0 | 1 | câu tổng |
| provincial_third_party | P1 | 20 | 28 | 0 | 72 | câu |
| provincial_third_party | P2 | 0 | 6 | 2 | 12 | câu tổng |

Các hàng P2 trong bảng trên tính **mức tổng câu theo proxy cũ**, không cộng vào 240 nhãn ý. Đơn vị chuẩn với TF là `(P2,idx,sub)`; mức toàn câu lấy **max NB < TH < VD** của 4 ý nếu xác định đủ, nếu còn một ý unknown thì whole question unknown. Nhánh tự chọn (không thấy trong 6 đề) nếu có phải thống kê riêng.

Nhận định mức cũ là partial; 72/120 MCQ tỉnh và 12/20 câu TF tỉnh chưa xác định mức toàn câu theo bảng trên. Không ép phân loại cho đủ số lượng.

[Dữ liệu từng địa chỉ](data/level-observations.json).

## Số liệu phân tích OCR hiện hành — 2026-11-04

Bảng đầu tài liệu là thống kê kế thừa (proxy toàn câu của hồ sơ trước), không còn là số liệu hiện hành. Dữ liệu hiện hành phân loại từng hàng/ý; P2 được giữ theo ý atomic, không gộp thành câu in. Mọi nhãn dưới đây là nhận định model trên OCR, chưa được giáo viên xác nhận.

| Lớp nguồn / phần | NB | TH | VD | Unknown |
|---|---:|---:|---:|---:|
| official / P1 | 17 | 7 | 0 | 0 |
| official / P2 | 3 | 13 | 0 | 0 |
| provincial_third_party / P1 | 70 | 49 | 0 | 1 |
| provincial_third_party / P2 | 20 | 57 | 3 | 0 |

Tổng nguồn hiện hành: 240 hàng ở 6 đề (1 official, 5 provincial); 1 hàng unknown được giữ nguyên. 65 câu mẫu mới đều có đáp án khớp giải lại; chỉ 1 ý được xếp VD trong ngân hàng, và việc đó không lấp bất cứ ô VD nào còn mở.

Ma trận 67 ô: 59 covered_model_checked, 8 missing. Không thúc ép câu mẫu lên VD để đóng ô. Xem [rà soát nhận thức](COGNITIVE-REVIEW.md) và [dữ liệu nguồn](data/source-observations-current.json).
