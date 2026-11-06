# Duyệt sử dụng GDKTPL — 06/11/2026

**Có thể lấy dùng 73 câu mẫu theo đúng dữ kiện và giới hạn đang viết.** Agent đã đọc lại 73 câu, kiểm 157 đáp án/ý và các phạm vi riêng của 21 guide, tái sử dụng những lượt giải không nhận khóa đã có. Đây là lượt đối chiếu có thấy khóa, không tự gọi là kiểm độc lập mới. Không yêu cầu giáo viên duyệt tiếp để dùng các mẫu này.

[Ngân hàng JSON hiện hành](data/samples-current.json) · [Danh sách mẫu đọc được](SAMPLES.md) · [Quyết định từng mẫu](USABILITY-REVIEW.json) · [Nguồn pháp lí đã kiểm](LEGAL-CONTEXT-20261106.json).

## Phân loại hai trục

- **Tính đúng:** dùng được; dùng được theo điều kiện/phạm vi; chưa xác định; sai như đang viết.
- **Bằng chứng:** đã suy luận/đối chiếu được; đã kiểm nguồn sơ cấp trong phạm vi cụ thể; còn thiếu; không áp dụng.

Thiếu khóa nguồn, chưa có thống kê học sinh, không có đề Bộ trong corpus hoặc không có giáo viên duyệt không phải chứng cứ nội dung sai. Không xóa câu nguồn hay câu mẫu trong lượt này. Bốn nhãn mức nguồn Unknown vẫn giữ; không diễn giải Unknown thành sai hoặc không dùng được.

## Đã sửa nội dung cụ thể

1. **KT-F-031:** nêu rõ M1/M2 và thu nhập vào đầu từng tháng trước chi tiêu, để điều kiện dự phòng sau mỗi khoản chi không phụ thuộc thứ tự bị bỏ lửng. Khóa B giữ nguyên. Mua ngay: số dư 15 rồi 15; trả góp: 20 rồi 14. Hạ nhãn VD xuống **TH** vì kiểm số dư liên hoàn là quy trình quen thuộc, không tự thành VD do có hai tháng.
2. **KT-F-030, KT-X-010:** nêu mỗi đợt đúng một thùng, chỉ chuyển sau khi mẫu đã được lấy đủ và niêm phong; không thể suy vị trí mẫu từ việc chuyển một thùng rỗng. Kết luận về M vẫn đúng theo thứ tự thời gian.
3. **KT-F-027:** làm rõ giới hạn vay tiền ngoài ba thỏa thuận đã nêu. P là tín dụng đầu vào được cho phép trong chính đề: còn 12 cuối cùng, N còn 11; không đánh đồng cấm vay ngoài với cấm mọi thỏa thuận trả chậm.
4. **KT-F-032:** lời giải chỉ so khả năng tự trang trải tại tuần 2, không suy mức lương hoặc nhu cầu ăn sau hai tuần khi đề chưa cho.
5. **18 guide T01–T18:** bỏ quy tắc điểm mặc định 0,25/ý. Kiểm đúng/sai từng ý và quy đổi điểm theo cả câu là hai việc khác nhau; điểm phải lấy từ đề đích. T19/T21 được nối thêm biên nhận luật của lượt này; các tệp nguồn cũ vẫn tồn tại trong git, dù không hiện ở sparse checkout.

**Không có câu mẫu bị loại vì sai.** Các sửa trên làm điều kiện rõ hơn, sửa giới hạn suy luận và một nhãn nhận thức. Nội dung dùng được vẫn giữ nguyên.

## Ma trận và mức nhận thức

Sau khi sửa KT-F-031, **76/77 ô mục tiêu** còn có mẫu đúng mức. Ô còn thiếu là **T16/P1/VD**, vốn chỉ được đề xuất, không có source ref bắt buộc. KT-F-031 tiếp tục dùng ở TH; không giữ nhãn VD để tô đủ coverage. Người lấy mẫu có thể dùng ngay 73 mẫu hiện hành, nhưng không coi ngân hàng này đã có ví dụ cho mọi cấu hình VD có thể yêu cầu.

Không có dữ liệu học sinh để đo độ khó/phân hóa; nhãn NB/TH/VD vẫn mô tả yêu cầu tư duy tối thiểu.

## Bằng chứng luật và câu nguồn

Đã đối chiếu các mệnh đề cần thiết với nguồn Chính phủ/LHQ trong [biên nhận luật](LEGAL-CONTEXT-20261106.json): Hiến pháp và sửa đổi203/2025, quyền sở hữu, khái niệm khiếu nại theo VBHN28/2026, điều ước theo VBHN10/2026 và Vienna1969, nội thủy, biện pháp hòa bình. Biên nhận phân biệt toàn văn đã mở với trích đoạn chỉ đọc được qua chỉ mục tìm kiếm; không tuyên bố đã rà tất cả sửa đổi pháp luật.

Mẫu hợp đồng/thuế/biển giả định vẫn là bài tập theo quy tắc cho sẵn, không biến điều khoản giả thành luật hiện hành. Không tự thêm mức phạt, mức hưởng, tuổi, thời hạn, thẩm quyền hoặc quyền miễn trừ.

560 hàng nguồn của 14 đề tỉnh được giữ; lượt này không giải lại toàn bộ khóa nguồn. Đây là **bằng chứng còn thiếu**, không phải phán quyết rằng các hàng ấy sai. Không dùng số lần xuất hiện trong 14 đề làm chuẩn tần suất chính thức.

## Lấy và dùng

Mở SAMPLES.md để lấy nguyên câu và lời giải; hoặc đọc `data/samples-current.json`. Mỗi câu có trạng thái `agent_reviewed_for_use`, đáp án, mức và điều kiện sử dụng. Giữ nguyên đoạn dẫn/các ý trong cùng câu chùm. Khi thay dữ kiện hoặc đưa vào đề mới phải giải lại câu mới.

Tool S-C2 hiện xuất **560 source items, 31 groups, 0 synthetic samples** cho GDKTPL vì adapter đang Tier C. Hồ sơ có 73 mẫu dùng trực tiếp, nhưng chúng chưa tự đi vào gói runtime; cần product lane hỗ trợ schema trước khi gọi là đã plug in. CLI xanh không thay kết luận này.
