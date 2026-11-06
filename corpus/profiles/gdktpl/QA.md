# QA — trạng thái hồ sơ GDKTPL hiện hành

## Kết quả đọc được từ scoped source data

| Hạng mục | Kết quả |
|---|---:|
| Đơn vị nguồn | 560/560 rows |
| Quy trình phân loại | 160 full-OCR/Sol; 400 Luna triage; trong đó 39 flagged Sol adjudications |
| Đề provincial_third_party | 14 |
| Đề official | 0 |
| Nhãn mức đang làm việc | NB 156; TH 399; VD 1; Unknown 4 |
| Chủ đề có guide | 21/21 |
| Mẫu synthetic dùng được trong phạm vi | 73; agent-reviewed, không yêu cầu giáo viên duyệt tiếp |
| Coverage cells | 76/77 có sample link accepted; không phải source validation |
| Source keys independently validated | no / incomplete |
| Teacher approval / runtime test | no / no |
| Prototype compile/layout receipt | pass; [PDF](prototype-revised/prototype.pdf) · [verification](prototype-revised/verification.json) |

## Giới hạn

- Các 560 nhãn là kết quả đọc/triage theo quy trình đã ghi; không tuyên bố tất cả do Sol đọc đầy đủ, không teacher-certified, không dùng để khái quát tần suất đề thi.
- Tách rõ 14 đề tỉnh và 0 đề official. Không gọi đây là official baseline.
- 73 sample records là synthetic được agent duyệt theo phạm vi; 76/77 ô có mẫu đúng mức sau khi KT-F-031 hạ về TH; độ phủ này là độ phủ ví dụ synthetic, không chứng minh đầy đủ độ phủ chương trình hoặc corpus.
- T04/T05/T09/T11/T12/T13 có source rows giữ Unknown; xem [LEVELS](LEVELS.md).
- Prototype revised compile/layout QA passed. Its 28 selected new questions were model-checked; source original unchanged. This is not independent content/key validation or teacher acceptance. Source-key/legal review remains incomplete; runtime/generator parity has not been tested.
- T03 quyền giáo dục/di sản văn hóa/sức khỏe/bình đẳng hôn nhân; T07 văn hóa tiêu dùng; T13 tình trạng cư trú/quy chế ngoại giao được ghi thành subform rõ ràng, không gộp lại thành tag đếm cũ.

Trạng thái sử dụng hiện hành 06/11/2026: xem [USABILITY-REVIEW](USABILITY-REVIEW.md). Nội dung thiếu bằng chứng không bị coi là sai; nhãn teacher_approved=false mô tả provenance, không tạo yêu cầu chờ giáo viên.
