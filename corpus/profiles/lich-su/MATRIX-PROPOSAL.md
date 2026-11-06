# Đề xuất ma trận — prototype revised, 2026-11-04

Giữ hình dạng tổng quan sát: 24 MCQ P1 + 4 câu đúng/sai P2 = 28 câu in, 40 đơn vị trả lời nguyên tử. Đây là prototype nghiên cứu, không phải quota đã được phê duyệt và không ghi đè mặc định sản phẩm.

| Phần | Topic ID | Mức trên selection | Slot (accepted sample ID) | Số câu |
|---|---|---|---|---:|
| P1 | LS-T01 | NB | P1/10 (LS-S-004) | 1 |
| P1 | LS-T02 | NB | P1/15 (LS-F-002) | 1 |
| P1 | LS-T02 | TH | P1/16 (LS-F-003) | 1 |
| P1 | LS-T03 | NB | P1/17 (LS-F-005) | 1 |
| P1 | LS-T03 | TH | P1/18 (LS-F-006) | 1 |
| P1 | LS-T04 | NB | P1/2 (LS-F-007) | 1 |
| P1 | LS-T04 | TH | P1/19 (LS-F-008) | 1 |
| P1 | LS-T05 | NB | P1/6 (LS-F-009) | 1 |
| P1 | LS-T06 | NB | P1/11 (LS-S-007) | 1 |
| P1 | LS-T06 | TH | P1/20 (LS-F-010) | 1 |
| P1 | LS-T07 | TH | P1/21 (LS-F-012) | 1 |
| P1 | LS-T08 | NB | P1/13 (LS-S-013) | 1 |
| P1 | LS-T08 | TH | P1/22 (LS-F-014) | 1 |
| P1 | LS-T09 | NB | P1/23 (LS-F-016) | 1 |
| P1 | LS-T09 | TH | P1/24 (LS-F-017) | 1 |
| P1 | LS-T12 | VD | P1/12 (LS-V-005) | 1 |
| P1 | LS-T13 | NB | P1/1 (LS-F-022) | 1 |
| P1 | LS-T14 | NB | P1/3 (LS-F-024) | 1 |
| P1 | LS-T16 | NB | P1/14 (LS-S-016) | 1 |
| P1 | LS-T18 | NB | P1/4 (LS-F-032) | 1 |
| P1 | LS-T19 | NB | P1/5 (LS-F-033) | 1 |
| P1 | LS-T21 | NB | P1/9 (LS-S-001) | 1 |
| P1 | LS-T23 | TH | P1/7 (LS-F-039) | 1 |
| P1 | LS-T24 | NB | P1/8 (LS-F-041) | 1 |
| P2 | LS-T01 | NB/TH/VD | P2/2 (LS-V-001) | 1 |
| P2 | LS-T06 | NB/TH/VD | P2/3 (LS-V-003) | 1 |
| P2 | LS-T12 | NB/TH/VD | P2/4 (LS-V-006) | 1 |
| P2 | LS-T17 | NB/TH/VD | P2/1 (LS-F-031) | 1 |

P1 gồm 24 MCQ; P2 gồm 4 câu × 4 ý. Điểm minh họa: 24×0,25 + 4×tối đa 1 = **10 điểm**. Cơ chế điểm TF là giả định nghiên cứu, cần xác nhận theo quy chế kỳ thi đích.

## Coverage: observed và prospective

Coverage ledger scoped ghi **64/67 ô covered_model_checked**; 3 ô còn thiếu đều là MCQ P1 mức VD ở LS-T06, LS-T08 và LS-T16. Đây là ô cần review/bổ sung nếu muốn bao phủ, không phải quota VD đã được chứng minh. Không tạo câu hay gán mức để làm đầy các ô này.

Trong 67 ô, 39 chỉ có căn cứ observed, 23 có cả observed và proposed, 5 là proposed-only; trong 5 ô proposed-only có 2 covered_model_checked và 3 missing. Các con số quan sát mô tả nguồn hiện có; proposed mô tả lựa chọn prototype, không được cộng nhập để tuyên bố tần suất thực nghiệm.

## Mức và source judgments

Selection có 24 nhãn câu MCQ và 16 mức ý đúng/sai (40 đơn vị). Hai đánh giá nguồn nhắm tới được giữ đúng như hiện tại: `686833f78102|P2|3|c` VD và `dff65825f390|P2|4|d` VD. Chúng là đánh giá reasoning trên hai câu nguồn, không phải chứng nhận đáp án official; không thay đổi nhãn trong selection từ các đánh giá này.

Mức reviewer vẫn bảo thủ và chờ giáo viên adjudicate. Các quota VD P1 cũ không có đủ hỗ trợ để khẳng định; 3 ô còn thiếu không được giả thành quota.

Chi tiết audit mặc định và source counts vẫn ở [MATRIX-AUDIT](MATRIX-AUDIT.md) và [matrix-audit-current.json](../../data/matrix-audit-current.json). Chi tiết selection/coverage/source judgments: [matrix-proposal-current.json](../../data/matrix-proposal-current.json).
