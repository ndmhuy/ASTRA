# SOURCE-CORRECTIONS — không sửa raw OCR

**Số chỉnh sửa văn bản OCR thực hiện trong lượt xây hồ sơ này: 0.** Tất cả `evidence/OCR/` được copy byte-for-byte, không normalize thuật ngữ hoặc áp dụng thay thế mù. Các `structure.json`, `key.json`, `CHANGES.md` trong nguồn phản ánh lần xử lí OCR trước; không được tự nhận là sửa hôm nay.

## Các vấn đề OCR/nguồn được kế thừa và cần theo dõi

| Đề | Mức | Phần | Chỉ số | Cờ từ nguồn |
| --- | --- | --- | --- | --- |
| P02 | warning | P2 | 4 | Bản DOCX khi render có 5 trang phần đề, khác thông báo 4 trang in trong đầu đề; đây có thể là thay đổi dàn trang, không kết luận thiếu trang. |
| P05 | info | P1 | 10 | Phần dẫn chung in số câu cách bất thường "10,  1 1"; giữ nguyên trong de.md, ánh xạ có ghi chú theo ngữ cảnh câu 10–11. |

Đặc biệt giữ trường `printed_number` riêng, không tự sửa cách in bất thường về câu 10/11 ở Tuyên Quang. Phú Thọ cần đối chiếu khác biệt giữa số trang in công bố và bản DOCX render. Ảnh trang gốc DOCX chưa được xem lại toàn bộ bằng mắt trong lần này; không giả định không có sai sót khác.

**Nếu sửa sau này:** ghi `(paper,part,index,sub)`, chuỗi OCR gốc, chuỗi sửa, chứng cứ là trang/hàng/vị trí trong original, người kiểm và ngày, rồi mới tạo `derived/` (không thay `evidence/OCR/`).
