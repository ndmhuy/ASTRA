# Mẫu và tiêu chí nghiệm thu hồ sơ ra đề

Mức tham chiếu: hồ sơ Toán là bản nghiên cứu hoàn chỉnh, chưa giáo viên duyệt/chưa thử runtime. Hồ sơ Sinh là ví dụ cấu trúc và nội dung, vẫn còn mẫu chưa đạt. Không dùng trạng thái mẫu để chứng minh chất lượng cho môn khác. Các hồ sơ này là mẫu cách làm; không phải nguồn nội dung hoặc tần suất cho môn khác.

## Thành phần bắt buộc
1. Kiểm kê nguồn và giới hạn: đề độc lập, official/provincial/format_only, mã đề, trang, khóa và vấn đề OCR. Chỉ tần suất trong tập đọc được; không gộp lớp nguồn.
2. Cấu trúc: phần theo đúng thứ tự, số câu in/số phải làm, các nhánh tự chọn, nhóm ngữ liệu, câu chùm, quy tắc đánh số. Luật cố định và quan sát riêng phải phân biệt.
3. Audit ma trận: từng dòng mặc định, bằng chứng ủng hộ/phản bác, quyết định giữ/sửa/chưa rõ; đề xuất riêng có tổng câu/ý/điểm khớp. Ma trận trong gói là baseline nghiên cứu ở SHA được ghi trong PACKAGE.json, không khẳng định là bản product mới nhất.
4. Audit prototype: đúng phiên bản, tự giải rồi đối chiếu khóa, nội dung/dạng/mức/phân hóa/nhiễu/dữ kiện/hình/danh pháp; dẫn câu cụ thể. Không tính prototype vào thống kê corpus thật.
5. Mỗi chủ đề: phạm vi/tiên quyết; kiến thức thường gặp; các dạng cho→hỏi→suy luận→đáp án; biến thể; tích hợp; lỗi và nhiễu; phân bố mức theo phần/ô ma trận; ví dụ; tránh lỗi; nguồn.
6. Tiêu chí mức: dùng level-scheme.json làm baseline, diễn giải theo môn. NB/TH/VD là thao tác nhận thức tối thiểu, không phải số phép tính; mức phân hóa là trục khác. Chưa có dữ liệu học sinh thì không gọi là độ khó thực nghiệm.
7. Mẫu: lập COVERAGE trước. Mỗi ô chủ đề × dạng/phần × mức có bằng chứng hoặc được đề xuất trong ma trận cần ít nhất một mẫu hoàn chỉnh. Tách ô đã quan sát và ô đề xuất. Một mẫu không chứng minh phủ mọi biến thể.
8. Mỗi mẫu: ID; ô mục tiêu; đề đủ dữ kiện; hình/bảng; khóa; lời giải; lý do xếp mức; nhiễu theo lỗi; biến thể dễ/khó. Tự luận có rubric điểm và đáp án/phương pháp tương đương; đúng/sai giải thích từng ý; câu chùm gồm cả ngữ liệu và tất cả câu liên quan.
9. Kiểm mẫu: giải lại trước khi đối chiếu khóa; đúng kiến thức/phép tính; đủ điều kiện; không đa nghĩa/đa khóa ngoài dự kiến; đúng dạng và mức; nhiễu hợp lý không lộ; hình/bảng khớp; danh pháp; không sao chép tình huống riêng từ đề thật.
10. Ngữ liệu tự biên soạn phải ghi rõ. Không bịa tác giả/citation. Nếu hình cần thiết mà chưa có ảnh/SVG thực thì giữ mẫu hold, không coi mô tả bằng lời là hình đã làm.
11. Phân biệt: nghiên cứu hoàn chỉnh, chờ giáo viên, chưa kiểm thử tích hợp. Không tuyên bố plug in hoặc kiểm định độc lập từ một lượt chat cùng model.

## Bảng phủ bắt buộc
| ID ô | Chủ đề | Dạng/phần | Mức | Đã quan sát/đề xuất | Nguồn hỗ trợ | ID mẫu | Kết quả giải lại | Cờ | Trạng thái |
|---|---|---|---|---|---|---|---|---|---|

## Khung một chủ đề (phải điền nội dung thực)
- Phạm vi và tiên quyết; nội dung thường gặp và mẫu số theo lớp nguồn.
- Dạng 1..n: dữ kiện, nhiệm vụ, chuỗi suy luận tối thiểu, kiến thức tích hợp, điểm quyết định.
- Bảng dạng × phần × mức × số câu/ý và số đề; unknown giữ riêng.
- Cách biến đổi; lỗi/nhiễu có cơ chế, không tự gọi là lỗi phổ biến.
- Liên hệ dòng ma trận và câu prototype.
- Các mẫu đủ đề/khóa/lời giải/rubric, tình trạng và ID trong COVERAGE.
- Dẫn địa chỉ nguồn và các giới hạn còn lại.

## Quy tắc diễn giải
- Đơn vị: (part,index_within_part,sub); printed_number riêng; không gộp các ý TF thành nhiều đề.
- Thống kê câu tích hợp/chủ đề không tự cộng thành 100%. Nhánh Tin học không cộng thành bài một học sinh phải làm.
- Prototype/khóa cùng chat có thể đã được model nhìn thấy: yêu cầu lượt tự giải tách là kiểm tra có cấu trúc, không chứng minh blind độc lập.
- Giữ raw OCR. Chuẩn hóa thuật ngữ chỉ trong nội dung nghiên cứu mới và mẫu: gene/allele/nucleotide/DNA/RNA/nitrogen, tên nguyên tố/chất bằng tiếng Anh chuẩn; vectơ và các thuật ngữ tiếng Việt đúng giữ nguyên; bảo vệ Oxy/Oxyz/biến/ký hiệu. Không replace từ đa nghĩa mù.
- Thống kê đọc được không phải kết luận về toàn bộ chương trình. Dưới năm đề độc lập đủ nội dung: chỉ mô tả/kiểm dạng, không phát biểu quy luật tần suất hoặc đề xuất thay mặc định dựa vào tần suất.
- Bài mẫu và lời giải mới không được nhập lại corpus bằng chứng đề thật.
