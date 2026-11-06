# Audit ma trận mặc định — dữ liệu hiện tại 2026-11-04

Chủ đề và số lượng dưới đây giữ nguyên cách viết từ snapshot `audit/outputs/defaults-snapshot.json` (SHA-256 `4c810e759de0ec366b3a1d1ab1f3cb1c833359aea70a1cf9a031cd58e4da6f45`). Đây là snapshot nghiên cứu, không phải xác nhận cấu hình đang triển khai.

Số đề là **paper có nhãn chủ đề ánh xạ trong cùng phần**, không phải số câu của ô. NB/TH/VD đếm dòng quan sát nguồn nguyên tử riêng; không được đồng nhất với số câu mặc định, nhất là câu đúng/sai P2. Nhãn nguồn là working model tags, không phải tần suất đã chứng nhận hay độ khó thực nghiệm. Không suy quota từ việc một chủ đề xuất hiện.

| Phần | Chủ đề baseline (nguyên văn) | Mức | Số câu baseline | Topic IDs ánh xạ | Official papers | Provincial papers | Atomic rows NB/TH/VD |
|---|---|---:|---:|---|---:|---:|---|
| P1 | Este – lipit | NB | 2 | T01 | 2 | 4 | 3/6/0 |
| P1 | Este – lipit | TH | 1 | T01 | 2 | 4 | 3/6/0 |
| P1 | Cacbohiđrat | NB | 2 | T02 | 1 | 6 | 9/3/0 |
| P1 | Cacbohiđrat | TH | 1 | T02 | 1 | 6 | 9/3/0 |
| P1 | Hợp chất chứa nitơ | NB | 2 | T03 | 2 | 5 | 8/7/0 |
| P1 | Hợp chất chứa nitơ | TH | 1 | T03 | 2 | 5 | 8/7/0 |
| P1 | Polime | NB | 2 | T04 | 1 | 5 | 5/3/0 |
| P1 | Polime | TH | 1 | T04 | 1 | 5 | 5/3/0 |
| P1 | Pin điện và điện phân | NB | 1 | T05, T06 | 2 | 6 | 3/13/0 |
| P1 | Pin điện và điện phân | TH | 1 | T05, T06 | 2 | 6 | 3/13/0 |
| P1 | Kim loại | NB | 1 | T08, T09 | 2 | 5 | 10/11/0 |
| P1 | Kim loại | TH | 1 | T08, T09 | 2 | 5 | 10/11/0 |
| P1 | Nguyên tố nhóm IA, IIA và kim loại chuyển tiếp | NB | 1 | T07, T10 | 2 | 5 | 5/10/0 |
| P1 | Nguyên tố nhóm IA, IIA và kim loại chuyển tiếp | TH | 1 | T07, T10 | 2 | 5 | 5/10/0 |
| P2 | Este – lipit | TH | 1 | T01 | 1 | 4 | 4/14/0 |
| P2 | Cacbohiđrat | TH | 1 | T02 | 1 | 1 | 1/7/0 |
| P2 | Hợp chất chứa nitơ | TH | 1 | T03 | 1 | 3 | 0/12/0 |
| P2 | Polime | TH | 1 | T04 | 2 | 3 | 4/14/1 |
| P3 | Este – lipit | VD | 1 | T01 | 1 | 2 | 1/2/0 |
| P3 | Cacbohiđrat | VD | 1 | T02 | 1 | 4 | 1/3/1 |
| P3 | Hợp chất chứa nitơ | VD | 1 | T03 | 1 | 3 | 0/4/1 |
| P3 | Polime | VD | 1 | T04 | 1 | 2 | 1/2/0 |
| P3 | Pin điện và điện phân | VD | 1 | T05, T06 | 1 | 4 | 0/6/1 |
| P3 | Kim loại | VD | 1 | T08, T09 | 1 | 6 | 2/5/3 |

Bản ghi đầy đủ, gồm raw baseline spelling/counts và phạm vi giới hạn: [matrix-audit-current.json](../../data/matrix-audit-current.json).

## Kết luận

Giữ hình dạng tổng đã quan sát và rà soát các chủ đề còn thiếu. Không dùng số paper để suy quota; không tuyên bố mức câu c/d của TF mặc định là VD chỉ từ vị trí ý. GDKTPL không có corpus official trong tập này; không khái quát số tỉnh thành tần suất toàn quốc.
