# Danh pháp dùng chung cho hồ sơ và câu mẫu

Tạm dừng hoàn thiện thêm các môn theo yêu cầu chủ app; bước hiện tại chỉ rà và chuẩn hóa danh pháp. Bảng chính là [replacements.json](replacements.json), hàm dùng chung là [replace_terms](../tools/terminology.py). Luna quét lại phần hồ sơ đã xuất; gợi ý của model phải qua rà trước khi thành quy tắc.

**Quy tắc đã chốt: nitrogen và gene; mọi tên nguyên tố và tên hóa chất trong ngữ cảnh khoa học dùng danh pháp chuẩn tiếng Anh.** Không quay lại nitơ/gen hoặc tên phiên âm cũ. Bảng replace bao phủ các alias thường gặp, không phải từ điển vô hạn; tên mới hoặc đa nghĩa phải đọc ngữ cảnh trước khi bổ sung.

Các tên khoa học tiếng Anh đã xác lập: nucleotide, gene, allele, DNA, RNA, amino acid, nucleic acid, enzyme, protein… Đây là quy ước biên tập theo yêu cầu chủ app, không phải tuyên bố đã đối chiếu mọi phiên bản sách hoặc văn bản Bộ GDĐT.

- Thay cụm dài trước; ranh giới từ đầy đủ, xử lý Unicode, giữ kiểu viết acronym. Không thay `gen1` hay một phần từ.
- Giữ nguyên khái niệm dạy học tiếng Việt còn đúng như nhiễm sắc thể, quang hợp, lục lạp, đạo hàm, nguyên hàm, vectơ. “Dùng danh pháp tiếng Anh” không đồng nghĩa dịch cả đề.
- Không biến “oxi hóa” thành “oxygen hóa”. Tên chất, quá trình oxidation và oxygenation của máu là những khái niệm khác nhau; trường hợp chưa rõ phải xem ngữ cảnh.
- Toán: tên bất đẳng thức, định lý và phiên âm tên riêng cần đọc công thức. Không đổi mọi “Cauchy” thành cùng một bất đẳng thức.
- Tên loài: danh pháp Latin, chữ hoa/thường, in nghiêng và đồng danh phân loại cần đối chiếu nguồn. Không đổi nhãn gene/locus hoặc ký hiệu allele thành tên loài.
- Hóa: ưu tiên tên nguyên tố/chất theo IUPAC, nhưng không tự đổi mọi tên thông dụng thành tên hệ thống hay thay tên làm sai chất/đồng phân/trạng thái. Cần rà riêng tiếng Anh, thứ tự tên, hóa trị và công thức.
- Vật lí: SI, tên người, ký hiệu đại lượng/đơn vị và cách viết tiền tố; không dịch hoặc đổi chữ hoa/thường của ký hiệu bằng replace văn xuôi.
- Địa lí/Công nghệ/Tin học: rà tên chất, khoáng vật, vật liệu, thuật ngữ sinh học khi có; tên địa danh, chuẩn giao thức và mã định danh có quy tắc riêng. Các môn chưa có hồ sơ nội dung chỉ nhận ghi chú cho lần soạn tiếp theo.

Bản đọc Markdown áp dụng replace. Các tệp gốc làm bằng chứng, khóa, nhãn và biên nhận model giữ nguyên. JSON chuẩn hóa nằm ở `profiles/<môn>/terminology/`: có hash nguồn gốc, hash quy tắc và nhãn `terminology_view`. Giá trị khóa, ID/ref và mã chủ đề vẫn giữ để truy nguyên; nhãn hiển thị là trường riêng. Không dùng một view đã đổi danh pháp như biên nhận tự giải mới.

Nguồn đối chiếu tên tiếng Anh: [NHGRI nucleotide](https://www.genome.gov/genetics-glossary/Nucleotide), [NHGRI allele](https://www.genome.gov/genetics-glossary/Allele), [NHGRI protein](https://www.genome.gov/genetics-glossary/Protein), [NIGMS glossary](https://www.nigms.nih.gov/education/glossary), [IUPAC periodic table](https://iupac.org/what-we-do/periodic-table-of-elements/). Các nguồn này xác nhận tên/khái niệm tiếng Anh; không tự chứng minh quy định biên tập của kỳ thi Việt Nam.

Đã bổ sung nitrate/nitrite/ammonium và các nguyên tố, ion, acid thường gặp. Bảo vệ riêng Oxy/Oxyz/Ox/Oz và các từ đa nghĩa đồng/vàng/bạc/chì; chỉ thay khi đúng cụm chỉ chất/nguyên tố.
