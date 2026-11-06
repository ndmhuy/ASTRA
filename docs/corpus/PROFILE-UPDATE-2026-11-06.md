# Cập nhật hồ sơ ra đề — 06/11/2026

Bản bổ sung cho snapshot ngày 03/11 trong PR này. Nguồn là kho exam-corpus nội bộ; các nhánh nguồn được giữ nguyên, không mang lịch sử Git sang ASTRA.

| Môn | Commit nguồn | Trạng thái và giới hạn |
|---|---|---|
| Toán | `2dcd095` | Bản nghiên cứu hoàn chỉnh; 9 mục nguồn chưa rõ, chưa xác nhận giáo viên hoặc runtime. |
| Sinh học | `2ec0124` | Bản nghiên cứu hoàn chỉnh; 21 mục nguồn chưa rõ, chưa xác nhận giáo viên hoặc runtime. |
| Hóa học | `59d5a2f` | Agent đã rà nội dung; 3 địa chỉ nguồn còn Unknown; không ghi là giáo viên phê duyệt. |
| Lịch sử | `1d89079` | Agent đã rà nội dung; các ô VD có điều kiện và thiếu được ghi trong hồ sơ. |
| GDKTPL | `33bcb4d` | Agent đã rà nội dung; một ô VD chưa có mẫu, không ghi là giáo viên phê duyệt. |

Đọc `PROFILE.md` và các hồ sơ QA/usability của từng môn để biết phạm vi kiểm tra và giả thiết. Các hồ sơ còn lại không được cập nhật trong lượt này. Một số đường dẫn Markdown tuyệt đối từ nguồn được chuyển thành tương đối; dữ liệu và các ghi nhận nguồn được giữ nguyên.

Kiểm tra lần chuyển: 1.052 tệp JSON trong năm hồ sơ parse thành công; quét mẫu khóa phổ biến không phát hiện kết quả. Chưa kiểm thử tích hợp runtime hoặc nghiệm thu bởi giáo viên.

Các bản gốc đề (PDF/DOCX/ảnh) tiếp tục được loại khỏi repo theo phạm vi PR ban đầu; tham chiếu đến chúng trong gói bằng chứng có thể không mở được từ bản sao ASTRA.
