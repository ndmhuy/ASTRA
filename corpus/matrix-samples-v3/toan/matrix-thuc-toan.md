# Toán 12 — ma trận thật (bản mẫu, đã sửa theo 5 câu trả lời ngày 29/10)

Mỗi câu hoặc mỗi ý có một khối riêng, viết đầy đủ bằng chữ. Không dùng mã viết tắt như C3, 1C, NL.1. Quy tắc viết rút ra từ bản này nằm ở `docs/release/next/matrix-writing-rules.md`.

**Trạng thái:** bản mẫu chờ duyệt cuối. Chưa nạp vào code, chưa chạy check.py, chưa thử sinh đề từ bản này.

## 1. Khung đề (lấy từ khung đã đăng ký trong code)

- Thời gian: 90 phút. Tổng điểm: 10.
- Phần I: 12 câu nhiều lựa chọn, 0,25 điểm mỗi câu, tổng 3,0 điểm.
- Phần II: 4 câu đúng/sai, mỗi câu 4 ý a, b, c, d. Chấm theo bậc thang: đúng 1 ý được 0,1; đúng 2 ý được 0,25; đúng 3 ý được 0,5; đúng cả 4 ý được 1,0. Ma trận này tính trung bình 0,25 điểm mỗi ý, tổng 4,0 điểm.
- Phần III: 6 câu trả lời ngắn, 0,5 điểm mỗi câu, tổng 3,0 điểm. Đáp số là một số, dấu phẩy thập phân.

## 2. Ba mức độ nghĩa là gì

- **Biết:** nhận ra, nêu hoặc đọc thông tin có sẵn; áp dụng một công thức hoặc một quy tắc trong một bước.
- **Hiểu:** thực hiện một quy trình đã học trong hai đến ba bước, giải thích hoặc so sánh kết quả, đọc ý nghĩa của số liệu.
- **Vận dụng:** lập mô hình hoặc hàm số từ một tình huống mới, kết hợp nhiều kiến thức, nhiều bước tính, rồi kết luận và nêu lí do.

Cách chia: cân bằng hơn số liệu đã gắn nhãn của đề chính thức 2025 mã 0101 (Biết 4, Hiểu 17, Vận dụng 13). Bản này lấy Biết 10, Hiểu 14, Vận dụng 10, vì các đề sở cho thấy Phần I có nhiều câu nhận biết hơn mức 4 câu. Đây là lựa chọn thiết kế, chưa phải số liệu đo.

## 3. Tổng hợp bằng số

| Phần | Số câu | Số ý chấm | Biết | Hiểu | Vận dụng | Điểm |
|---|---|---|---|---|---|---|
| Phần I (nhiều lựa chọn) | 12 | 12 | 6 | 5 | 1 | 3,0 |
| Phần II (đúng/sai) | 4 | 16 | 4 | 7 | 5 | 4,0 |
| Phần III (trả lời ngắn) | 6 | 6 | 0 | 2 | 4 | 3,0 |
| **Tổng** | 22 | 34 | 10 | 14 | 10 | 10,0 |

Theo điểm: Biết 2,5 điểm (25%), Hiểu 4 điểm (40%), Vận dụng 3,5 điểm (35%).

Kiến thức lớp 10 và 11 chiếm 8 trên 22 câu (36,36%): 5 câu ở Phần I, 3 câu ở Phần III. Trong 7 đề đã xem, tỉ lệ này khoảng 38% ở Phần I.

## 4. Số câu theo chủ đề và bài

