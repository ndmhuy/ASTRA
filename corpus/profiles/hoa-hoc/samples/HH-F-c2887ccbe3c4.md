# HH-F-c2887ccbe3c4 — T05

Phần P3; dạng short_answer. Mẫu synthetic, không thuộc corpus nguồn. Trạng thái: agent_reviewed_usable_with_stated_assumptions; chưa giáo viên duyệt.

## Đề bài

Có 6 pin loại U và 4 pin loại V, chưa sử dụng. Mỗi U duy trì 1,50 V, có 0,0300 mol chất oxi hóa nhận 2 electron mỗi phân tử; mỗi V duy trì 1,00 V, có 0,100 mol chất oxi hóa nhận 1 electron mỗi phân tử. Chất khử mỗi pin dư. Chỉ được ghép một chuỗi nối tiếp cố định, không mắc song song, không thay pin giữa chừng. Thiết bị cần hiệu điện thế ít nhất 5,00 V và lấy dòng không đổi 0,965 A. Mọi pin trong chuỗi có cùng dòng; pin cạn đầu tiên làm cả chuỗi dừng. Bỏ qua điện trở, điện áp không đổi đến khi cạn; F=96500 C/mol. Chọn số pin từng loại để thời gian hoạt động dài nhất. Thời gian dài nhất bằng bao nhiêu giây? Ghi số nguyên.

## Khóa, lời giải và mức nhận thức

- Đáp án: **6000**; mức **VD**. Mỗi U cho 0,0600 mol electron, mỗi V cho 0,100 mol. Nếu không dùng U, bốn V chỉ có 4,00 V nên không đủ. Do đó mọi chuỗi hợp lệ phải có U và dung lượng chuỗi không vượt 0,0600F C. Có thể ghép 2U+2V đạt 5,00 V, dung lượng 0,0600F. Thời gian tối đa là 0,0600×96500/0,965=6000 s.

Mỗi U cho 0,0600 mol electron, mỗi V cho 0,100 mol. Nếu không dùng U, bốn V chỉ có 4,00 V nên không đủ. Do đó mọi chuỗi hợp lệ phải có U và dung lượng chuỗi không vượt 0,0600F C. Có thể ghép 2U+2V đạt 5,00 V, dung lượng 0,0600F. Thời gian tối đa là 0,0600×96500/0,965=6000 s.

**Căn cứ nhận thức:** VD: phải mô hình hóa chuỗi nối tiếp bằng pin yếu nhất thay vì cộng dung lượng, dùng điều kiện điện áp chứng minh cần U và chỉ ra cấu hình đạt cận.

## Nhiễu và cách làm tương đương


Chấp nhận lập luận hóa học tương đương, bảo toàn và đổi đơn vị nhất quán; kết quả phải thỏa toàn bộ điều kiện đề.

## Tiêu chí chấm và biến thể

- 1 điểm minh họa: Mỗi U cho 0,0600 mol electron, mỗi V cho 0,100 mol. Nếu không dùng U, bốn V chỉ có 4,00 V nên không đủ. Do đó mọi chuỗi hợp lệ phải có U và dung lượng chuỗi không vượt 0,0600F C. Có thể ghép 2U+2V đạt 5,00 V, dung lượng 0,0600F. Thời gian tối đa là 0,0600×96500/0,965=6000 s.

Tiêu chí là minh họa nghiên cứu, không thay biểu điểm của đề đích. Với TF, không mặc định chia đều điểm từng ý. Xem [CRITERIA](../CRITERIA.md).

- Dễ hơn: Cho sẵn chuỗi 2U+2V, nêu quy tắc pin yếu nhất và hỏi thời gian.
- Khó hơn: Cho phép hai chuỗi song song có điện áp bằng nhau và tối ưu số pin sử dụng.

## Giải lại và trạng thái

**agent_reviewed_usable_with_stated_assumptions**. Hồ sơ không gọi lượt kiểm tra là teacher-approved.

Phải chọn cấu hình rồi xét pin giới hạn: tối đa bốn V chỉ có 4 V, nên mọi chuỗi đủ 5 V phải chứa U. U chỉ có 0,0600F điện lượng, t=0,0600F/0,965=6000 s; ví dụ 2U+2V đạt 5 V.

Chi tiết: [ngân hàng hiện hành](../data/samples-current.json).
