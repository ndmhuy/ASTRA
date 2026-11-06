# Rà danh pháp Toán, Sinh và ghi chú các môn khác

Đã tạm dừng hoàn thiện thêm hồ sơ/đề. Lượt này thêm lớp biên tập danh pháp, áp dụng cho bản đọc Toán/Sinh và dùng Luna quét các hồ sơ đã xuất. Không chạy lại OCR, không sinh thêm đề và không đổi bộ bằng chứng hoặc biên nhận tự giải.

Luna hoàn thành 62/62 phần quét. Đoạn trùng được gom theo hash. Đây là quét thuật ngữ, không phải duyệt tính đúng của toàn đề. Một phần quét có thể chỉ là NOTE thiếu dữ liệu; xem phạm vi từng môn.

## Kết quả chính

- Toán: 22 phần quét, không có phát hiện danh pháp từ Luna; bản đọc không cần thay từ theo bảng hiện tại. Giữ thuật ngữ toán tiếng Việt và đọc công thức trước khi đổi tên bất đẳng thức.
- Sinh: chuẩn hóa bản đọc và JSON dẫn xuất: ADN/DNA, ARN/RNA, alen/allele; nitơ/nitrogen, nitrat/nitrate, nitrit/nitrite, amoni/ammonium và các tên chất/đại phân tử thường gặp. Quy tắc chủ app chốt: mọi tên nguyên tố và hóa chất dùng danh pháp chuẩn tiếng Anh. Ví dụ nuclêôtit → nucleotide đã có trong hàm dù không còn trong bản Markdown đã rà. Một cụm sẵn có về oxygen trong máu đã được diễn đạt rõ hơn bằng quy tắc có ngữ cảnh.
- Luna nêu 31 gợi ý: 28 gợi ý không đủ cơ sở để sửa hoặc trái quy ước đã chọn; 1 chú giải song ngữ tùy chọn ở Hóa; 2 báo cáo cùng vấn đề nuclôn/nucleon ở Vật lí đã xác minh. Không áp dụng gợi ý của model tự động.
- Vật lí: đã thêm alias nuclôn → nucleon cùng các tên hạt thông dụng vào bảng để dùng khi tiếp tục môn này. Các môn khác hiện chỉ nhận ghi chú, không được đánh dấu đã hoàn thiện hồ sơ.

## Phạm vi từng môn

| Môn | Phạm vi đã có để quét | Phần Luna | Phát hiện thô |
|---|---|---:|---:|
| Toán | Hồ sơ nội dung đã xuất | 22 | 0 |
| Vật lí | Hồ sơ nội dung đã xuất | 6 | 4 |
| Hoá học | Hồ sơ nội dung đã xuất | 6 | 7 |
| Sinh học | Hồ sơ nội dung đã xuất | 8 | 20 |
| Lịch sử | Hồ sơ nội dung đã xuất | 6 | 0 |
| Địa lí | Hồ sơ nội dung đã xuất | 5 | 0 |
| Giáo dục kinh tế và pháp luật | Chưa có bản nội dung để quét | 0 | 0 |
| Tin học | Chỉ NOTE; chưa có hồ sơ nội dung đủ để rà | 1 | 0 |
| Ngữ văn | Chưa có bản nội dung để quét | 0 | 0 |
| Tiếng Anh | Chưa có bản nội dung để quét | 0 | 0 |
| Tiếng Nga | Chỉ NOTE; chưa có hồ sơ nội dung đủ để rà | 1 | 0 |
| Tiếng Nhật | Chỉ NOTE; chưa có hồ sơ nội dung đủ để rà | 1 | 0 |
| Tiếng Hàn | Chỉ NOTE; chưa có hồ sơ nội dung đủ để rà | 1 | 0 |
| Tiếng Pháp | Chỉ NOTE; chưa có hồ sơ nội dung đủ để rà | 1 | 0 |
| Tiếng Đức | Chỉ NOTE; chưa có hồ sơ nội dung đủ để rà | 1 | 0 |
| Tiếng Trung | Chỉ NOTE; chưa có hồ sơ nội dung đủ để rà | 1 | 0 |
| Công nghệ Công nghiệp | Chỉ NOTE; chưa có hồ sơ nội dung đủ để rà | 1 | 0 |
| Công nghệ Nông nghiệp | Chỉ NOTE; chưa có hồ sơ nội dung đủ để rà | 1 | 0 |

## Kiểm lại sau xác nhận của chủ app

Sau khi chốt mọi tên nguyên tố/hóa chất dùng tiếng Anh, đã bổ sung nitrate/nitrite/ammonium và bảng nguyên tố/chất thường gặp. Luna kiểm lại 2 phần gồm các đoạn vừa đổi và ca ký hiệu Oxy/từ đa nghĩa: không phát hiện thêm. Đây là phần bổ sung cho 62 phần quét đầu, không thay biên nhận cũ.

[Nguyên nhân có request/output để đối chiếu](/Users/huynguyen/Lecturing_Lab/wt-corpus-merged/audit/terminology/CAUSES.md).

## Kiểm chứng và giới hạn

Hàm replace có ranh giới từ, cụm dài trước, Unicode và bảo vệ công thức/đường dẫn/ID/khóa. Riêng oxi hóa và oxygenation phải giữ khác nhau; không sửa tên loài hoặc tên bất đẳng thức bằng thay chuỗi đơn giản. Bản JSON chuẩn hóa là view dẫn xuất, không phải một lượt tự giải lại.

Bằng chứng model, prompt, địa chỉ đoạn và disposition được lưu đầy đủ. Luna có báo động giả; agent chính đã rà các gợi ý, không coi lượt quét này là chứng nhận chuyên môn hoặc xác nhận mọi thuật ngữ đúng theo mọi sách.

Nguồn tên tiếng Anh: [NHGRI nucleotide](https://www.genome.gov/genetics-glossary/Nucleotide), [NHGRI allele](https://www.genome.gov/genetics-glossary/Allele), [NIGMS glossary](https://www.nigms.nih.gov/education/glossary), [IUPAC nucleon](https://goldbook.iupac.org/terms/view/N04247), [IUPAC periodic table](https://iupac.org/what-we-do/periodic-table-of-elements/), [BIPM SI Brochure](https://www.bipm.org/en/publications/si-brochure/). Đây là nguồn tên/khái niệm, không phải xác nhận quy định Bộ GDĐT Việt Nam.

## Tệp để kiểm lại

- [Bảng thay thế](/Users/huynguyen/Lecturing_Lab/wt-corpus-merged/audit/terminology/replacements.json).
- [Hàm replace](/Users/huynguyen/Lecturing_Lab/wt-corpus-merged/audit/tools/terminology.py).
- [Prompt Luna](/Users/huynguyen/Lecturing_Lab/wt-corpus-merged/audit/prompts/TERMINOLOGY_SCAN.txt).
- [Toàn bộ kết quả Luna](/Users/huynguyen/Lecturing_Lab/wt-corpus-merged/audit/outputs/terminology/luna-scan.json).
- [Disposition từng phát hiện](/Users/huynguyen/Lecturing_Lab/wt-corpus-merged/audit/outputs/terminology/parent-dispositions.json).
