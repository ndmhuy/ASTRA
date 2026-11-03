# Hồ sơ ra đề đầy đủ — tiêu chí nghiệm thu

Cập nhật theo yêu cầu chủ sở hữu ngày 03/11/2026. `NOTE.md` trước đây chỉ là bản tóm tắt trích xuất, không phải toàn bộ hồ sơ ra đề. Trạng thái kỹ thuật của rows/aggregate không được gọi là hồ sơ đã hoàn tất hay sẵn sàng plug in.

## Khung trình bày được chọn

Chủ sở hữu đồng ý tiếp tục dùng cấu trúc hồ sơ Sinh làm khung trình bày chung ngày 03/11/2026: tổng quan → cách ra đề theo chủ đề → ma trận → audit prototype → mức nhận thức → câu mẫu và tự giải → giới hạn/truy nguyên. Mỗi môn lấy kiểu câu, câu chùm, thứ tự và nhánh lựa chọn từ bằng chứng và registry của môn đó.

## Phạm vi và tình trạng thực tế

| Thành phần | Đã có | Còn phải hoàn tất |
|---|---|---|
| Nguồn thật và truy nguyên | Manifest, hash, địa chỉ phần/câu/ý, lớp bằng chứng, khóa và giới hạn nguồn | Các môn còn chạy; giữ nguyên các chỗ thiếu, không suy diễn |
| Mẫu cách hỏi | Rows và aggregate cho Toán, Sinh, Sử | Gộp nhãn về chủ đề canonical; trình bày đủ từng chủ đề, không chỉ vài ví dụ toàn môn |
| Nội dung thường gặp | Đếm số đề theo chủ đề/phần/lớp, chính thức và tỉnh riêng | Tần suất họ/chương và các dạng sau khi ánh xạ; không biến nhiều mã hay nhiều ý thành nhiều đề |
| Phân hóa | Nhãn thấp/vừa/cao và chuỗi suy luận do Sol nhận định | Tách khỏi mức nhận thức; ghi riêng các hàng không đủ bằng chứng |
| Phân bố theo ma trận | Snapshot slot NB/TH/VD của ma trận hiện tại | Gắn mức theo định nghĩa canonical cho từng hàng thật; bảng chủ đề × phần × lớp × mức, đối chiếu default, nói rõ đơn vị câu/ý và trường hợp tự chọn |
| Audit ma trận | Mã thực hiện và snapshot đã có; bắt đầu chạy cho ba môn đủ nguồn | Bảng mặc định so với đề thật; thiếu/thừa theo bằng chứng; đề xuất từng phần, các quyết định của chủ app, không sửa product |
| Audit prototype | Đã đo cơ học độ dài phương án và nối bản sao | Tự giải mù, nhiễu từng phương án, đúng/sai, mức thật so với nhãn, nhớ máy móc, phủ chủ đề, độ khó, câu chùm/thứ tự, xếp thứ tự lỗi và tối đa ba việc sửa/môn |
| Câu mẫu mới | Chưa có bộ câu mẫu theo chủ đề | Viết mới bằng Sol; đáp án, lời giải, từng nhiễu/lỗi, mức dự kiến, tự giải độc lập; không đưa vào thống kê đề thật |
| Tích hợp | Đã đọc seam context có sẵn trong bản product được đóng băng | Gói dữ liệu có version/hash, projection theo vai trò và đề/phần; kiểm prompt thực tế; thí nghiệm pipeline bằng Luna |

## Nội dung bắt buộc cho MỖI chủ đề

