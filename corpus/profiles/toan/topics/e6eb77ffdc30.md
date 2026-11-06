# Quá trình xác suất hữu hạn

[Quay về hồ sơ](../PROFILE.md)

Lớp được gắn nhãn: 11. Phần xuất hiện: P3.

| Nguồn / phần | Đề có chủ đề / tổng đề | Câu phân biệt | Ý/hàng | Thấp | Vừa | Cao | Chưa rõ |
|---|---:|---:|---:|---:|---:|---:|---:|
| Chính thức / P3 | 0/2 | 0 | 0 | 0 | 0 | 0 | 0 |
| Tỉnh/trường / P3 | 2/20 | 2 | 2 | 0 | 1 | 1 | 0 |

Số câu/ý và số đề là các đơn vị khác nhau; một câu tích hợp có thể thuộc nhiều chủ đề. Thấp/vừa/cao là nhận định phân hóa, chưa phải NB/TH/VD hay kết quả đo trên học sinh.

**Nội dung và cách hỏi quan sát được:**

- Chính thức: chưa có quan sát trong mẫu.
- Tỉnh/trường / P3: cho Hai đối thủ ngang sức, ngưỡng số lần thắng để kết thúc và trạng thái thắng hiện tại. Yêu cầu: Tính xác suất thắng chung cuộc rồi thực hiện phép biến đổi trên phân số tối giản.
  Suy luận: Xác định số lần thắng còn thiếu của mỗi bên. → Phân loại các chuỗi kết thúc bằng lần thắng quyết định của bên được xét. → Đếm thứ tự hợp lệ trước lần thắng cuối và gán xác suất cho từng loại chuỗi. → Cộng xác suất các trường hợp rời nhau. → Rút gọn phân số và tính biểu thức yêu cầu. Kết hợp: Quy tắc đếm; Biến cố độc lập; Công thức cộng xác suất; Quá trình dừng. Nguồn độ khó: Đếm chuỗi kết thúc đúng lúc, tránh tính tiếp sau khi đã có người thắng..
  Giới hạn: Đề không nêu rõ tính độc lập hay cách xử lý ván hòa; đáp án phù hợp với mô hình các ván độc lập, không hòa và hai bên có xác suất thắng bằng nhau.
- Tỉnh/trường / P3: cho Một trò chơi có điểm biến đổi theo các kết quả độc lập, dừng ngay khi chạm một trong các ngưỡng và có thời điểm kết thúc được chỉ định. Yêu cầu: Tính xác suất thắng đúng thời điểm quy định rồi thực hiện phép chuẩn hóa.
  Suy luận: Xác định các trạng thái điểm chưa kết thúc. → Suy ra trạng thái cần có ngay trước lượt thắng cuối. → Lập truy hồi hoặc phân loại các chuỗi chỉ đi qua trạng thái chưa kết thúc ở các lượt trước. → Dùng quy tắc nhân và cộng để tính xác suất đến trạng thái trước lượt cuối. → Nhân xác suất của lượt kết thúc và thực hiện phép chuẩn hóa. Kết hợp: Biến cố độc lập; Quy tắc cộng xác suất; Quá trình theo trạng thái; Điều kiện dừng. Nguồn độ khó: Loại các chuỗi chạm ngưỡng sớm dù có cùng tổng biến thiên điểm ở thời điểm cuối..
  Giới hạn: Mốc thời gian và tên riêng chỉ tạo bối cảnh, không cần nhớ hay dùng trong lời giải. Xếp lớp theo các quy tắc xác suất; cách tổ chức truy hồi không được định vị riêng trong danh mục.

**Các dạng câu và cách tạo nhiễu:**

- Chính thức: chưa có mẫu lặp được aggregate xác lập cho chủ đề này; xem mô tả từng câu phía trên.
- Tỉnh/trường / short_answer: Chọn trạng thái đủ thông tin, lập chuyển trạng thái hoặc truy hồi, khởi tạo rồi tính tới mốc yêu cầu; khi tính xác suất, gắn trọng số và loại lịch sử đã dừng. Nhiễu: không áp dụng/chưa rõ

**Đối chiếu ma trận và NB/TH/VD:**

- Họ chủ đề này chưa được ánh xạ vào một chương mặc định; cần xem kết luận audit trước khi đề xuất thêm.

**Cách dùng dữ kiện thuộc lòng — số câu/ý trong mẫu:**

| Nguồn | Hỏi trực tiếp | Cho làm gợi ý | Cần trong suy luận | Không dùng | Chưa rõ |
|---|---:|---:|---:|---:|---:|
| Chính thức | 0 | 0 | 0 | 0 | 0 |
| Tỉnh/trường | 0 | 0 | 2 | 0 | 0 |

**Cách tăng yêu cầu suy luận có bằng chứng:**

- Tỉnh/trường: Theo dõi danh tính, thuộc tính và thành phần còn lại qua từng bước; tính trọng số có điều kiện rồi gộp đủ nhánh. Với quá trình dài, nén lịch sử vào trạng thái đủ thông tin, khởi tạo đúng và loại lịch sử đã dừng. — có refs thuộc chủ đề trong 1 đề.

**NB/TH/VD quan sát — đơn vị câu/ý:**

| Nguồn / phần | NB | TH | VD | Chưa rõ |
|---|---:|---:|---:|---:|
| provincial_third_party / P3 | 0 | 0 | 1 | 1 |

Nhãn dựa trên khái quát đã trích, chưa phải rà toàn bộ câu gốc hoặc điểm học sinh. TF đếm từng ý; slot mặc định đếm câu. Không so trực tiếp hai đơn vị này.

**Mức toàn câu có chứa chủ đề — cùng đơn vị câu với slot ma trận:**

| Nguồn / phần | NB | TH | VD | Chưa rõ |
|---|:---:|:---:|:---:|:---:|
| provincial_third_party / P3 | 0 | 0 | 1 | 1 |
Lấy mức cao nhất của toàn bộ ý trong câu; có ý chưa rõ thì cả câu giữ chưa rõ. Với câu tích hợp, mức này có thể do kiến thức khác quyết định. Không cộng bảng của nhiều chủ đề thành tổng câu hoặc chuyển thành hạn ngạch NB/TH/VD.

**Audit ma trận liên quan:**

| Phần | Slot mặc định | Đề chính thức có | Đề tỉnh có |
|---|---:|---:|---:|
| P3 | 0 | 0 | 2 |
Mẫu số và kết luận đề xuất ở [audit ma trận](../../../audit/matrices/toan.md). Hiện diện không tự chứng minh cần tăng số slot; lớp bằng chứng tách riêng.

**Prototype liên quan đến chủ đề:**

Chưa nối được câu prototype vào chủ đề qua mapping đã kiểm; không coi đây là bằng chứng prototype không có chủ đề.

**Câu mẫu mới của chủ đề:**

[Đọc 1 câu mẫu, đáp án, lời giải và lượt tự giải của chủ đề](../samples/topics/e6eb77ffdc30.md). Mẫu tổng hợp mới, chờ giáo viên; mẫu có cờ chưa sẵn dùng.

