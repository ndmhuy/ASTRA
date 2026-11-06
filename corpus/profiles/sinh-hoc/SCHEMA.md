# Hợp đồng dữ liệu nghiên cứu — Sinh

profile.bundle.json là điểm vào; bundle_path_base là thư mục chứa bundle, source_path_base là corpus_root. Các topics/*.json là đơn vị truy xuất theo họ chủ đề; không đưa toàn corpus vào mọi prompt. Mỗi pack có quan sát khái quát, refs nguồn, nhãn mức và ví dụ synthetic đã qua kiểm tra hiện có; unready/missing tách riêng. completion.json giữ trạng thái nghiệm thu.

Địa chỉ là part/index/sub, printed index giữ riêng. Câu TF và ngữ liệu phụ thuộc được mang nguyên nhóm; không tách một ý khỏi dữ kiện. class official/provincial và mẫu synthetic không trộn. raw topic key dùng để nối receipt đã đóng băng; display_topic và terminology/ là bản đọc chuẩn hóa, không thay ID hoặc nguồn.

Đây là schema đề xuất cho nghiên cứu, chưa chứng minh tương thích runtime. Tiêu chí sử dụng nằm ở CRITERIA.md; giới hạn và quyết định nằm ở DECISIONS.md.