| Chủ đề | Bài hoặc nội dung | Lớp | Số câu hoặc số ý theo dạng, mức độ | Điểm |
|---|---|---|---|---|
| Vectơ và hệ trục tọa độ trong không gian | Bài 6. Vectơ trong không gian | lớp 12 | 1 câu nhiều lựa chọn mức Biết | 0,25 |
| Quan hệ song song và vuông góc trong không gian | Quan hệ song song trong không gian (kiến thức nền) | lớp 11 | 1 câu nhiều lựa chọn mức Biết | 0,25 |
| Phương pháp tọa độ trong không gian | Bài 15. Phương trình đường thẳng trong không gian | lớp 12 | 1 câu nhiều lựa chọn mức Biết | 0,25 |
| Nguyên hàm và tích phân | Bài 11. Nguyên hàm | lớp 12 | 1 câu nhiều lựa chọn mức Biết | 0,25 |
| Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm | Bài 9. Khoảng biến thiên và khoảng tứ phân vị | lớp 12 | 1 câu nhiều lựa chọn mức Hiểu | 0,25 |
| Dãy số, cấp số cộng và cấp số nhân | Cấp số cộng và cấp số nhân (kiến thức nền) | lớp 11 | 1 câu nhiều lựa chọn mức Hiểu | 0,25 |
| Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số | Bài 3. Đường tiệm cận của đồ thị hàm số | lớp 12 | 1 câu nhiều lựa chọn mức Biết | 0,25 |
| Nguyên hàm và tích phân | Bài 13. Ứng dụng hình học của tích phân | lớp 12 | 1 câu nhiều lựa chọn mức Hiểu; 1 câu trả lời ngắn mức Vận dụng | 0,75 |
| Phương pháp tọa độ trong không gian | Bài 14. Phương trình mặt phẳng | lớp 12 | 1 câu nhiều lựa chọn mức Hiểu | 0,25 |
| Hàm số mũ và hàm số lôgarit | Phương trình, bất phương trình mũ và lôgarit (kiến thức nền) | lớp 11 | 1 câu nhiều lựa chọn mức Hiểu | 0,25 |
| Hàm số lượng giác và phương trình lượng giác | Phương trình lượng giác cơ bản (kiến thức nền) | lớp 11 | 1 câu nhiều lựa chọn mức Biết | 0,25 |
| Hình học không gian | Khối chóp và khối lăng trụ (kiến thức nền) | lớp 11 | 1 câu nhiều lựa chọn mức Vận dụng | 0,25 |
| Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số | Phần II không gắn bài, chỉ gắn từng ý | lớp 12 | 1 ý đúng/sai mức Biết; 2 ý đúng/sai mức Hiểu; 1 ý đúng/sai mức Vận dụng | 1 |
| Nguyên hàm và tích phân | Phần II không gắn bài, chỉ gắn từng ý | lớp 12 | 1 ý đúng/sai mức Biết; 2 ý đúng/sai mức Hiểu; 1 ý đúng/sai mức Vận dụng | 1 |
| Phương pháp tọa độ trong không gian | Phần II không gắn bài, chỉ gắn từng ý | lớp 12 | 1 ý đúng/sai mức Biết; 1 ý đúng/sai mức Hiểu; 2 ý đúng/sai mức Vận dụng | 1 |
| Xác suất có điều kiện | Phần II không gắn bài, chỉ gắn từng ý | lớp 12 | 1 ý đúng/sai mức Biết; 2 ý đúng/sai mức Hiểu; 1 ý đúng/sai mức Vận dụng | 1 |
| Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số | Bài 2 và Bài 5. Giá trị lớn nhất, nhỏ nhất và ứng dụng thực tiễn | lớp 12 | 1 câu trả lời ngắn mức Vận dụng | 0,5 |
| Hình học không gian | Khoảng cách và góc trong không gian (kiến thức nền) | lớp 11 | 1 câu trả lời ngắn mức Vận dụng | 0,5 |
| Tổ hợp và xác suất cổ điển | Quy tắc đếm, hoán vị, chỉnh hợp, tổ hợp (kiến thức nền) | lớp 11 | 1 câu trả lời ngắn mức Hiểu | 0,5 |
| Hệ bất phương trình bậc nhất hai ẩn | Bất phương trình bậc nhất hai ẩn và quy hoạch tuyến tính (kiến thức nền) | lớp 10 | 1 câu trả lời ngắn mức Hiểu | 0,5 |
| Phương pháp tọa độ trong không gian | Bài 7, Bài 14 và Bài 17. Tọa độ, mặt phẳng và mặt cầu | lớp 12 | 1 câu trả lời ngắn mức Vận dụng | 0,5 |

Bài 8, Bài 10 và Bài 16 không có câu nào trong bản mẫu: đây là chủ ý, vì ở mỗi đề ban ra đề phải chọn trong số các nội dung hay gặp và các bài này ít xuất hiện trong 7 đề đã xem.

## 5. Chi tiết từng câu và từng ý


### Phần I — Nhiều lựa chọn

**Phần I, câu 1** · Nhiều lựa chọn · 0,25 điểm · mức **Biết**
- Chủ đề: Vectơ và hệ trục tọa độ trong không gian
- Bài: Bài 6. Vectơ trong không gian (lớp 12)
- Mục tiêu đánh giá: Áp dụng quy tắc ba điểm hoặc quy tắc hình bình hành để cộng, trừ hai vectơ trên một hình hộp hoặc hình lăng trụ cho sẵn, rồi chọn đẳng thức vectơ đúng.
- Dạng câu hỏi và dữ kiện: Một hình hộp hoặc hình lăng trụ có hình vẽ; bốn phương án là bốn đẳng thức vectơ. Không có số liệu.
- Năng lực: Tư duy và lập luận toán học
- Mức độ gặp trong các đề đã xem: 5/7 đề

**Phần I, câu 2** · Nhiều lựa chọn · 0,25 điểm · mức **Biết**
- Chủ đề: Quan hệ song song và vuông góc trong không gian
- Bài: Quan hệ song song trong không gian (kiến thức nền) (lớp 11)
- Mục tiêu đánh giá: Nhận biết một đường thẳng song song với mặt phẳng nào trong hình hộp hoặc tứ diện, hoặc hai mặt phẳng nào song song.
- Dạng câu hỏi và dữ kiện: Hình hộp hoặc tứ diện có hình vẽ, bốn phương án là bốn mặt phẳng hoặc bốn đường thẳng đặt tên bằng đỉnh. Không có số liệu.
- Năng lực: Tư duy và lập luận toán học
- Mức độ gặp trong các đề đã xem: 3/7 đề

