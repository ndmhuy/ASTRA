# CRITERIA — quy tắc ra đề/đánh giá nội bộ

## Điều kiện nội dung
1. Dùng cấu trúc 18 MCQ/4 TF×4 ý/6 trả lời ngắn theo 8 đề, nhưng không áp cứng vị trí chùm câu; câu dùng chung ngữ liệu phải giữ cả đoạn và tất cả thành viên.
2. Xác nhận công thức, trạng thái phản ứng, giới hạn chất, đơn vị, độ chính xác làm tròn, giả thiết điện cực, nhiệt độ/áp suất; ngữ liệu tự biên soạn ghi rõ.
3. MCQ phải có đúng **một** phương án đúng trong bốn phương án, mỗi nhiễu tương ứng một suy nghĩ sai có thể giải thích. Không suy đoán tần suất lỗi học sinh.
4. TF có chính xác bốn ý và giải riêng từng ý, phân mức theo ý, câu lấy max; phần P2 có thể dùng bảng/hình nhưng phải lưu asset thật và đường dẫn hợp lệ.
5. Trả lời ngắn nêu đáp án số/định dạng, các phương pháp giải tương đương, rubric quá trình; không khóa kết quả sai quy tắc làm tròn.
6. NB/TH/VD được thẩm định theo thao tác nhận thức tối thiểu, không theo số phép tính; phân hóa thực nghiệm chưa đo được.
7. Mọi hình cần thiết phải tồn tại dưới dạng PNG/SVG/PDF render thực được kiểm, nếu chưa đủ hình thì ghi **thiếu bằng chứng**, giữ nội dung và nêu phần chưa thể xác định; không đánh đồng với sai. Đề hoàn toàn đủ dữ kiện bằng văn bản/bảng thì không cần hình giả.
8. Kiểm không sao chép đề thật: không chỉ đổi số/tên cùng một tình huống đặc thù; so sánh nguồn, rà độc lập và ghi biên nhận của agent; không dùng teacher-approved khi chưa có.

## Rubric mẫu và nghiệm thu
- **P1:** 0,25 điểm cho chọn đúng; trong bản mẫu phải chứng minh vì sao đúng, vì sao ba nhiễu sai và có biến thể dễ/khó.
- **P2:** tối đa 1,00 điểm/câu trong ma trận đề xuất; 4 ý độc lập có giải và level. Quy tắc điểm lẻ theo số ý đúng phải do giáo viên/cơ chế chấm xác nhận, không ép 0,25/ý khi chưa có quy định.
- **P3:** tối đa 0,25 điểm/câu trong đề thật đề xuất, nhưng rubric huấn luyện trong file sample dùng **thang quy trình 1,00** để chấm các bước; khi quy đổi sang bài thi nhân với 0,25. Chấp nhận hệ phương trình, bảo toàn nguyên tố hoặc phương pháp thay thế nếu tương đương.
- Một mẫu được đánh `pass_same_model` chỉ sau lượt giải lại công thức và kiểm duy nhất khóa; chưa tương đương teacher-approved. Tất cả mẫu còn bất đồng hoặc thiếu hình giữ hold; không tính đạt.
- Ô COVERAGE là `pass` chỉ khi tồn tại sample pass; mỗi ô observed unknown chưa có mức nên để missing, không tự nâng hạng.

## Cờ cần người duyệt
- Gán mức nhận thức cho 320 địa chỉ sau đọc lại trường hợp cần thiết từ OCR/nguyên bản, ưu tiên các cờ partial.
- Chốt quy tắc điểm P2 và cách mã hóa trả lời ngắn trong runtime, kiểm hình render với pipeline triển khai.
- Duyệt 116 câu mẫu, kiểm không sao chép, độ khó/độ phân hóa khi có học sinh và sửa mức nếu cần.

Mẫu tiêu chí cách làm: [REFERENCES/CRITERIA.md](evidence/REFERENCE-CRITERIA.md) chỉ làm chỉ dẫn, không dùng nội dung Toán/Sinh làm bằng chứng Hóa.

## Bổ sung theo phản hồi giáo viên về prototype (04/11/2026)

9. **Câu chùm – nhất quán dữ kiện:** so lượng chất, giới hạn thuốc thử, khoảng thời gian và điều kiện của **từng ý với ngữ liệu chung**. Nếu chuyển sang trường hợp giả định khác, phải viết rõ “Trong một thí nghiệm khác…” và bổ sung điều kiện thuốc thử dư khi cần. Khớp đáp án nhưng giả thiết mâu thuẫn với ngữ liệu vẫn là **hold nội dung**.
10. **Hình công thức phân tử/cấu tạo:** không chỉ kiểm file có thật hoặc render được; kiểm **hóa học/khả năng đọc**. Riêng Haworth phải thể hiện đúng vòng và hướng các nhóm thế, nhất quán với anomer/dạng cấu hình nếu nêu; kiểm cấu hình và khả năng đọc trên bản render, ghi rõ bằng chứng của lượt rà. Hình nhìn được nhưng không thể xác minh độ chính xác vẫn **hold hình**.
11. **Đáp án nguyên và diễn đạt số:** số đếm đồng phân, số hiện tượng/số chất là số nguyên; không yêu cầu “làm tròn” vô nghĩa. Các kết quả đo hoặc tính gần đúng mới cần đơn vị và quy tắc làm tròn hợp lý.
12. **QA trang PDF:** giữ câu hỏi + bốn phương án cùng trang, không tách ngữ liệu chung khỏi câu phụ thuộc; kiểm khoảng trắng trang cuối sau khi render. Kiểm cú pháp TeX hoặc link asset tồn tại **không thay** kiểm bố cục PDF thực.
13. **Nghiệm thu toàn đề theo mục đích:** thêm lượt review độ phủ, câu hỏi lặp cùng thao tác kiến thức, sự phân bố NB/TH/VD **thực chất** và độ khó; không tự suy tính phân hóa từ số bước tính. Cần có ngữ cảnh sử dụng: đề ôn tập cơ bản có thể được chấp nhận sau sửa, còn đề luyện thi phân hóa cần thiết kế theo ma trận đích và tự giải/kiểm độc lập riêng; không suy mức nhận thức từ số phép tính.

**Hai cấp gate độc lập:** (a) `answer_math_key_check` = giải/khóa khớp, (b) `editorial_release_check` = dữ kiện, hình, dàn trang, độ phủ toàn đề và mục đích sử dụng. Không cho phát hành prototype nếu (b) còn `hold` dù (a) đạt 40/40. Phản hồi được ghi tại [TEACHER-FEEDBACK.md](TEACHER-FEEDBACK.md); không phải chứng nhận các mẫu mới.
