# Tiêu chí dùng hồ sơ Sinh để ra đề

[Quay về hồ sơ](PROFILE.md). Hồ sơ là bản nghiên cứu, chưa là chứng nhận giáo viên hoặc bằng chứng tích hợp runtime.

## Độ phủ và cách lấy mẫu

25 họ chủ đề được truy nguyên về 1 đề chính thức và 5 đề tỉnh. Mỗi ô trong sample-plan.json là một tổ hợp chủ đề/phần/mức có nhãn mức đủ tin cậy trên quan sát khái quát. Tổng 54 ô là kế hoạch minh họa đã đóng băng; không phải toàn bộ dạng Sinh học có thể ra. Không suy tỷ trọng từ số mẫu. Không dùng đề hoặc câu AI sinh để tính tần suất nguồn thật.

Mỗi lần ra đề: chọn phạm vi kiến thức và ma trận của chính đề đó; đối chiếu họ chủ đề, dạng và mức; lấy ví dụ phù hợp làm chuẩn yêu cầu; sáng tác tình huống mới; giải và kiểm trước khi dùng. Có nguồn ở một ô không buộc mọi đề phải chứa ô đó. Phần chưa có nhãn rõ không được tự loại khỏi phạm vi chương trình.

## Câu trắc nghiệm và đúng/sai

- Dữ kiện và giả thiết phải đủ: loài/mô hình, trạng thái tế bào, quan hệ trội–lặn, liên kết/phân li độc lập hoặc điều kiện thí nghiệm chỉ nêu khi cần. Không cho đáp án chỉ đúng dưới giả thiết ngầm.
- Khóa phải khớp lời giải. MCQ có một đáp án đúng theo yêu cầu; các nhiễu biểu đạt cùng loại đại lượng hoặc cùng lớp kết luận, dựa trên lỗi cụ thể và không tự lộ qua độ dài/ngữ pháp.
- TF phải đưa trọn ngữ liệu và đủ ý; mỗi ý được giải thích. Ý sai cần cơ chế nhầm hợp lý, tránh đảo lời giả thiết vừa nêu để tạo câu sai hiển nhiên. Tách level từng ý khỏi level cao nhất toàn câu.
- Thực nghiệm/đồ thị/phả hệ có đủ nhãn, trục/đơn vị/chú giải/đối chứng; các câu dùng cùng dữ kiện phải giữ liên kết. Mô tả hình bằng lời không thay cho hình nếu việc đọc hình chính là thao tác cần đo.

## Trả lời ngắn

Đáp án lưu là một giá trị số, không kèm phần trăm/đơn vị hoặc chuỗi thứ tự có dấu nối. Đơn vị, cách mã hóa và quy tắc làm tròn được đặt trong đề. Một yêu cầu sắp xếp thao tác phải đổi cách hỏi sang một đại lượng hoặc mã số có quy tắc rõ; không nhét chuỗi văn bản vào ô số. Kết quả tính theo phân số chính xác trước khi làm tròn; khác dấu phẩy/dấu chấm thập phân không tự thành sai kiến thức.

## Mức nhận thức và mức phân hóa

- NB: nhận ra/nhớ một khái niệm, chức năng, thuộc tính hoặc đơn vị kiến thức đã học. Ngữ cảnh trang trí không đổi mức.
- TH: giải thích, phân biệt, diễn giải hình/bảng quen thuộc hoặc thực hiện một quy trình chuẩn; nhiều bước tính thường quy vẫn có thể là TH.
- VD: xây dựng mô hình hoặc kết nối các đơn vị kiến thức và chuỗi suy luận phụ thuộc để giải nhiệm vụ. Không gán VD chỉ vì nhiều con số hoặc tình huống dài.
- Mức phân hóa thấp/vừa/cao là trục riêng. Chưa có dữ liệu học sinh thì không báo độ khó hoặc khả năng phân biệt thực nghiệm.
- 21/240 hàng nguồn còn unknown được giữ nguyên, không ép nhãn để đủ một tỉ lệ; xem LEVELS.md.

## Sinh học và danh pháp

Trong nội dung mới dùng gene, allele, nucleotide, DNA/RNA, nitrogen và tên tiếng Anh chuẩn của nguyên tố/chất; giữ nhiễm sắc thể, quang hợp và ngữ pháp tiếng Việt. Phân biệt mô hình giả định dùng để tính với quy luật đúng cho mọi loài; không lấy suy luận của mô hình đơn giản làm khẳng định sinh học phổ quát. Bản chép đề gốc giữ nguyên, thuật ngữ chuẩn hóa nằm ở bản đọc dẫn xuất và mẫu.

## Nghiệm thu một mẫu

1. Đủ dữ kiện và các điều kiện quyết định kết quả.
2. Đúng kiến thức, phép tính, khóa và lời giải.
3. Đúng hình thức phần, số ý/đáp án và dạng trả lời.
4. Mức mục tiêu khớp thao tác tối thiểu; ghi nhận bất đồng khi giải lại.
5. Nhiễu có cơ chế, không lộ khóa hoặc tự mâu thuẫn trực tiếp với giả thiết.
6. Không thiếu hình/bảng và không đứt nhóm dữ kiện dùng chung.
7. Không sao chép câu/số liệu/tình huống riêng từ corpus; kiểm chuỗi chỉ là hỗ trợ, không chứng minh không trùng ý.
8. Có receipt sinh, lượt giải lại không được đưa khóa/mức mục tiêu, và đối chiếu code. Hai lượt cùng Sol không đồng nghĩa giáo viên hoặc model khác đã thẩm định.

Mẫu đạt các mục trên vẫn chờ giáo viên; mẫu có cờ giữ hold. Tích hợp còn phải kiểm mapping đề/matrix, câu chùm và đầu ra của pipeline thực tế.

## Giới hạn nguồn cần giữ

Đề Cà Mau phần III câu 5 dẫn bảng không có trong vùng nguồn được cung cấp. Hàng đó đã ghi uncertainty và không dùng làm chứng cứ cho mức/phân hóa hoặc khóa suy ra từ bảng; việc nhìn thấy tên chủ đề không xác nhận đọc được toàn bộ nhiệm vụ. OCR mới không bổ sung bảng này. Chỉ một đề chính thức nên hiện diện trong đề đó không chứng minh tần suất ổn định.