**Phần I, câu 3** · Nhiều lựa chọn · 0,25 điểm · mức **Biết**
- Chủ đề: Phương pháp tọa độ trong không gian
- Bài: Bài 15. Phương trình đường thẳng trong không gian (lớp 12)
- Mục tiêu đánh giá: Đọc phương trình chính tắc hoặc tham số của một đường thẳng và chỉ ra một vectơ chỉ phương, hoặc một điểm thuộc đường thẳng.
- Dạng câu hỏi và dữ kiện: Phương trình đường thẳng cho sẵn bằng công thức; bốn phương án là bốn bộ ba số. Chỉ cần đọc hệ số, không tính toán.
- Năng lực: Tư duy và lập luận toán học
- Mức độ gặp trong các đề đã xem: 6/7 đề

**Phần I, câu 4** · Nhiều lựa chọn · 0,25 điểm · mức **Biết**
- Chủ đề: Nguyên hàm và tích phân
- Bài: Bài 11. Nguyên hàm (lớp 12)
- Mục tiêu đánh giá: Nêu họ nguyên hàm của một hàm cơ bản (lũy thừa của x hoặc hàm mũ a^x) bằng bảng nguyên hàm, một bước.
- Dạng câu hỏi và dữ kiện: Một hàm số cho bằng công thức; bốn phương án là bốn biểu thức có hằng số C, trong đó có các phương án sai quen thuộc (quên chia hệ số, sai số mũ).
- Năng lực: Tư duy và lập luận toán học
- Mức độ gặp trong các đề đã xem: 4/7 đề, 2 đề khác có câu liên quan

**Phần I, câu 5** · Nhiều lựa chọn · 0,25 điểm · mức **Hiểu**
- Chủ đề: Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm
- Bài: Bài 9. Khoảng biến thiên và khoảng tứ phân vị (lớp 12)
- Mục tiêu đánh giá: Tính tứ phân vị thứ nhất hoặc thứ ba, hoặc khoảng tứ phân vị, từ một bảng tần số ghép nhóm bằng công thức đã học.
- Dạng câu hỏi và dữ kiện: Bảng tần số ghép nhóm 5 đến 6 nhóm, số liệu một tình huống đời sống (thời lượng cuộc gọi, điểm số, cân nặng). Đáp số là một số, làm tròn nếu cần.
- Năng lực: Giải quyết vấn đề toán học
- Mức độ gặp trong các đề đã xem: 6/7 đề

**Phần I, câu 6** · Nhiều lựa chọn · 0,25 điểm · mức **Hiểu**
- Chủ đề: Dãy số, cấp số cộng và cấp số nhân
- Bài: Cấp số cộng và cấp số nhân (kiến thức nền) (lớp 11)
- Mục tiêu đánh giá: Tìm công sai, công bội hoặc một số hạng của cấp số cộng hoặc cấp số nhân từ hai dữ kiện cho trước.
- Dạng câu hỏi và dữ kiện: Cho hai số hạng hoặc số hạng đầu cùng công sai; hỏi một đại lượng còn lại. Tính trong hai đến ba bước.
- Năng lực: Giải quyết vấn đề toán học
- Mức độ gặp trong các đề đã xem: 6/7 đề

**Phần I, câu 7** · Nhiều lựa chọn · 0,25 điểm · mức **Biết**
- Chủ đề: Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số
- Bài: Bài 3. Đường tiệm cận của đồ thị hàm số (lớp 12)
- Mục tiêu đánh giá: Nhận ra tiệm cận đứng hoặc tiệm cận ngang của đồ thị hàm phân thức từ đồ thị cho sẵn hoặc từ công thức.
- Dạng câu hỏi và dữ kiện: Đồ thị hàm y = (ax+b)/(cx+d) có đường tiệm cận vẽ nét đứt, hoặc công thức hàm số; bốn phương án là bốn đường thẳng.
- Năng lực: Tư duy và lập luận toán học
- Mức độ gặp trong các đề đã xem: 3/7 đề

**Phần I, câu 8** · Nhiều lựa chọn · 0,25 điểm · mức **Hiểu**
- Chủ đề: Nguyên hàm và tích phân
- Bài: Bài 13. Ứng dụng hình học của tích phân (lớp 12)
- Mục tiêu đánh giá: Tính diện tích hình phẳng giới hạn bởi đồ thị một hàm số đơn giản, trục hoành và hai đường thẳng đứng, hoặc thể tích khối tròn xoay, bằng tích phân.
- Dạng câu hỏi và dữ kiện: Hàm số bậc nhất hoặc bậc hai cho bằng công thức, cận cho sẵn; đáp số là một số nguyên hoặc phân số.
- Năng lực: Giải quyết vấn đề toán học
- Mức độ gặp trong các đề đã xem: 4/7 đề

