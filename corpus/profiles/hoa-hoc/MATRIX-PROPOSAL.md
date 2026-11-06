# Đề xuất ma trận — prototype revised, 2026-11-04

Giữ hình dạng tổng đã quan sát; đây là proposal nghiên cứu, không phải quota đã được giáo viên phê duyệt và không ghi đè mặc định sản phẩm. Bảng selection lấy nguyên topic ID, slot, sample ID và mức từ ledger hiện tại; cột căn cứ giữ riêng hai loại evidence.

| Phần | Topic ID | Mức | Căn cứ mức | Slot (sample ID / ref) | Câu | Ý mức đã gán |
|---|---|---|---|---|---:|---:|
| P1 | T01 | NB | ước lượng model legacy; không phải blind review mới | P1/5 (PROTO-P1-05) | 1 | 1 |
| P1 | T02 | TH | ước lượng model legacy; không phải blind review mới | P1/3 (PROTO-P1-03) | 1 | 1 |
| P1 | T03 | NB | ước lượng model legacy; không phải blind review mới | P1/2 (PROTO-P1-02), P1/8 (PROTO-P1-08), P1/17 (PROTO-P1-17) | 3 | 3 |
| P1 | T04 | NB | ước lượng model legacy; không phải blind review mới | P1/7 (PROTO-P1-07) | 1 | 1 |
| P1 | T05 | TH | ước lượng model legacy; không phải blind review mới | P1/4 (PROTO-P1-04) | 1 | 1 |
| P1 | T06 | TH | ước lượng model legacy; không phải blind review mới | P1/11 (PROTO-P1-11) | 1 | 1 |
| P1 | T07 | NB | ước lượng model legacy; không phải blind review mới | P1/1 (PROTO-P1-01) | 1 | 1 |
| P1 | T07 | TH | ước lượng model legacy; không phải blind review mới | P1/12 (PROTO-P1-12) | 1 | 1 |
| P1 | T08 | TH | ước lượng model legacy; không phải blind review mới | P1/18 (PROTO-P1-18) | 1 | 1 |
| P1 | T09 | TH | ước lượng model legacy; không phải blind review mới | P1/13 (PROTO-P1-13) | 1 | 1 |
| P1 | T10 | TH | ước lượng model legacy; không phải blind review mới | P1/9 (PROTO-P1-09) | 1 | 1 |
| P1 | T11 | TH | ước lượng model legacy; không phải blind review mới | P1/10 (PROTO-P1-10) | 1 | 1 |
| P1 | T15 | TH | review riêng, không khóa đáp án | P1/14 (HH-M20) | 1 | 1 |
| P1 | T16 | TH | review riêng, không khóa đáp án | P1/6 (HH-M21) | 1 | 1 |
| P1 | T17 | TH | review riêng, không khóa đáp án | P1/15 (HH-M22) | 1 | 1 |
| P1 | T19 | TH | review riêng, không khóa đáp án | P1/16 (HH-M23) | 1 | 1 |
| P2 | T01 | NB/TH | ước lượng model legacy; không phải blind review mới | P2/3 (PROTO-P2-03-a,PROTO-P2-03-b,PROTO-P2-03-c,PROTO-P2-03-d) | 1 | 4 |
| P2 | T02 | NB/TH | ước lượng model legacy; không phải blind review mới | P2/2 (PROTO-P2-02-a,PROTO-P2-02-b,PROTO-P2-02-c,PROTO-P2-02-d) | 1 | 4 |
| P2 | T06 | NB/TH | ước lượng model legacy; không phải blind review mới | P2/1 (PROTO-P2-01-a,PROTO-P2-01-b,PROTO-P2-01-c,PROTO-P2-01-d) | 1 | 4 |
| P2 | T13 | NB/TH | ước lượng model legacy; không phải blind review mới | P2/4 (PROTO-P2-04-a,PROTO-P2-04-b,PROTO-P2-04-c,PROTO-P2-04-d) | 1 | 4 |
| P3 | T01 | TH | ước lượng model legacy; không phải blind review mới | P3/2 (PROTO-P3-02) | 1 | 1 |
| P3 | T01 | VD | review riêng, không khóa đáp án | P3/3 (HH-N-6372ec510266) | 1 | 1 |
| P3 | T02 | VD | review riêng, không khóa đáp án | P3/4 (HH-N-794e3a30c695) | 1 | 1 |
| P3 | T03 | VD | review riêng, không khóa đáp án | P3/5 (HH-N-a2cd9d0a688a) | 1 | 1 |
| P3 | T04 | TH | ước lượng model legacy; không phải blind review mới | P3/1 (PROTO-P3-01) | 1 | 1 |
| P3 | T04 | VD | review riêng, không khóa đáp án | P3/6 (HH-F-bb9a43e05e8a) | 1 | 1 |

**Tổng hình dạng và điểm minh họa:** P1 18 MCQ × 0,25 = 4,50; P2 4 TF × tối đa 1,00 = 4,00; P3 6 trả lời ngắn × 0,25 = 1,50. Tổng 28 câu in, 40 ô mức/đáp án nguyên tử, 10,00 điểm. Rubric TF là giả định nghiên cứu, cần xác nhận theo quy chế chấm đích.

8 câu thay thế có mức từ review riêng, không khóa đáp án. 20 câu giữ nội dung gốc có mức ước lượng model legacy; chỉnh sửa biên tập và bố cục được kiểm riêng, nhưng không biến các mức này thành blind review mới. Mức chưa phải độ khó thực nghiệm; teacher adjudication vẫn pending.

Không mặc định ý c/d của TF là VD. Mức câu tổng hợp chỉ lấy mức cao nhất từ các ý đã review; nếu thiếu căn cứ thì giữ unknown/chờ duyệt.

Chi tiết selection ledger và căn cứ từng slot: [matrix-proposal-current.json](../../data/matrix-proposal-current.json).
