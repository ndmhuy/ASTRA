# Đề xuất ma trận — prototype revised, 2026-11-04

Giữ hình dạng tổng đã quan sát; đây là proposal nghiên cứu, không phải quota đã được giáo viên phê duyệt và không ghi đè mặc định sản phẩm. Chủ đề/level dưới đây lấy từ selection ledger đang có; mức chưa xác nhận không được tự suy thêm.

| Phần | Topic ID | Mức reviewed trong selection | Slot (sample ID) | Số câu |
|---|---|---|---|---:|
| P1 | T01 | TH | P1/1 (KT-F-001) | 1 |
| P1 | T02 | NB | P1/2 (KT-F-013) | 1 |
| P1 | T03 | NB | P1/3 (S-MCQ-02) | 1 |
| P1 | T03 | TH | P1/22 (KT-F-015) | 1 |
| P1 | T04 | NB | P1/4 (KT-F-003) | 1 |
| P1 | T05 | NB | P1/5 (KT-F-007) | 1 |
| P1 | T05 | TH | P1/19 (KT-F-002) | 1 |
| P1 | T06 | NB | P1/6 (S-MCQ-05) | 1 |
| P1 | T06 | TH | P1/21 (KT-F-014) | 1 |
| P1 | T07 | NB | P1/7 (S-MCQ-06) | 1 |
| P1 | T07 | TH | P1/20 (KT-F-004) | 1 |
| P1 | T08 | NB | P1/8 (KT-F-006) | 1 |
| P1 | T09 | NB | P1/9 (KT-F-021) | 1 |
| P1 | T10 | NB | P1/10 (KT-F-026) | 1 |
| P1 | T11 | VD | P1/11 (KT-F-027) | 1 |
| P1 | T12 | NB | P1/12 (S-MCQ-09) | 1 |
| P1 | T13 | VD | P1/13 (KT-F-030) | 1 |
| P1 | T14 | NB | P1/14 (KT-F-022) | 1 |
| P1 | T15 | TH | P1/15 (KT-F-005) | 1 |
| P1 | T16 | VD | P1/16 (KT-F-031) | 1 |
| P1 | T17 | NB | P1/17 (S-MCQ-21) | 1 |
| P1 | T18 | VD | P1/18 (KT-F-032) | 1 |
| P1 | T19 | NB | P1/23 (KT-X-001) | 1 |
| P1 | T19 | TH | P1/24 (KT-X-002) | 1 |
| P2 | T05 | TH/VD | P2/3 (KT-F-024) | 1 |
| P2 | T06 | NB/TH/VD | P2/1 (KT-F-025) | 1 |
| P2 | T11 | TH/VD | P2/4 (KT-F-028) | 1 |
| P2 | T13 | NB/TH/VD | P2/2 (KT-X-010) | 1 |

P1: 24 MCQ; P2: 4 câu TF (16 ý); tổng 28 câu in, 40 đáp án nguyên tử. Điểm minh họa: 24×0,25 + 4×tối đa 1 = 10.

Bảng selection là snapshot prototype ngày 04/11, không phải ma trận tự cập nhật theo ngân hàng hiện hành. Ngày 06/11 KT-F-031 đã được hạ về TH theo yêu cầu tối thiểu; ô T16/P1/VD vì thế còn thiếu mẫu, nhưng câu vẫn dùng được. Không yêu cầu giáo viên adjudicate; không dùng bảng cũ để khẳng định đã đủ quota VD.

Không mặc định ý c/d của TF là VD. Câu tổng hợp phải lấy mức cao nhất từ các ý đã review; nếu thiếu căn cứ, giữ unknown/chờ duyệt. Điểm TF tối đa 1 là giả định nghiên cứu, cần xác nhận theo quy chế chấm đích.

GDKTPL: tập nguồn hiện tại không có đề official; không khái quát số tỉnh thành tần suất. T19 (thiết chế) là khoảng trống baseline thực sự, không gộp vào nhóm quyền công dân.

Chi tiết selection ledger và quyết định: [matrix-proposal-current.json](../../data/matrix-proposal-current.json).

Trạng thái sử dụng hiện hành 06/11/2026: xem [USABILITY-REVIEW](USABILITY-REVIEW.md). Nội dung thiếu bằng chứng không bị coi là sai; nhãn teacher_approved=false mô tả provenance, không tạo yêu cầu chờ giáo viên.