**Phần I, câu 9** · Nhiều lựa chọn · 0,25 điểm · mức **Hiểu**
- Chủ đề: Phương pháp tọa độ trong không gian
- Bài: Bài 14. Phương trình mặt phẳng (lớp 12)
- Mục tiêu đánh giá: Lập phương trình mặt phẳng đi qua một điểm và có vectơ pháp tuyến cho trước, hoặc chỉ ra vectơ pháp tuyến của mặt phẳng cho bằng phương trình.
- Dạng câu hỏi và dữ kiện: Điểm và vectơ cho bằng tọa độ; bốn phương án là bốn phương trình dạng ax+by+cz+d=0 có hệ số d khác nhau.
- Năng lực: Giải quyết vấn đề toán học
- Mức độ gặp trong các đề đã xem: 5/7 đề

**Phần I, câu 10** · Nhiều lựa chọn · 0,25 điểm · mức **Hiểu**
- Chủ đề: Hàm số mũ và hàm số lôgarit
- Bài: Phương trình, bất phương trình mũ và lôgarit (kiến thức nền) (lớp 11)
- Mục tiêu đánh giá: Giải phương trình hoặc bất phương trình mũ hoặc lôgarit cơ bản, kết luận nghiệm hoặc tập nghiệm.
- Dạng câu hỏi và dữ kiện: Phương trình dạng log_a(f(x)) = m hoặc a^x < b; bốn phương án là bốn nghiệm hoặc bốn tập nghiệm, có phương án quên điều kiện xác định.
- Năng lực: Giải quyết vấn đề toán học
- Mức độ gặp trong các đề đã xem: 7/7 đề

**Phần I, câu 11** · Nhiều lựa chọn · 0,25 điểm · mức **Biết**
- Chủ đề: Hàm số lượng giác và phương trình lượng giác
- Bài: Phương trình lượng giác cơ bản (kiến thức nền) (lớp 11)
- Mục tiêu đánh giá: Nhận ra tập nghiệm của phương trình sin x = m hoặc cos x = m với m là giá trị đặc biệt (0, 1, -1), viết theo k thuộc tập số nguyên.
- Dạng câu hỏi và dữ kiện: Một phương trình lượng giác cơ bản; bốn phương án là bốn tập nghiệm khác nhau ở phần cộng k2π hoặc kπ.
- Năng lực: Giải quyết vấn đề toán học
- Mức độ gặp trong các đề đã xem: 5/7 đề

**Phần I, câu 12** · Nhiều lựa chọn · 0,25 điểm · mức **Vận dụng**
- Chủ đề: Hình học không gian
- Bài: Khối chóp và khối lăng trụ (kiến thức nền) (lớp 11)
- Mục tiêu đánh giá: Tính thể tích khối chóp hoặc khối lăng trụ mà chiều cao hoặc diện tích đáy phải tự tìm từ góc hoặc quan hệ vuông góc cho trước, rồi tính tiếp.
- Dạng câu hỏi và dữ kiện: Hình chóp hoặc lăng trụ cho bằng lời, có một góc hoặc một quan hệ vuông góc; phải tự dựng hoặc tính chiều cao; đáp số là một số.
- Năng lực: Giải quyết vấn đề toán học
- Mức độ gặp trong các đề đã xem: 4/7 đề, 6/7 đề nếu tính cả khối đa diện nói chung


### Phần II — Đúng/sai

Mỗi câu của Phần II thuộc một chủ đề, tức một chương của phạm vi bài kiểm tra tổng thể. Phần II không gắn bài; chỉ gắn từng ý.

**Phần II, câu 1, ý a** · Đúng/sai · 0,25 điểm · mức **Biết**
- Chủ đề (một chương của phạm vi kiểm tra): Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số (lớp 12)
- Mục tiêu đánh giá: Tính đạo hàm của hàm số hoặc giá trị của hàm số tại một điểm cho trước, một bước.
- Dạng câu hỏi và dữ kiện: Phát biểu về giá trị cụ thể, đúng hoặc sai theo phép tính.  Tình huống chung của câu: một hàm số bậc ba hoặc hàm phân thức cho bằng công thức, có thể gắn với một đại lượng thực tế (lợi nhuận, chi phí) theo biến x.
- Năng lực: Giải quyết vấn đề toán học
- Mức độ gặp trong các đề đã xem: 6/7 đề

**Phần II, câu 1, ý b** · Đúng/sai · 0,25 điểm · mức **Hiểu**
- Chủ đề (một chương của phạm vi kiểm tra): Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số (lớp 12)
- Mục tiêu đánh giá: Xét dấu đạo hàm để kết luận khoảng đồng biến hoặc nghịch biến.
- Dạng câu hỏi và dữ kiện: Phát biểu về khoảng đơn điệu.  Tình huống chung của câu: một hàm số bậc ba hoặc hàm phân thức cho bằng công thức, có thể gắn với một đại lượng thực tế (lợi nhuận, chi phí) theo biến x.
- Năng lực: Tư duy và lập luận toán học
- Mức độ gặp trong các đề đã xem: 6/7 đề

