> **Lịch sử đánh giá:** các số/hold và yêu cầu giáo viên ở dưới thuộc đợt trước. Quyết định dùng hiện hành 06/11/2026 tại [USABILITY-REVIEW](USABILITY-REVIEW.md): 73 mẫu nội dung dùng được, bằng chứng mức được tách riêng; không có gate giáo viên mới.

# Rà soát nhận thức — ba ô VD còn mở

Tình trạng hiện hành: 70/70 mẫu được chấp nhận giải lại nhất quán trong lượt model không nhận khóa/mức đích; không có nghĩa các mẫu đã đạt mọi mức dự kiến. Coverage yêu cầu mức chính xác, nên 64/67 ô được hỗ trợ và 3 ô VD dưới đây vẫn mở. Không tự đổi nhãn VD cho mẫu gần ranh giới. Người duyệt có thể phân loại lại ô/cell theo tiêu chí hoặc yêu cầu câu mạnh hơn; chưa có phê duyệt nào được ghi nhận.

| Cell | Topic / phần / mức | Địa chỉ nguồn liên quan | Mẫu cùng topic/part để tham khảo |
|---|---|---|---|
| `CELL-be33f53d06ab` | LS-T06 — Cách mạng tháng Tám và kháng chiến chống thực dân Pháp; P1/VD | không có địa chỉ cùng ô trong đề đã đọc | [LS-S-007](samples/LS-S-007.md), [LS-S-008](samples/LS-S-008.md), [LS-S-009](samples/LS-S-009.md), [LS-F-010](samples/LS-F-010.md) |
| `CELL-be64831a7097` | LS-T08 — Công cuộc Đổi mới ở Việt Nam từ năm 1986; P1/VD | không có địa chỉ cùng ô trong đề đã đọc | [LS-S-013](samples/LS-S-013.md), [LS-S-014](samples/LS-S-014.md), [LS-S-015](samples/LS-S-015.md), [LS-F-014](samples/LS-F-014.md) |
| `CELL-1988a566675d` | LS-T16 — Lịch sử đối ngoại Việt Nam; P1/VD | không có địa chỉ cùng ô trong đề đã đọc | [LS-S-016](samples/LS-S-016.md), [LS-S-017](samples/LS-S-017.md), [LS-S-018](samples/LS-S-018.md), [LS-F-028](samples/LS-F-028.md) |

## Tác giả, reviewer và quyết định của người duyệt

Đợt bổ sung đã sinh câu cho các mục tiêu và có lượt model reviewer tách; kết quả được hợp nhất vào [ngân hàng cuối](data/scoped-final-bank.json), phần tác giả ở [scoped-author-revision1.json](data/scoped-author-revision1.json), input reviewer tại [scoped-review-revision1-input.json](data/scoped-review-revision1-input.json), và kết quả tại [scoped-review-revision1-result.json](data/scoped-review-revision1-result.json). Mẫu tương ứng được liên kết theo từng topic/part trong bảng; các file này không phải chữ ký duyệt của giáo viên.

## Quyết định cần để ngỏ

1. Giữ đúng ba cell ID ở trạng thái missing đến khi giáo viên chọn một trong hai hướng: (a) phân loại lại theo demand tối thiểu có căn cứ, nêu lý do; hoặc (b) yêu cầu tác giả viết tác vụ thực sự buộc lập chuỗi/quan hệ và loại bỏ đường tắt NB/TH.
2. Không gán VD theo ý định người viết, vị trí c/d, độ dài câu, hoặc nhãn cũ.
3. Giữ mơ hồ prototype tại `P2/1a`; quy ước D/Đ là cùng giá trị đúng/sai chỉ chuẩn hóa cách so khóa, không giải quyết mơ hồ nội dung. Xem [audit prototype](PROTOTYPE-AUDIT.md) và [audit quyết định](DECISIONS.md).
4. Phản hồi giáo viên có 7 ghi chú được ghi nhận; teacher feedback chưa đóng toàn bộ. Parent revised prototype đang chờ render, nên prototype review/render và mọi feedback follow-up vẫn pending.

