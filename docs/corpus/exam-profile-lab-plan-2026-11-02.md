# Lab hồ sơ đề: nâng độ khó và chất lượng câu hỏi

Cập nhật 2 tháng 11 năm 2026. Trạng thái: **đang dừng, chờ chủ app báo chạy tiếp.** Không tự đặt lịch.

Thư mục lab: `~/Lecturing_Lab/agent-review/TOAN-PROFILE-1102/`. Code nền: nhánh `claude/agent-runner`, worktree `~/Lecturing_Lab/wt-agent-runner`. Lab không sửa code sản phẩm.

## Vấn đề

Giáo viên nhận xét câu phân hoá chưa đủ khó, và còn câu mang đặc trưng LLM như hỏi ngày tháng môn Lịch sử. Thiết kế dùng đề mẫu để rút ra chủ đề hay ra và cách ra đề chưa từng chạy tự động. Đề Sử chạy thật ngày 2/11 có đáp án đúng là phương án dài nhất ở 22/24 câu Phần I, đề thật 2026 là 8/24.

## Nguyên tắc (chủ app, 2/11)

- Không chặn câu hỏi bằng code. Luật theo từng lỗi không phủ hết mọi môn.
- Giải pháp phải tổng quát để LLM tự cải thiện chất lượng. Môn mới chỉ cần thêm đề, không thêm luật.
- Các phép đo chỉ dùng để chấm thí nghiệm, không dùng để chặn câu trong app.
- Đề gốc không đi vào app; app chỉ dùng hồ sơ dẫn xuất.

## Ba lớp cần kiểm chứng

1. **Dữ liệu:** một agent ngoài app đọc đề thật theo một lược đồ chung, rồi tạo hồ sơ: chủ đề và lớp, cách dựng câu, cách tạo phương án nhiễu, nguồn của độ khó, cách dùng dữ kiện. Code đếm số đề từ tham chiếu.
2. **Đường dẫn vào câu hỏi:** hồ sơ đi vào bước lập kế hoạch và composer. Composer phải bám ý tưởng của ô; ở đề Sử, ý tưởng đã bị bỏ qua.
3. **LLM tự phản biện:** dùng cùng một bộ câu hỏi cho mọi môn. Không có kiến thức có loại được phương án không? Câu này thực sự đo gì? So với dạng trong hồ sơ thì dễ hơn ở đâu? Lab hiện đặt bước này trong prompt composer. Một lượt đọc độc lập chỉ thử sau, nếu cần.

## Dữ liệu của lab Toán

- Dựng hồ sơ: 9 đề tỉnh 2026 (nhánh corpus `ocr-4-20261029`). Danh sách ở `papers/INDEX.txt`.
- Mốc so sánh: đề chính thức 2026, không đưa vào hồ sơ. Đề tỉnh có thể khó hơn đề thật.
- Lịch sử chưa đủ dữ liệu: có 2 đề làm bằng chứng nội dung, cần chép thêm đề tỉnh.

## Các bước

| # | Bước | Trạng thái |
|---|---|---|
| 1 | Viết prompt chung, chia dữ liệu, viết bộ chạy | Xong; phần gắn prompt mới qua kiểm tra, chưa chạy thật |
| 2 | Trích từng đề (`extract.py`, Sonnet) | 3/9 đề tỉnh và đề 2026 xong; 6 đề bị lỗi 429 |
| 3 | Tổng hợp hồ sơ (`aggregate.py`) | Chưa chạy |
| 4 | Sinh đề cùng đường chạy: A1, A2 không hồ sơ; B1, B2 có hồ sơ (Haiku) | Chưa chạy |
| 5 | Kiểm tra hồ sơ có bao phủ đề 2026 giữ riêng không | Chưa viết |
| 6 | Chấm mù A, B và đề 2026; đo độ dài đáp án, số bước suy luận, độ giống đề gốc | Chưa viết |
| 7 | Đóng gói prompt, test case, output để chủ app duyệt | Chưa làm |

Chạy tiếp bước 2 đến 4 (bỏ qua đề đã trích):

```bash
~/Lecturing_Lab/agent-review/TOAN-PROFILE-1102/run_all.sh
```

Lưu ý: `claude -p` hết hạn mức tuần, mở lại lúc 22:00 ngày 2/11. Lab tốn khá nhiều hạn mức. Không dùng API có tính phí khi chưa được duyệt.

## Cách đọc kết quả

| Kết quả | Kết luận | Việc tiếp theo |
|---|---|---|
| Hồ sơ bao phủ đề 2026 kém | Dữ liệu hoặc bước trích chưa đủ | Bổ sung đề, sửa prompt trích |
| Hồ sơ tốt, kế hoạch tốt, câu vẫn dễ | Composer chưa bám hồ sơ | Sửa đường dẫn vào composer, thử lượt phản biện độc lập |
| B tốt hơn A rõ rệt ở cả 2 lần | Hướng này đúng | Xin duyệt prompt, thêm mức phân hoá có mẫu, mở rộng môn |
| A và B không khác nhau | Haiku có thể là giới hạn | Chỉ khi đó thử model mạnh hơn cho câu phân hoá |

## Quyết định của chủ app (2/11, sau lượt đo chi phí)

- Lab so sánh chạy bằng CLI, không dùng API key nữa, bỏ qua mọi bước cần hình. Chờ CLI có hạn mức rồi mới chạy.
- Việc ưu tiên trước mắt là xử lí dữ liệu.
- Lượt đo chi phí đã xong: một đề Toán có kiểm tra hình, 39 lượt gọi, 0,156 USD theo bảng giá trong code. Lưu ở `~/Lecturing_Lab/fixtures/runs/2026-11-02_toan_haiku_cost1/`.

## Giới hạn

- Mỗi nhánh chỉ có 2 đề, nên kết quả là tín hiệu, chưa phải kết luận thống kê.
- Dev CLI không áp dụng effort.
- Bước trích chỉ đọc mô tả hình, không đọc ảnh.
- Mức phân hoá trong dữ liệu trích là nhận định của model, chưa được giáo viên xác nhận.
- Cần chủ app duyệt trước khi đưa prompt mới vào sản phẩm.