**Phần II, câu 1, ý c** · Đúng/sai · 0,25 điểm · mức **Hiểu**
- Chủ đề (một chương của phạm vi kiểm tra): Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số (lớp 12)
- Mục tiêu đánh giá: Tìm giá trị lớn nhất hoặc nhỏ nhất của hàm số trên một đoạn cho trước.
- Dạng câu hỏi và dữ kiện: Phát biểu về giá trị lớn nhất hoặc nhỏ nhất.  Tình huống chung của câu: một hàm số bậc ba hoặc hàm phân thức cho bằng công thức, có thể gắn với một đại lượng thực tế (lợi nhuận, chi phí) theo biến x.
- Năng lực: Giải quyết vấn đề toán học
- Mức độ gặp trong các đề đã xem: 6/7 đề

**Phần II, câu 1, ý d** · Đúng/sai · 0,25 điểm · mức **Vận dụng**
- Chủ đề (một chương của phạm vi kiểm tra): Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số (lớp 12)
- Mục tiêu đánh giá: Dùng bảng biến thiên hoặc đồ thị để biện luận số nghiệm của f(x) = m, hoặc so sánh giá trị lớn nhất của tình huống với một ngưỡng rồi kết luận.
- Dạng câu hỏi và dữ kiện: Phát biểu kết luận có kèm lí do bằng số.  Tình huống chung của câu: một hàm số bậc ba hoặc hàm phân thức cho bằng công thức, có thể gắn với một đại lượng thực tế (lợi nhuận, chi phí) theo biến x.
- Năng lực: Mô hình hóa toán học
- Mức độ gặp trong các đề đã xem: 6/7 đề

**Phần II, câu 2, ý a** · Đúng/sai · 0,25 điểm · mức **Biết**
- Chủ đề (một chương của phạm vi kiểm tra): Nguyên hàm và tích phân (lớp 12)
- Mục tiêu đánh giá: Tính giá trị của hàm vận tốc hoặc hàm quãng đường tại một thời điểm cho trước, hoặc nhận ra nguyên hàm của một hàm đơn giản.
- Dạng câu hỏi và dữ kiện: Phát biểu về một giá trị cụ thể.  Tình huống chung của câu: một vật chuyển động với gia tốc hoặc vận tốc cho bằng công thức theo thời gian t, hoặc một miền phẳng bị chặn bởi hai đường cong cho bằng công thức.
- Năng lực: Giải quyết vấn đề toán học
- Mức độ gặp trong các đề đã xem: 5/7 đề

**Phần II, câu 2, ý b** · Đúng/sai · 0,25 điểm · mức **Hiểu**
- Chủ đề (một chương của phạm vi kiểm tra): Nguyên hàm và tích phân (lớp 12)
- Mục tiêu đánh giá: Thiết lập tích phân biểu diễn quãng đường hoặc diện tích (xác định đúng cận và hàm dưới dấu tích phân).
- Dạng câu hỏi và dữ kiện: Phát biểu về biểu thức tích phân.  Tình huống chung của câu: một vật chuyển động với gia tốc hoặc vận tốc cho bằng công thức theo thời gian t, hoặc một miền phẳng bị chặn bởi hai đường cong cho bằng công thức.
- Năng lực: Tư duy và lập luận toán học
- Mức độ gặp trong các đề đã xem: 5/7 đề

**Phần II, câu 2, ý c** · Đúng/sai · 0,25 điểm · mức **Hiểu**
- Chủ đề (một chương của phạm vi kiểm tra): Nguyên hàm và tích phân (lớp 12)
- Mục tiêu đánh giá: Tính quãng đường hoặc diện tích bằng tích phân.
- Dạng câu hỏi và dữ kiện: Phát biểu về một số cụ thể.  Tình huống chung của câu: một vật chuyển động với gia tốc hoặc vận tốc cho bằng công thức theo thời gian t, hoặc một miền phẳng bị chặn bởi hai đường cong cho bằng công thức.
- Năng lực: Giải quyết vấn đề toán học
- Mức độ gặp trong các đề đã xem: 5/7 đề

**Phần II, câu 2, ý d** · Đúng/sai · 0,25 điểm · mức **Vận dụng**
- Chủ đề (một chương của phạm vi kiểm tra): Nguyên hàm và tích phân (lớp 12)
- Mục tiêu đánh giá: Giải yêu cầu ngược hoặc so sánh: tìm thời điểm hoặc tham số để quãng đường hoặc diện tích đạt một giá trị cho trước, và kết luận.
- Dạng câu hỏi và dữ kiện: Phát biểu về thời điểm hoặc tham số, có lí do.  Tình huống chung của câu: một vật chuyển động với gia tốc hoặc vận tốc cho bằng công thức theo thời gian t, hoặc một miền phẳng bị chặn bởi hai đường cong cho bằng công thức.
- Năng lực: Mô hình hóa toán học
- Mức độ gặp trong các đề đã xem: 5/7 đề

