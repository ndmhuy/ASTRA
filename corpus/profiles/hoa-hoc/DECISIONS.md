> **Quyết định sử dụng hiện hành (06/11/2026):** [USABILITY-REVIEW](USABILITY-REVIEW.md) thay thế nhãn chờ giáo viên trong các ghi nhận lịch sử bên dưới. 116 mẫu được giữ và dùng theo giả thiết nêu trong từng câu; 4 mẫu đã sửa ngữ nghĩa/nhiễu. Prototype hiện hành đã giải độc lập đủ40câu/ý,40khớpkhóa. Không yêu cầu giáo viên review; không gán teacher-approved hoặc độ khó thực nghiệm.

# Quyết định nghiên cứu — Hóa học

- Dùng `data/scoped-final-bank.json` làm nguồn chính cho 116 mẫu được nhận; bank ghi 0 mẫu hold. `data/samples-current.json` và trang mẫu phản ánh chính các bản ghi đó.
- Dùng 320 source rows trong `data/completion-plan.json` làm snapshot nhãn hiện hành; bản sao ở `data/source-observations-current.json`. Có 8 đề: 2 official và 6 provincial/third-party.
- Dùng 124 cells trong `data/scoped-coverage.json` làm phủ exact topic–part–level: tất cả covered_model_checked nhờ ít nhất một mẫu synthetic; không đồng nghĩa đã thiết kế mọi biến thể.
- Giữ Unknown cho ba địa chỉ có ảnh/OCR chưa đủ căn cứ; lý do cụ thể ở `LEVELS.md` và `completion.json`.
- Giữ riêng phân bố nguồn và mẫu synthetic; không dùng số lượng mẫu để tuyên bố tần suất corpus. Topic tích hợp có thể làm tổng theo topic chồng lấp.
- 23 topic guide đã khôi phục và T24/T25 đã được viết; các tần suất cũ được gắn nhãn lưu trữ hoặc thay bằng bảng hiện hành.
- Trạng thái dossier: `agent_reviewed_usable_with_stated_assumptions`. Chưa giáo viên duyệt, chưa xác thực toàn bộ answer keys, chưa tích hợp runtime; prototype render QA chờ receipt.