### Hiện trạng feedback và prototype

[Bổ sung](BO-SUNG.md) ghi 5 nhận xét tổng quát và 2 Word comments. Các góp ý về độ phủ lớp/chủ đề (đặc biệt Hồ Chí Minh), VD, mức từng ý TF, nguồn, biên tập và câu chỉ hỏi niên đại cần tiếp tục được phân xử; việc ánh xạ không đồng nghĩa đã áp dụng hoặc đã đóng. Bản prototype revised là sản phẩm riêng, chưa có receipt render/duyệt để tuyên bố hoàn tất.


### Cập nhật lượt công bố 2026-11-04

Ngân hàng authority hiện có 70 mẫu được chấp nhận và ba bản nháp giữ riêng: `LS-V-002`, `LS-V-004`, `LS-V-007`. Ba ô VD còn mở là `CELL-be33f53d06ab` (LS-T06/P1), `CELL-be64831a7097` (LS-T08/P1), `CELL-1988a566675d` (LS-T16/P1). Năm mẫu mới có lời giải lại; các mức VD dưới đây là đề xuất có điều kiện, chưa đóng review shortcut:

| Mẫu | Ý VD | Rủi ro còn lại cần reviewer/giáo viên kiểm |
|---|---|---|
| [LS-V-001](samples/LS-V-001.md) | b | Ý b tự nêu gần đủ chuỗi lập luận; có thể thành TH nếu không cần huy động cả hai tuyến lịch sử. |
| [LS-V-003](samples/LS-V-003.md) | c | Cụm “chuyển nguyên” gợi đáp án; cần xác nhận đối chiếu hai giai đoạn và hai miền thực sự thiết yếu. |
| [LS-V-005](samples/LS-V-005.md) | đáp án A | Hai vế đáp án ghép gần sát câu hỏi trong stem; có thể giải bằng ghép ngữ nghĩa thay vì phân tích giá trị hai loại bằng chứng. |
| [LS-V-006](samples/LS-V-006.md) | a | Ý a nêu sẵn phần lớn kết luận; reviewer cần xác nhận phải nối khác biệt bố trí lực lượng hai hiệp định. |
| [LS-V-008](samples/LS-V-008.md) | c | Ý c tự nêu gần đủ chuỗi nhân quả; phần cuối có thể loại bằng hiểu phạm vi, cần kiểm tích hợp lịch sử ở phần đầu. |

Do đó không xem nhãn VD hoặc chất lượng nhiễu là đã được giáo viên xác nhận hay phản hồi chuyên môn đã đóng.

Hai kết quả `source-critical-two` đánh giá hai nhận định nguồn VD là phán đoán lịch sử đang làm việc; chúng không xác thực khóa đáp án chính thức. Dữ kiện/tiêu đề cột OCR của bảng thuế có dấu hiệu đảo; nhận định Potsdam cần kiến thức lịch sử ngoài trích đoạn.

## Phạm vi ba ô còn mở

Ba ô T06/P1/VD, T08/P1/VD và T16/P1/VD đều chỉ có căn cứ `proposed`, không có địa chỉ nguồn trong corpus hiện hành. Toàn bộ **62/62 ô có căn cứ observed** đã có mẫu khớp mức; trong 5 ô chỉ đề xuất, 2 đã có mẫu và 3 còn mở. Giữ đủ 67 ô trong báo cáo để không che phần đề xuất chưa làm được. Chưa có căn cứ bắt buộc mỗi chủ đề phải có VD MCQ; cần duyệt mục tiêu ma trận trước khi dùng ba ô này làm quota. Hai lượt sửa ba mẫu vẫn có đường tắt TH; dừng lặp cùng cách thiết kế, giữ draft/phiếu giải lại để tái thiết kế sau.