**Phần II, câu 3, ý a** · Đúng/sai · 0,25 điểm · mức **Biết**
- Chủ đề (một chương của phạm vi kiểm tra): Phương pháp tọa độ trong không gian (lớp 12)
- Mục tiêu đánh giá: Đọc tọa độ điểm hoặc vectơ trực tiếp từ dữ kiện của tình huống.
- Dạng câu hỏi và dữ kiện: Phát biểu về tọa độ cụ thể.  Tình huống chung của câu: một vật chuyển động hoặc một công trình đặt trong hệ trục Oxyz (máy bay, đường đi, đài quan sát), đơn vị trên trục cho sẵn.
- Năng lực: Giải quyết vấn đề toán học
- Mức độ gặp trong các đề đã xem: 6/7 đề

**Phần II, câu 3, ý b** · Đúng/sai · 0,25 điểm · mức **Hiểu**
- Chủ đề (một chương của phạm vi kiểm tra): Phương pháp tọa độ trong không gian (lớp 12)
- Mục tiêu đánh giá: Viết hoặc nhận ra phương trình đường thẳng (đường đi) hoặc mặt phẳng từ dữ kiện.
- Dạng câu hỏi và dữ kiện: Phát biểu về phương trình.  Tình huống chung của câu: một vật chuyển động hoặc một công trình đặt trong hệ trục Oxyz (máy bay, đường đi, đài quan sát), đơn vị trên trục cho sẵn.
- Năng lực: Tư duy và lập luận toán học
- Mức độ gặp trong các đề đã xem: 6/7 đề

**Phần II, câu 3, ý c** · Đúng/sai · 0,25 điểm · mức **Vận dụng**
- Chủ đề (một chương của phạm vi kiểm tra): Phương pháp tọa độ trong không gian (lớp 12)
- Mục tiêu đánh giá: Tính khoảng cách hoặc độ dài đoạn thẳng trong tình huống rồi so sánh với giới hạn an toàn cho trước.
- Dạng câu hỏi và dữ kiện: Phát biểu kết luận có kèm số liệu.  Tình huống chung của câu: một vật chuyển động hoặc một công trình đặt trong hệ trục Oxyz (máy bay, đường đi, đài quan sát), đơn vị trên trục cho sẵn.
- Năng lực: Mô hình hóa toán học
- Mức độ gặp trong các đề đã xem: 6/7 đề

**Phần II, câu 3, ý d** · Đúng/sai · 0,25 điểm · mức **Vận dụng**
- Chủ đề (một chương của phạm vi kiểm tra): Phương pháp tọa độ trong không gian (lớp 12)
- Mục tiêu đánh giá: Xác định vị trí hai đối tượng (cắt nhau, chéo nhau, một điểm có nằm trong mặt cầu hay không) và nêu kết luận.
- Dạng câu hỏi và dữ kiện: Phát biểu về vị trí tương đối.  Tình huống chung của câu: một vật chuyển động hoặc một công trình đặt trong hệ trục Oxyz (máy bay, đường đi, đài quan sát), đơn vị trên trục cho sẵn.
- Năng lực: Tư duy và lập luận toán học
- Mức độ gặp trong các đề đã xem: 6/7 đề

**Phần II, câu 4, ý a** · Đúng/sai · 0,25 điểm · mức **Biết**
- Chủ đề (một chương của phạm vi kiểm tra): Xác suất có điều kiện (lớp 12)
- Mục tiêu đánh giá: Đọc từ đề bài một xác suất có điều kiện hoặc xác suất của một biến cố đơn.
- Dạng câu hỏi và dữ kiện: Phát biểu về giá trị xác suất cho sẵn.  Tình huống chung của câu: một xét nghiệm hoặc một dây chuyền sản xuất có hai bước, cho tỉ lệ phần trăm của từng bước (độ chính xác của xét nghiệm, tỉ lệ mắc bệnh trong cộng đồng).
- Năng lực: Giải quyết vấn đề toán học
- Mức độ gặp trong các đề đã xem: 7/7 đề

**Phần II, câu 4, ý b** · Đúng/sai · 0,25 điểm · mức **Hiểu**
- Chủ đề (một chương của phạm vi kiểm tra): Xác suất có điều kiện (lớp 12)
- Mục tiêu đánh giá: Tính xác suất của giao hai biến cố bằng công thức nhân.
- Dạng câu hỏi và dữ kiện: Phát biểu về một số thập phân.  Tình huống chung của câu: một xét nghiệm hoặc một dây chuyền sản xuất có hai bước, cho tỉ lệ phần trăm của từng bước (độ chính xác của xét nghiệm, tỉ lệ mắc bệnh trong cộng đồng).
- Năng lực: Giải quyết vấn đề toán học
- Mức độ gặp trong các đề đã xem: 7/7 đề

