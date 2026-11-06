# Luật viết ma trận đề (bản đề xuất, rút ra từ mẫu Toán 12)

Trạng thái: chủ app đã duyệt hướng ngày 2026-10-29 (5 câu trả lời trên bản mẫu Toán). Luật này chưa được nạp vào code hay prompt. Mẫu minh họa: `docs/release/next/matrix-samples-v3/toan/matrix-thuc-toan.md`.

Mục đích: một ma trận thật phải tự nói rõ mình, để người đọc và mô hình không cần giải mã ký hiệu riêng của giáo viên. Ma trận nói rõ từng câu có bao nhiêu điểm, thuộc bài nào, loại gì, mức nào, đánh giá điều gì.

## A. Đơn vị và cấu trúc

1. **Một ô là một câu.** Riêng Phần đúng/sai, một ô là một ý (a, b, c, d) của một câu. Không có ô nào đại diện cho nhiều câu.
2. **Khung đề quyết định các ô.** Số phần, số câu, số ý, điểm mỗi câu lấy từ khung đã đăng ký trong code. Ma trận chỉ điền nội dung vào các ô đó; không thêm, bớt hay đổi chỗ ô.
3. **Địa chỉ viết bằng chữ:** "Phần II, câu 3, ý c". Không dùng "C3", "1C", "2D3B3C4A4D".
4. **Phần đúng/sai không gắn bài.** Mỗi câu thuộc một chủ đề, tức một chương của phạm vi bài kiểm tra tổng thể. Từng ý có mục tiêu riêng. Phần nhiều lựa chọn và trả lời ngắn vẫn ghi bài.

## B. Mỗi khối ô gồm những trường nào

Các trường bắt buộc, theo thứ tự:

| Trường | Viết thế nào |
|---|---|
| Địa chỉ | Phần, câu, ý, bằng chữ |
| Dạng và điểm | "Nhiều lựa chọn · 0,25 điểm"; đúng/sai ghi điểm trung bình mỗi ý và nhắc quy tắc chấm bậc thang |
| Mức độ | Viết đủ "Biết", "Hiểu", "Vận dụng". Không viết "Vận" |
| Chủ đề | Tên chương theo sách giáo khoa của bộ sách đang dùng (Kết nối tri thức) |
| Bài và lớp | Tên bài kèm lớp. Nội dung lớp 10 và 11 ghi "(kiến thức nền)" và nêu lớp |
| Mục tiêu đánh giá | Một hành vi quan sát được (xem mục D) |
| Dạng câu hỏi và dữ kiện | Học sinh nhìn thấy gì (hình, bảng, công thức, tình huống), đáp án có dạng gì (số nguyên, làm tròn đến hàng phần mười) |
| Năng lực | Tên đầy đủ, không mã |
| Tần suất | Chỉ có trong bản mẫu: số đề đã xem có dạng này. Không đưa vào ma trận của giáo viên |

## C. Mức độ

5. **Định nghĩa mức độ nằm ngay trong ma trận**, bằng lời, theo hành vi của học sinh chứ không theo độ dài đề:
   - Biết: nhận ra, nêu, đọc thông tin có sẵn; một công thức hoặc một quy tắc, một bước.
   - Hiểu: thực hiện quy trình đã học trong hai đến ba bước, giải thích hoặc so sánh, đọc ý nghĩa số liệu.
   - Vận dụng: lập mô hình từ tình huống mới, kết hợp nhiều kiến thức, nhiều bước, kết luận và nêu lí do.
6. **Tỉ lệ cân bằng.** Mặc định gần 25% Biết, 40% Hiểu, 35% Vận dụng theo điểm (mẫu Toán: 10, 14, 10 ý). Số này là lựa chọn thiết kế; đề chính thức nếu có số liệu thì ghi riêng để so sánh, không thay quy tắc.
7. **Phần II xếp mức theo ý:** ý a Biết, ý b Hiểu, ý c Hiểu hoặc Vận dụng, ý d Vận dụng. Phần III chủ yếu Vận dụng, có thể có vài câu Hiểu.
8. Tổng số ô mỗi mức, tổng điểm, và tổng theo phần do **code tính**, không do mô hình viết tay. Các tổng phải bằng nhau ở mọi bảng.

