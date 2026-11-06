# Bổ sung — phản hồi giáo viên về prototype Hóa học

**Nguồn:** lời nhận xét của giáo viên do người dùng cung cấp ngày **04/11/2026**. Phạm vi là **prototype** một nội dung `28eb748d17fc`, không phải corpus đề thật, các mẫu synthetic hoặc biên bản duyệt độc lập toàn bộ đề. Tình trạng: **đã ghi nhận để điều chỉnh tiêu chí và audit; chưa sửa file LaTeX gốc, chưa render bản sửa**.

## Đánh giá và quy tắc diễn giải

- **Bố cục/độ đọc:** ba phần rõ, chữ và sơ đồ đọc được. Có thể dùng ôn tập cơ bản **sau khi** chỉnh các lỗi ghi dưới đây.
- **Độ khó:** giáo viên nhận xét đề nhẹ và có phần lặp nội dung; **chưa** đủ cơ sở sử dụng như đề luyện thi yêu cầu phân hóa. Nhận xét này không phải phép đo phân hóa thực nghiệm và không tự định nghĩa mức NB/TH/VD cho từng câu.
- **Phép tính và chất lượng câu hỏi là hai trục độc lập:** ý II.2d cho kết quả 1,08 gam Ag khi giả định glucose phản ứng hoàn toàn và lượng thuốc thử dư, nhưng dữ kiện không tương thích nếu hiểu là nối tiếp thí nghiệm đã cho. Khớp khóa không đồng nghĩa câu đã đạt nghiệm thu.

## Các yêu cầu cần làm trước khi phát hành prototype

| ID | Địa chỉ / phạm vi | Nhận xét và biện pháp sửa | Trạng thái |
|---|---|---|---|
| TF-HH-01 | `P2.2.d` | Tách rõ phản ứng tráng bạc thành thí nghiệm khác, thuốc thử dư. Đề xuất nguyên văn: **“Trong một thí nghiệm khác, cho 0,9 gam glucose phản ứng hoàn toàn với dung dịch AgNO₃/NH₃ dư thì thu được 1,08 gam Ag.”** Sau sửa kiểm lại toàn bộ câu chùm. | `needs_revision` |
| TF-HH-02 | `P1.3` | Thay hình vòng fructose bằng **công thức Haworth** thể hiện rõ hướng các nhóm OH/CH₂OH theo dạng được chọn; rà cấu hình hoá học, đáp án và render mới. Hình hiện có không phải “ảnh thiếu”: vấn đề là **độ chính xác biểu diễn**. | `needs_figure_and_visual_verification` |
| TF-HH-03 | `P3.2` | Bỏ yêu cầu “Làm tròn đến chữ số hàng đơn vị” khỏi câu đếm đồng phân; đáp án số đếm nguyên. | `needs_revision` |
| TF-HH-04 | Toàn tài liệu | Kiểm ngắt trang; không tách câu hỏi và toàn bộ phương án. Đối với chùm/TF, không tách ngữ liệu khỏi các ý phụ thuộc. | `needs_pdf_review` |
| TF-HH-05 | Trang cuối | Giảm khoảng trắng thừa sau khi cân trang; không phá bố cục để ép trang. | `needs_pdf_review` |
| TF-HH-06 | Toàn đề | Rà nội dung lặp và cân mức; nếu dùng luyện thi phân hóa, viết lại/thêm nhiệm vụ **VD thực chất**, phải lập liên hệ nhiều dữ kiện hoặc cân nhắc giới hạn, không chỉ dài/nhiều bước tính thường quy. | `pending_design_and_teacher_review` |

## Kiểm tra lại sau khi sửa

1. Giữ nguồn LaTeX và khóa nguyên trạng trong `evidence/`; tạo **bản dẫn xuất sửa riêng** rồi kiểm bản render PDF thật. Chưa có bản dẫn xuất đó ở đợt bổ sung này.
2. Tự giải lại **từng câu/ý bị sửa**, đối chiếu khóa; kiểm tính đủ dữ kiện, ngữ cảnh thí nghiệm và hóa học hình Haworth.
3. Rà toàn đề theo hai trục độc lập: **tính đúng câu/đáp án** và **độ phủ, trùng lặp, phân hóa cho mục đích sử dụng**; kiểm trang PDF.
4. Sau đó gửi giáo viên xem lại. Nhận xét lần này **không** đồng nghĩa `teacher-approved`.

Dữ liệu có ID và trạng thái: [data/teacher-feedback.json](data/teacher-feedback.json). Liên kết sang [PROTOTYPE-AUDIT.md](PROTOTYPE-AUDIT.md), [CRITERIA.md](CRITERIA.md), [QA.md](QA.md).