**Phần II, câu 4, ý c** · Đúng/sai · 0,25 điểm · mức **Hiểu**
- Chủ đề (một chương của phạm vi kiểm tra): Xác suất có điều kiện (lớp 12)
- Mục tiêu đánh giá: Tính xác suất toàn phần của một biến cố.
- Dạng câu hỏi và dữ kiện: Phát biểu về một số thập phân.  Tình huống chung của câu: một xét nghiệm hoặc một dây chuyền sản xuất có hai bước, cho tỉ lệ phần trăm của từng bước (độ chính xác của xét nghiệm, tỉ lệ mắc bệnh trong cộng đồng).
- Năng lực: Giải quyết vấn đề toán học
- Mức độ gặp trong các đề đã xem: 7/7 đề

**Phần II, câu 4, ý d** · Đúng/sai · 0,25 điểm · mức **Vận dụng**
- Chủ đề (một chương của phạm vi kiểm tra): Xác suất có điều kiện (lớp 12)
- Mục tiêu đánh giá: Dùng công thức Bayes để tính xác suất một người thật sự mắc bệnh khi xét nghiệm dương tính, rồi nhận xét ý nghĩa của kết quả.
- Dạng câu hỏi và dữ kiện: Phát biểu về kết quả và kết luận kèm lí do.  Tình huống chung của câu: một xét nghiệm hoặc một dây chuyền sản xuất có hai bước, cho tỉ lệ phần trăm của từng bước (độ chính xác của xét nghiệm, tỉ lệ mắc bệnh trong cộng đồng).
- Năng lực: Mô hình hóa toán học
- Mức độ gặp trong các đề đã xem: 7/7 đề


### Phần III — Trả lời ngắn

**Phần III, câu 1** · Trả lời ngắn · 0,5 điểm · mức **Vận dụng**
- Chủ đề: Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số
- Bài: Bài 2 và Bài 5. Giá trị lớn nhất, nhỏ nhất và ứng dụng thực tiễn (lớp 12)
- Mục tiêu đánh giá: Lập hàm số một biến từ tình huống sản xuất hoặc kinh doanh (doanh thu, lợi nhuận, chi phí), tìm giá trị lớn nhất trên một đoạn và đọc kết quả đúng đơn vị.
- Dạng câu hỏi và dữ kiện: Tình huống một doanh nghiệp có công thức theo số sản phẩm x trong một khoảng cho trước; đáp số là một số nguyên hoặc làm tròn đến hàng phần mười.
- Năng lực: Mô hình hóa toán học
- Mức độ gặp trong các đề đã xem: 5/7 đề

**Phần III, câu 2** · Trả lời ngắn · 0,5 điểm · mức **Vận dụng**
- Chủ đề: Hình học không gian
- Bài: Khoảng cách và góc trong không gian (kiến thức nền) (lớp 11)
- Mục tiêu đánh giá: Tính khoảng cách từ một điểm đến mặt phẳng hoặc giữa hai đường thẳng chéo nhau, hoặc góc giữa hai mặt phẳng, trong một khối chóp hoặc lăng trụ có số đo cho trước.
- Dạng câu hỏi và dữ kiện: Hình chóp hoặc lăng trụ cho bằng lời, có hình vẽ; phải dựng thêm đoạn vuông góc; đáp số làm tròn đến hàng phần mười.
- Năng lực: Tư duy và lập luận toán học
- Mức độ gặp trong các đề đã xem: 6/7 đề

**Phần III, câu 3** · Trả lời ngắn · 0,5 điểm · mức **Hiểu**
- Chủ đề: Tổ hợp và xác suất cổ điển
- Bài: Quy tắc đếm, hoán vị, chỉnh hợp, tổ hợp (kiến thức nền) (lớp 11)
- Mục tiêu đánh giá: Đếm số cách sắp xếp hoặc chọn thỏa một điều kiện ràng buộc đơn giản bằng quy tắc nhân, hoán vị hoặc tổ hợp.
- Dạng câu hỏi và dữ kiện: Một tình huống xếp chỗ hoặc chọn nhóm có một điều kiện ràng buộc; đáp số là một số nguyên.
- Năng lực: Giải quyết vấn đề toán học
- Mức độ gặp trong các đề đã xem: 5/7 đề

**Phần III, câu 4** · Trả lời ngắn · 0,5 điểm · mức **Hiểu**
- Chủ đề: Hệ bất phương trình bậc nhất hai ẩn
- Bài: Bất phương trình bậc nhất hai ẩn và quy hoạch tuyến tính (kiến thức nền) (lớp 10)
- Mục tiêu đánh giá: Từ miền nghiệm đã cho (hoặc hệ bất phương trình đã lập sẵn), tìm giá trị lớn nhất hoặc nhỏ nhất của biểu thức mục tiêu tại các đỉnh.
- Dạng câu hỏi và dữ kiện: Một cơ sở sản xuất hai loại sản phẩm; miền nghiệm cho sẵn dưới dạng hệ bất phương trình; đáp số là một số nguyên.
- Năng lực: Mô hình hóa toán học
- Mức độ gặp trong các đề đã xem: 3/7 đề

