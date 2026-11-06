# Hóa học — bản duyệt để sử dụng, 06/11/2026

**Có thể lấy 116 câu mẫu hiện hành và prototype revised để dùng làm tư liệu soạn đề hoặc ôn tập theo các giả thiết đã ghi. Không có gate chờ giáo viên.** Đã sửa 4 mẫu còn vướng nội dung và giải độc lập đủ 40 câu/ý prototype; tất cả 40 khớp khóa. Đây là quyết định của agent, không gọi thành teacher-approved.

[116 mẫu theo chủ đề](SAMPLES.md) · [25 hướng dẫn](TOPICS.md) · [PDF prototype](prototype-revised/prototype.pdf) · [40 lời giải kiểm prototype](prototype-revised/content-review-20261106.json) · [Biên nhận và hash](USABILITY-REVIEW.json).

## Phân loại theo hai trục

| Nội dung | Tính đúng và cách sử dụng | Bằng chứng còn thiếu |
|---|---|---|
| 116 mẫu synthetic hiện hành | Giữ 116, bỏ 0; dùng theo điều kiện từng câu. Đã có lượt giải không kèm khóa cho đủ 116; lượt này sửa và giải lại 4 mẫu. | Chưa có dữ liệu học sinh; không khẳng định độ khó thực nghiệm hay tần suất nhiễu. |
| Prototype revised, 40 câu/ý | Đã giải đủ 40 và so khóa; dùng ôn tập hỗn hợp hoặc lấy từng câu làm mẫu. Haworth đã kiểm mã cấu hình và ảnh trang 1 thật. | Không tuyên bố đạt mọi ma trận mặc định hoặc phân hóa thực nghiệm. |
| 3 địa chỉ nguồn ảnh chưa đủ | Giữ lại với `validity = undetermined`, không gọi sai hoặc loại khỏi hồ sơ. | Thiếu hình đủ rõ để chốt phổ MS, carbanion hoặc đoạn polyisoprene. Xem lý do từng ref trong JSON. |
| Các note nhiễu yếu | Vẫn dùng được; không biến note biên tập thành lỗi hóa học hoặc đáp án sai. | Chưa có tỉ lệ học sinh chọn từng nhiễu. |
| Khóa của 320 nguồn | Không mặc nhiên chứng nhận toàn bộ khóa từ việc tool xanh. | Lượt này không tự giải lại 320 nguồn; giữ ranh giới với ngân hàng 116 mẫu đã có kiểm riêng. |

## Bốn mẫu đã sửa và giải lại

- **HH-S08:** mẫu nước ban đầu đủ lớn; lấy hai phần riêng, mỗi phần 20 mL. Bỏ mâu thuẫn mẫu 20 mL lại lấy 40 mL. Kết quả vẫn 0,015 mol/L.
- **HH-T02.d:** tách thành thí nghiệm khác; 80% đơn vị ban đầu chuyển thành glucose tự do và được thu hồi hoàn toàn. Không đánh đồng 80% liên kết bị thủy phân với 80% glucose thu được. Kết quả 14,4 g; khóa D.
- **HH-M08:** thay hai nhiễu glycine bằng cation và anion có cấu tạo đúng, tương ứng môi trường acid và base. B vẫn là dạng ion lưỡng cực gần điểm đẳng điện.
- **HH-M30:** hỏi tiểu phân, cho bộ lựa chọn amide, ammonium, ammonia và hydroxylamine; chỉ `NH₃ + H⁺ → NH₄⁺` đúng. B/NB giữ nguyên.

Đã đồng bộ các sửa này ở bank canonical, bank hiện hành, wrapper tool và trang Markdown. Bản review trước sửa được giữ làm lịch sử, có phân xử hiện hành đi kèm.

## Prototype và ma trận

40 đơn vị sau rà yêu cầu tối thiểu: **13 NB / 23 TH / 4 VD**. Không nâng nhãn để khớp số mong muốn. Bốn câu VD trả lời ngắn đòi hỏi lập ràng buộc và kiểm tính khả thi: tối ưu hỗn hợp muối, phân bổ thuốc thử theo phần nguyên, suy cấu tạo amine và bảo toàn đầu mạch polyamide. Các câu tính thế pin, khối lượng điện phân, chuẩn độ hoặc đếm ester quen thuộc vẫn ở TH.

Một đề đúng vẫn có thể không phù hợp một ma trận luyện thi cụ thể. Khi dùng làm đề đích, lấy ma trận của lần ra đề đó, chọn mẫu theo mức đã duyệt và tạo, kiểm bổ sung ô cần thiết. Không loại các mẫu đúng vì cả prototype chưa cân theo một mục tiêu khác.

## Đã kiểm

- Đủ 116 review không kèm khóa có lời giải; tất cả báo unique-answer, key-agreement và level-agreement. Đây không phải một lượt giải mù mới cho cả 116.
- 124/124 ô có sample ID; wrapper và bank trùng stem, options, statements cho đủ 116 mẫu.
- Giải độc lập 40 đơn vị prototype, so đúng địa chỉ `(part, idx, sub)`; 40/40 khớp JSON key. Không đổi TEX, PDF hoặc key; giữ biên nhận bố cục 7 trang cũ theo hash.
- Liệt kê toàn miền nguyên của bài phân bổ 10 phần và thuốc thử: 7R + 3H tối ưu, thu 21,9456 g Ag, đủ 116 tấm. Kiểm lại cận liên tục bài hỗn hợp muối và nghiệm đạt cận.

Chưa chạy pipeline sinh đề hoặc đo thực nghiệm học sinh. Những giới hạn đó được ghi đúng phạm vi, không dùng làm lý do phủ định nội dung đã kiểm bằng hóa học và lời giải.

## Kiểm bằng CLI thật

[Biên nhận CLI](USABILITY-CLI-20261106.json): 8 đề, `failed: []`; pack có 320 items, 63 patterns, 116 mẫu, `problems: 0`, `gaps: 0`. Đã đọc pack xác nhận đủ 4 bản sửa và 116 trạng thái hiện hành được xuất. Tool chưa xuất metadata usability tùy ý; các điều kiện quan trọng nằm trong stem/statements và ghi chú trong variation guidance. Không khẳng định runtime tự lọc theo biên nhận này.