## D. Mục tiêu đánh giá

9. Công thức: **động từ quan sát được + đối tượng + điều kiện cho trước + kết quả mong đợi.** Ví dụ: "Tính tứ phân vị thứ ba từ một bảng tần số ghép nhóm bằng công thức đã học."
10. Động từ phải khớp mức: Biết dùng nhận ra, nêu, đọc; Hiểu dùng tính, xét dấu, giải thích; Vận dụng dùng lập, đánh giá, kết luận.
11. Không chép tên bài thành mục tiêu. "Tích phân" không phải mục tiêu.
12. Không có số liệu hay câu chữ của đề thật trong mục tiêu. Chỉ mô tả loại tình huống.

## E. Chọn nội dung

13. **Chỉ chọn nội dung hay ra.** Dựa vào đếm trong các đề thật và đề tỉnh, ghi "gặp trong x trên N đề". Nội dung ít gặp (Bài 8, 10, 16 của Toán) không đưa vào mẫu mặc định, trừ khi giáo viên yêu cầu.
14. **Giữ kiến thức lớp 10 và 11 nếu các đề thật có.** Ma trận ghi rõ lớp.
15. Số liệu tần suất ghi rõ nguồn: đề chính thức hay đề sở, đã xác minh nguồn hay chưa. Không trộn.
16. Ma trận mẫu chỉ là ví dụ về mức chi tiết. Không sao chép chủ đề hay câu chữ của nó sang ma trận của giáo viên.

## F. Khi nhận file của giáo viên

17. **Giữ ý của giáo viên, giải mã mã ký hiệu thành chữ.** Ví dụ ô "C3C4" thành hai ô "Phần I, câu 3" và "Phần I, câu 4". Ghi chú "đã giải mã từ file".
18. **Không đổi con số của giáo viên**, trừ khi phép cộng chứng minh file mâu thuẫn. Mọi thay đổi hiện trước và sau, hoàn tác một cú nhấp (quyết định ngày 2026-10-29).
19. Ô nào file không nói (mục tiêu, dạng câu hỏi) do trợ lý bổ sung phải ghi "bổ sung bởi trợ lý". Giáo viên xác nhận trước khi sinh đề.
20. Khi file không đọc được, báo "không đọc được", không trả ma trận rỗng.

## G. Kiểm tra bằng máy (bắt buộc trước khi gửi duyệt)

- Số ô mỗi phần bằng khung đã đăng ký.
- Tổng điểm bằng 10; tổng các mức bằng tổng điểm.
- Không còn chuỗi khớp `C\d`, `\d[A-D]`, `NL\.\d`, và không có mức độ viết tắt.
- Mọi ô có đủ các trường ở mục B.
- Mỗi mục tiêu bắt đầu bằng động từ thuộc danh sách của mức tương ứng.
- Phần II không có trường Bài.

## H. Ánh xạ sang vòng ma trận v2 (chưa xây)

Trong `matrix-round-v2-prompt-proposal.md`, trường `requirement` là Mục tiêu đánh giá, `ask_style` là Dạng câu hỏi và dữ kiện, `example_stem` là một câu khung tình huống. Tên năng lực và định nghĩa mức độ cần thêm vào payload (`level_pack`). Phần G là các kiểm tra mà `validate_answer` của v2 sẽ cần.

## Chưa chứng minh

Luật này mới được áp dụng cho một môn (Toán). Chưa kiểm với GDKT&PL, Ngữ văn (câu tự luận, không có đúng/sai) và ngoại ngữ (khối đoạn văn). Các môn đó có thể cần thêm quy tắc.
