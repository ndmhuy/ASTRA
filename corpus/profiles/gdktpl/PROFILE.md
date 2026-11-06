# Hồ sơ ra đề — Giáo dục kinh tế và pháp luật

**73 mẫu được agent duyệt để lấy dùng theo phạm vi dữ kiện; 21 hướng dẫn chủ đề.** Bắt đầu tại [Duyệt sử dụng](USABILITY-REVIEW.md), [Mẫu](SAMPLES.md), [Chủ đề](TOPICS.md) hoặc [ngân hàng JSON](data/samples-current.json). Không yêu cầu một lượt giáo viên duyệt nữa; `teacher_approved` vẫn false để mô tả đúng người đã kiểm.

Có 560 hàng nguồn từ 14 đề tỉnh, 0 đề official: 160 full-OCR/Sol, 400 structured Luna triage, trong đó39 flagged Sol adjudications. Lượt duyệt sử dụng này không biến toàn bộ thành560 câu đã giải lại; khóa nguồn và một số nhãn còn thiếu bằng chứng được giữ riêng.

Coverage mẫu đúng mức hiện là **76/77 ô mục tiêu**. KT-F-031 được sửa rõ dòng tiền và hạ VD→TH; ô đề xuất T16/P1/VD chưa có mẫu thay thế. Câu vẫn dùng được ở TH, không bị loại. Không suy từ coverage thành độ phủ đầy đủ chương trình hay độ khó thực nghiệm.

[Tiêu chí](CRITERIA.md) · [Mức](LEVELS.md) · [Coverage](COVERAGE.csv) · [QA](QA.md) · [Nguồn](SOURCES.md) · [Nguồn luật](LEGAL-CONTEXT-20261106.json) · [Prototype audit](PROTOTYPE-AUDIT.md).

Prototype revised đã compile và layout-pass theo [biên nhận](prototype-revised/verification.json). 28 câu chọn từ mẫu ban đầu đã có lượt giải trước; source original không bị sửa. Lượt này không chạy runtime hay thay PDF. Adapter S-C2 Tier C đang xuất nguồn và câu chùm, chưa xuất73 mẫu dossier. Tính dùng được của tài liệu và khả năng tự nhúng vào app được ghi tách biệt.
