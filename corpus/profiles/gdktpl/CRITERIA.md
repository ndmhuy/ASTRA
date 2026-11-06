# CRITERIA — quy tắc nghiên cứu và nghiệm thu GDKTPL

## Nguồn và quyết định

- Phân loại nguồn theo `PACKAGE.json`, không dùng tên thư mục `originals/official` để nâng đề tỉnh thành đề Bộ. Một mã đề trong gói là một đơn vị độc lập, không nâng bản sao/giải bài thành đề mới. Ngữ liệu chung gắn `stimulus_id` bất biến.
- Có khóa theo bảng nguồn chưa phải chứng minh đáp án đúng. Ghi `unknown` cho mức nhận thức chưa xem thủ công; dữ liệu học sinh và phân tích độ phân hóa chưa có.
- Baseline chỉ được kiểm ở revision `de8c614...`; đề xuất lưu riêng và không ghi đè snapshot.

## Dữ kiện và tính duy nhất

- Mỗi mẫu có stem tự đứng được hoặc dẫn toàn bộ ngữ liệu kèm câu chùm; tất cả điều kiện giả định phải hiện diện. Nếu dùng văn bản pháp luật cụ thể, cần kiểm hiệu lực, đối tượng và ngoại lệ; ưu tiên nêu rõ quy tắc giả định trong đề khi khảo sát cách suy luận.
- MCQ có đúng 4 phương án A–D và đúng một phương án hợp lí theo dữ kiện. Phương án nhiễu phải sai bằng **cơ chế cụ thể**: nhầm khái niệm, đọc thiếu điều kiện, đảo logic, bỏ một nghĩa vụ; không tạo lựa chọn sai vì phi lí/lố bịch.
- TF bốn ý có phán định và lời giải riêng; không suy mức tất cả ý từ nhãn mức câu. Chùm câu được đánh giá toàn nhóm, không chia rời đoạn dẫn. Không tạo hình bằng lời mà báo đã có hình; chỉ mẫu hình thực được kiểm mới pass.

## NB / TH / VD và phân hóa

- NB nhận dạng một quy tắc/chỉ báo, TH giải thích và áp dụng quen thuộc, VD phối hợp điều kiện và lập kế hoạch có chuỗi phụ thuộc; dài/một vài phép tính không tự thành VD.
- Độ khó/phân hóa thực nghiệm cần dữ liệu học sinh, không có trong đầu vào. Một số nhãn VD prototype cần rà: P1–19, 20, 22.

## Rubric/đáp án

- Biểu điểm trong matrix proposal là một giả định lịch sử, không phải mặc định khi dùng. MCQ và TF chấm đúng quy tắc của đề đích; không biến lời giải theo từng ý thành quy tắc cộng 0,25 điểm/ý.
- TF xét từng ý theo điều kiện của ngữ liệu, không dùng quy tắc “một ý sai thì cả câu sai”. Đối với câu chùm, rubric của các câu phụ thuộc phải đọc cùng ngữ liệu.
- Nếu xây mẫu tự luận ở bước sau, cho điểm theo thao tác: nhận diện vấn đề, nêu căn cứ, đối chiếu sự kiện, kết luận; chấp nhận các giải thích và lập luận tương đương đúng bản chất. Chưa đề xuất tự luận trong cơ cấu hai phần của corpus.

## Nghiệm thu mẫu — điều kiện pass nghiên cứu

1. Nguồn mới hoàn toàn, không trá hình sao chép đề tỉnh; không bịa nguồn tác giả.
2. Đủ dữ kiện/đơn vị, duy nhất khóa, kiểm tổng số câu/ý/điểm, không mất nhóm ngữ liệu.
3. Có lời giải chi tiết, từng nhiễu có lí do, từng ý TF có khóa và mức; biến thể dễ/khó có ranh giới cụ thể.
4. Tự giải lại lượt riêng, lưu khác biệt, **cùng model không gọi độc lập/blind**.
5. Phân loại tính đúng và sức mạnh bằng chứng riêng. Khóa không khớp phải tự giải và chỉ rõ sai ở khóa hay ở câu; hình thiếu hoặc luật chưa đủ nguồn được ghi “chưa xác định”, không coi là sai. Nếu dùng được theo một điều kiện, ghi rõ điều kiện và giữ phần đúng. Chỉ loại phát biểu/câu đã chứng minh sai như đang viết; lưu nguyên nguồn để truy lại. Runtime là hạng mục tích hợp riêng.

**Không tuyên bố:** teacher-approved, đã cắm vào generator, đã chạy test runtime, phân hóa thực nghiệm đã đo hoặc mô hình dự báo tần suất chính thức.

Trạng thái sử dụng hiện hành 06/11/2026: xem [USABILITY-REVIEW](USABILITY-REVIEW.md). Nội dung thiếu bằng chứng không bị coi là sai; nhãn teacher_approved=false mô tả provenance, không tạo yêu cầu chờ giáo viên.
