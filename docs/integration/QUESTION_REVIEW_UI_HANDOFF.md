# ASTRA Handoff UI duyệt từng câu hỏi

Dành cho nhóm UI/UX và backend ASTRA. Giáo viên hoặc giám khảo cần thấy ngay câu nào còn vướng, mở đúng câu để kiểm tra và bấm **Duyệt câu** sau khi xác nhận nội dung và đáp án đúng.

## 1. Duyệt từng câu sau khi kiểm tra

- Trong **Xem đáp án**, đặt nút **Duyệt câu** cạnh **Chỉnh sửa** và **Giải kiểm tra lại**. Giữ các thao tác nhìn thấy được trên màn hình cảm ứng và khi dùng bàn phím.
- Hiển thị đề bài, đáp án dự kiến, kết quả giải độc lập và lý do bị gắn cờ trong cùng một thẻ. Với câu đúng/sai, ghi cụ thể ý a–d khi dữ liệu cho biết ý nào có vấn đề.
- Sau khi lưu thành công, thẻ hiện **Đã duyệt**, tên người duyệt và thời điểm nếu API cung cấp. Giáo viên vẫn có thể sửa câu. Khi nội dung, đáp án hoặc ngữ liệu dùng chung của câu thay đổi, đưa các câu bị ảnh hưởng về **Chưa duyệt**.
- Khi Solver và đáp án dự kiến còn lệch nhưng người duyệt xác nhận đáp án dự kiến đúng, hiển thị yêu cầu ghi lý do xác nhận. Lưu kết quả đối chiếu gốc cùng quyết định của người duyệt để người xem sau hiểu vì sao câu được chấp nhận.
- **Duyệt đề** vẫn là bước riêng ở cấp đề, gắn với bản xem trước và phiên bản đang xuất. Điều kiện cần duyệt từng câu trước khi duyệt đề là điểm UI và backend cần thống nhất.

## 2. Gom các câu có vấn đề vào một danh sách

Đặt một vùng **Câu cần xử lý** ngay trên nội dung đề trong chế độ kiểm tra. Mỗi câu xuất hiện một lần, theo thứ tự trong đề, với nhãn dễ tìm như **Câu III.3**. Khi bấm vào một hàng, mở đúng câu và phần đối chiếu đáp án. Khi có nhiều vấn đề trên cùng một câu, hiển thị lý do quan trọng nhất trước và cho mở các chi tiết còn lại.

| Tín hiệu | Nhãn UI | Thao tác chính |
| --- | --- | --- |
| `answerCheck=mismatched` | Lệch đáp án | Xem hai kết quả, sửa hoặc ghi lý do xác nhận. |
| `answerCheck=needs_recheck` hoặc chưa có kết quả | Cần đối chiếu | Xem lý do, sửa nếu cần rồi giải kiểm tra lại. |
| `answerCheck=matched`, chưa có duyệt của người | Khớp đáp án · Chưa duyệt | Kiểm tra nội dung rồi duyệt câu. |
| Đã có xác nhận của người duyệt cho nội dung hiện tại | Đã duyệt | Xem chi tiết quyết định khi cần. |
| Cảnh báo RAG hoặc hình/bảng | Lưu ý nguồn hoặc hình/bảng | Gộp theo câu và cho mở chi tiết. Đếm riêng với các câu vướng đáp án. |

Dùng số **câu riêng biệt** cho bộ đếm. Giữ những câu đã duyệt trong đề và tab đáp án để xem lại. Khi đã xử lý hết lỗi đáp án, vùng này hiện **Đã đối chiếu hết các câu bị gắn cờ** và vẫn cho xem danh sách câu chưa được người duyệt xác nhận.

**Ca tái hiện:** Câu III.3 của đề xác suất yêu cầu kết quả chính xác, người soạn ghi `0,67` và Solver trả `2/3`. Hàng **Câu III.3 · Cần đối chiếu** cần hiển thị cả hai kết quả, kèm lý do chưa thể so sánh tự động. Sau khi sửa đề bài thành yêu cầu làm tròn đến hàng phần trăm, giáo viên có thể giải kiểm tra lại rồi duyệt. Các lưu ý thiếu câu mẫu RAG vẫn nằm ở mục nguồn tham khảo.

## Dữ liệu hiện có và phần cần backend

- API đọc đề trả về `questions[].stableId`, `answerCheck`, `key`, `solverKey`, `auditNotes` và `examRevision`. Có thể dùng ngay để hiển thị danh sách và lý do. [Kiểu dữ liệu frontend](../../astra-frontend/src/types/exam.ts) · [Thẻ câu hỏi](../../astra-frontend/src/components/Workspace/LiveCanvas/QuestionCard.tsx).
- `POST /api/exams/{jobId}/questions/{questionId}/verify` chạy Solver lại. `POST /api/exams/{jobId}/approve` phê duyệt toàn đề. Cần thêm thao tác **duyệt từng câu** ở backend và trả trạng thái đã lưu để UI hiển thị sau khi tải lại. [Các route API](../../src/exam_baseline/api/routes_ui.py).
- Hợp đồng đề xuất lưu quyết định theo đề, mã câu và nội dung đã duyệt, kèm người duyệt, thời điểm và lý do nếu có. Yêu cầu duyệt phải mang phiên bản đang xem. Nếu câu đã đổi trong lúc người duyệt mở màn hình, API trả xung đột để UI yêu cầu tải lại câu trước khi duyệt.

## Tiêu chí nghiệm thu

1. Đề có một câu lệch và một câu cần đối chiếu hiển thị **2 câu cần xử lý**, kể cả khi một trong hai câu có thêm lưu ý RAG. Mỗi hàng mở đúng câu và cho thấy lý do ngay.
2. Một câu khớp đáp án vẫn hiển thị **Chưa duyệt** cho tới khi giám khảo bấm **Duyệt câu**. Sau khi tải lại, UI đọc được trạng thái **Đã duyệt** từ backend.
3. Khi sửa nội dung đã duyệt, trạng thái trở về **Chưa duyệt** ở đúng các câu bị ảnh hưởng. Hai người thao tác trên hai phiên bản khác nhau thấy thông báo xung đột rõ ràng.
4. Trên màn hình hẹp, người dùng thấy và bấm được **Xem đối chiếu**, **Chỉnh sửa** và **Duyệt câu** mà không cần rê chuột.
