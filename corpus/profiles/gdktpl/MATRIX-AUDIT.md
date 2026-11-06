# Audit ma trận mặc định — dữ liệu hiện tại 2026-11-04

Chủ đề và số lượng dưới đây giữ nguyên cách viết từ snapshot `audit/outputs/defaults-snapshot.json` (SHA-256 `4c810e759de0ec366b3a1d1ab1f3cb1c833359aea70a1cf9a031cd58e4da6f45`). Đây là snapshot nghiên cứu, không phải xác nhận cấu hình đang triển khai.

Số đề là **paper có nhãn chủ đề ánh xạ trong cùng phần**, không phải số câu của ô. NB/TH/VD đếm dòng quan sát nguồn nguyên tử riêng; không được đồng nhất với số câu mặc định, nhất là câu đúng/sai P2. Nhãn nguồn là working model tags, không phải tần suất đã chứng nhận hay độ khó thực nghiệm. Không suy quota từ việc một chủ đề xuất hiện.

| Phần | Chủ đề baseline (nguyên văn) | Mức | Số câu baseline | Topic IDs ánh xạ | Official papers | Provincial papers | Atomic rows NB/TH/VD |
|---|---|---:|---:|---|---:|---:|---|
| P1 | Quyền và nghĩa vụ công dân | NB | 2 | T01, T02, T03, T04, T05 | 0 | 14 | 46/65/0 |
| P1 | Quyền và nghĩa vụ công dân | TH | 2 | T01, T02, T03, T04, T05 | 0 | 14 | 46/65/0 |
| P1 | Tăng trưởng và phát triển kinh tế | NB | 2 | T06, T07, T08, T09 | 0 | 14 | 49/31/0 |
| P1 | Tăng trưởng và phát triển kinh tế | TH | 2 | T06, T07, T08, T09 | 0 | 14 | 49/31/0 |
| P1 | Pháp luật quốc tế | NB | 2 | T12, T13, T21 | 0 | 10 | 6/13/0 |
| P1 | Pháp luật quốc tế | TH | 1 | T12, T13, T21 | 0 | 10 | 6/13/0 |
| P1 | Pháp luật quốc tế | VD | 1 | T12, T13, T21 | 0 | 10 | 6/13/0 |
| P1 | Hội nhập kinh tế quốc tế | NB | 2 | T10, T11 | 0 | 13 | 9/25/0 |
| P1 | Hội nhập kinh tế quốc tế | TH | 1 | T10, T11 | 0 | 13 | 9/25/0 |
| P1 | Hội nhập kinh tế quốc tế | VD | 1 | T10, T11 | 0 | 13 | 9/25/0 |
| P1 | Quản lí thu chi và kinh doanh | NB | 2 | T14, T15, T16, T20 | 0 | 14 | 20/50/0 |
| P1 | Quản lí thu chi và kinh doanh | TH | 1 | T14, T15, T16, T20 | 0 | 14 | 20/50/0 |
| P1 | Quản lí thu chi và kinh doanh | VD | 1 | T14, T15, T16, T20 | 0 | 14 | 20/50/0 |
| P1 | Bảo hiểm và an sinh xã hội | NB | 2 | T17, T18 | 0 | 11 | 10/13/0 |
| P1 | Bảo hiểm và an sinh xã hội | TH | 1 | T17, T18 | 0 | 11 | 10/13/0 |
| P1 | Bảo hiểm và an sinh xã hội | VD | 1 | T17, T18 | 0 | 11 | 10/13/0 |
| P2 | Quyền và nghĩa vụ công dân | TH | 1 | T01, T02, T03, T04, T05 | 0 | 13 | 1/55/0 |
| P2 | Tăng trưởng và phát triển kinh tế | TH | 1 | T06, T07, T08, T09 | 0 | 12 | 2/33/0 |
| P2 | Pháp luật quốc tế | TH | 1 | T12, T13, T21 | 0 | 11 | 2/32/1 |
| P2 | Hội nhập kinh tế quốc tế | TH | 1 | T10, T11 | 0 | 10 | 1/32/0 |

Bản ghi đầy đủ, gồm raw baseline spelling/counts và phạm vi giới hạn: [matrix-audit-current.json](../../data/matrix-audit-current.json).

## Kết luận

Giữ hình dạng tổng đã quan sát và rà soát các chủ đề còn thiếu. Không dùng số paper để suy quota; không tuyên bố mức câu c/d của TF mặc định là VD chỉ từ vị trí ý. GDKTPL không có corpus official trong tập này; không khái quát số tỉnh thành tần suất toàn quốc.

Trạng thái sử dụng hiện hành 06/11/2026: xem [USABILITY-REVIEW](USABILITY-REVIEW.md). Nội dung thiếu bằng chứng không bị coi là sai; nhãn teacher_approved=false mô tả provenance, không tạo yêu cầu chờ giáo viên.