**Phần III, câu 5** · Trả lời ngắn · 0,5 điểm · mức **Vận dụng**
- Chủ đề: Nguyên hàm và tích phân
- Bài: Bài 13. Ứng dụng hình học của tích phân (lớp 12)
- Mục tiêu đánh giá: Tính thể tích một vật thể hoặc một khối tròn xoay mô tả bằng đồ vật thật (bình, chân đế, vật trang trí) bằng tích phân, kèm đổi đơn vị.
- Dạng câu hỏi và dữ kiện: Hình phẳng cho bằng công thức hàm số quay quanh trục, hoặc diện tích thiết diện cho theo x; đáp số làm tròn.
- Năng lực: Mô hình hóa toán học
- Mức độ gặp trong các đề đã xem: 3/7 đề

**Phần III, câu 6** · Trả lời ngắn · 0,5 điểm · mức **Vận dụng**
- Chủ đề: Phương pháp tọa độ trong không gian
- Bài: Bài 7, Bài 14 và Bài 17. Tọa độ, mặt phẳng và mặt cầu (lớp 12)
- Mục tiêu đánh giá: Đặt hệ trục tọa độ vào một tình huống thực tế (Trái Đất, căn phòng, công trình), lập phương trình mặt cầu hoặc mặt phẳng và tính một khoảng cách hay một tham số.
- Dạng câu hỏi và dữ kiện: Tình huống có đơn vị đo; phải chọn gốc tọa độ hợp lí; đáp số làm tròn đến hàng phần mười.
- Năng lực: Mô hình hóa toán học
- Mức độ gặp trong các đề đã xem: 3/7 đề

## 6. Cơ sở của việc chọn chủ đề

Mình xếp các câu của 7 đề Toán 2025–2026 vào bài bằng tay, dựa vào phần đầu của từng câu: đề chính thức 2025 mã 0101 và 6 đề của các sở (Bắc Ninh, Đà Nẵng, Hà Tĩnh, Hải Phòng lần 1 và lần 2, Phú Thọ). Số đề ghi ở mỗi câu là số đề có ít nhất một câu thuộc dạng đó, kiểm đếm tay nên chỉ là ước lượng.

Những dạng xuất hiện gần như đề nào cũng có:
- Phần I: phương trình hoặc bất phương trình mũ và lôgarit (7/7); vectơ chỉ phương hoặc vectơ pháp tuyến (6/7 và 5/7); cấp số cộng hoặc cấp số nhân (6/7); tứ phân vị của mẫu số liệu ghép nhóm (6/7); nguyên hàm của hàm cơ bản; thể tích khối chóp hoặc lăng trụ; vectơ trong hình hộp.
- Phần II: gần như mỗi đề có một câu khảo sát hàm số hoặc đạo hàm gắn thực tế, một câu tích phân (vận tốc, diện tích, thể tích), một câu Oxyz tình huống (máy bay, đường đi), và một câu xác suất có điều kiện kiểu xét nghiệm (7/7).
- Phần III: tối ưu bằng đạo hàm, hình học không gian (khoảng cách, góc), đếm tổ hợp, quy hoạch tuyến tính, tích phân thể tích, Oxyz với mặt cầu.

**Hạn chế cần biết:**
- Chỉ mã 0101 chắc chắn là đề chính thức. Sáu đề sở là các file trong `outputs/official-exams-2025/drive-provincial-toan`; nguồn gốc chưa được xác minh, có thể là bản dựng lại.
- Mã đề 0101 mới có nhãn mức độ do phiên làm việc gắn, chưa có nhãn chính thức nào.
- Chưa có các mã đề khác của 2025 hay đề chính thức 2026. Kế hoạch OCR đề tỉnh (`docs/release/next/ocr-provincial/HANDOFF.md`) sẽ bổ sung; danh sách dạng kinh điển sẽ đổi khi có thêm đề.
- Đề tham khảo 2025 (kết quả OCR-1) không dùng để lấy chủ đề vì quy tắc 'đề tham khảo chỉ làm khung'.

## 7. Các quyết định của chủ app (29/10)

1. Tỉ lệ mức độ cân bằng hơn: Biết 10, Hiểu 14, Vận dụng 10 (đã áp dụng).
2. Giữ kiến thức lớp 10 và 11 (đã giữ, 8 trên 22 câu).
3. Các bài ít gặp (8, 10, 16) không đưa vào; ma trận chỉ gồm nội dung thường ra (đã áp dụng).
4. Phần II không gắn bài, chỉ gắn từng ý; mỗi câu thuộc một chương của phạm vi kiểm tra (đã áp dụng).
5. Ghi năng lực bằng tên đầy đủ ở mỗi câu và mỗi ý (đã áp dụng).