1. Tên chủ đề canonical, các bài con và lớp; kiến thức/phương pháp tiên quyết, phần nào có thể tích hợp với chủ đề khác.
2. Nội dung xuất hiện: số đề phân biệt và mẫu số, số câu/ý, vị trí phần, biến thể, chia chính thức/tỉnh. Điều không thấy chỉ được gọi là chưa thấy trong mẫu.
3. Các dạng câu: kiểu câu, dữ kiện/biểu diễn cho sẵn, đầu ra cần tìm, chuỗi quyết định và suy luận, cách biến đổi dữ kiện mà vẫn giữ dạng, điều kiện áp dụng và trường hợp biên.
4. Mức nhận thức NB/TH/VD theo thang product được đóng băng; tách nhãn phân hóa thấp/vừa/cao. Đối chiếu ma trận theo từng phần và đúng đơn vị slot; không quy đổi một-một hai thang. Có loại chưa đủ bằng chứng.
5. Cách nâng yêu cầu: thay đổi quyết định, mô hình hóa, kết nối, phản ví dụ hoặc kiểm điều kiện; không nâng mức chỉ bằng số lớn, văn dài hay thêm phép tính lặp.
6. Nhiễu/ý sai: lỗi cụ thể đứng sau từng lựa chọn, vì sao hợp lý, trường hợp chỉ là diễn đạt lộ/phi lý, giới hạn xác nhận khóa; không tuyên bố lỗi phổ biến trên học sinh khi chưa có dữ liệu bài làm.
7. Cách dùng ngày tháng, tên gọi, công thức và định nghĩa: hỏi nhớ trực tiếp, cho làm gợi ý, dùng trong suy luận; giữ tần suất quan sát riêng từng nguồn.
8. Câu chùm/tư liệu: chung trong một câu, chung nhiều câu hay xuyên phần; phụ thuộc giữa câu; thứ tự cố định/hoán vị/vị trí tự do; nhánh tự chọn. Quan sát lặp không tự thành ràng buộc universal.
9. Câu mẫu MỚI cho những dạng và mức có căn cứ; nếu chưa có mẫu ở một dạng/mức phải hiện rõ khoảng thiếu. Mỗi mẫu có đề đầy đủ, đáp án, lời giải, giải thích từng nhiễu/ý sai, lý do gán mức và lượt tự giải độc lập. Mẫu gắn nhãn app tạo/chờ giáo viên, không phải trích đề thật hay bằng chứng tần suất.
10. Kết quả audit ma trận và prototype liên quan trực tiếp đến chủ đề: thiếu/thừa, mức bị gán sai, chất lượng nhiễu, độ đúng, lỗi layout/câu chùm, khuyến nghị có bằng chứng.
11. Độ tin cậy, nguồn/refs, mẫu số, model, revision, chỗ chưa chắc, câu cần giáo viên. Hướng dẫn nào là quan sát, đề xuất hay ràng buộc từ registry phải tách rõ.

## Nguyên tắc bộ hồ sơ

- Hồ sơ mô tả cách ra câu; registry và yêu cầu của từng đề quyết định shape, thời lượng, điểm và thứ tự được phép. Không tự phát sinh bảng số cố định theo môn ngoài registry.
- Ma trận mặc định là đối tượng audit, không là bằng chứng tần suất. Toán do chủ app đặt tay, quyền quyết định thay đổi thuộc chủ app.
- Không sao chép câu, số liệu hay tình huống riêng của đề thật vào báo cáo/câu mẫu. Truy nguyên bằng địa chỉ/hashes; mẫu mới lưu tách và không đọc vào registry bằng chứng.
- Nghiên cứu, gộp chủ đề, audit và sinh câu mẫu dùng Sol. OCR thuần dùng Luna. Thí nghiệm dùng prompt pipeline thật cho Planner/Composer dùng Luna. Không API key trả phí.
- Không sửa product trong lane corpus; chỉ báo cáo và đề xuất. Kiểm file đạt không thay chứng minh đầu ra/prompt thực tế, độc lập tự giải hoặc rà của giáo viên.

## Tệp người đọc

- `NOTE.md`: tóm tắt và trạng thái đầy đủ/thiếu.
- `TOPICS.md` / `topics.json`: hồ sơ theo chủ đề, định danh canonical khi ánh xạ xong.
- `LEVELS.md` / `levels.json`: mức nhận thức theo ma trận, tách khỏi phân hóa.
- `SAMPLES.md` / `samples/`: câu mẫu mới và receipt tự giải.
- `audit/matrices/<subject>.md`: audit và đề xuất ma trận.
- `audit/prototypes/<subject>.md`: audit prototype; `audit/prototypes/SUMMARY.md` xếp thứ tự cần sửa.
- `rows.json`, `distributions.json`, `paper-structures.json`, `verification.json`: dữ liệu và kiểm định nền.

Một môn chỉ được gọi là hồ sơ ra đề hoàn chỉnh khi các mục bắt buộc đã có bằng chứng đầu ra hoặc khoảng thiếu được chủ sở hữu chấp nhận rõ. `Đang làm` và `chưa đủ bằng chứng` không được trình bày như đã làm.
