# Khung đề ĐGNL HCM từ đề tham chiếu 11

`examples/hcm_de11/input.json` là request mẫu cho profile `hcm_dgnl_de11`. Profile ràng buộc 120 câu trắc nghiệm A-D theo thứ tự: Tiếng Việt 1-30, Tiếng Anh 31-60, Toán 61-90, Logic/phân tích số liệu 91-102, Suy luận khoa học 103-120. ID câu phải là `q1` đến `q120`.

Các nhóm 21-25, 26-30, 46-52, 53-60, 91-94, 95-98, 99-102, 103-105, 106-108, 109-111, 112-114, 115-117, 118-120 cần mỗi nhóm một `shared_passages` có nội dung riêng. Validator kiểm số câu, thứ tự, lựa chọn, nhóm đoạn, ngoài các ràng buộc matrix sẵn có. Chất lượng nội dung và sự phù hợp giữa đoạn với câu vẫn cần người duyệt.

Thời gian 150 phút, tổng 120 điểm và phân bố độ khó trong file mẫu là **giá trị cấu hình minh họa**, không được suy ra từ PDF. Thay chúng theo yêu cầu thực tế. Các ràng buộc cấu trúc nêu trên là từ đề tham chiếu.

Chạy với model đã cấu hình trong `.env`:

```powershell
python -m exam_baseline.draft.cli --request examples/hcm_de11/input.json --output runs/hcm_de11/live1
```

Nếu dùng RAG, thêm từng mẩu vào `evidence` với `role: "content_support"`, `id`, `text` và `locator`, bật `require_evidence: true`. Nếu dùng đề mẫu chỉ làm khung hình thức, thêm đoạn mô tả hoặc trích đoạn với `role: "form_example"`; không coi đó là bằng chứng đúng về nội dung. Không đặt lệnh điều khiển trong văn bản evidence. Khi có biểu đồ/hình bắt buộc, khai báo ID câu trong `required_visual_question_ids`; Illustrator mini chỉ hỗ trợ các loại hình trong `VisualSpec`.

Mini CLI xuất draft JSON/PNG và ba file LaTeX chưa qua Solver/Reviewer. Full pipeline
đã kiểm tra dùng `pipeline_cli`, xem [pipeline hiện tại](../architecture/PIPELINE_PLAN_AND_BENCHMARK.md).
Chưa có kết quả chấm học thuật độc lập cho đề HCM 120 câu.
