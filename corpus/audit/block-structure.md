# Câu chùm và thứ tự phần/nhóm — audit đang thực hiện

## Phạm vi bằng chứng

Đã đọc code ở revision `de8c614ada6e3ae9f9072cedb7521fb96c1d13e5`, probe registry thuần dữ liệu và đọc marker/header của các prototype thật. Chưa chạy một pipeline product end-to-end để xác nhận mọi đường vào; không mở UI và không sửa product. Các kết luận dưới đây phân biệt dữ liệu khai báo, đường truyền code và đầu ra.

## Cơ chế đã có

- Thứ tự **phần địa chỉ** lấy từ layout/format. V-ACT có bốn phần địa chỉ để chấm bài; các tiêu đề lớn in trên giấy được khai báo riêng. Không gộp địa chỉ theo tiêu đề in.
- Các ngoại ngữ có danh sách block theo loại và số câu. Một order chuẩn được lưu, còn comment của registry ghi rõ một số mã đề hoán vị block. Không suy thành mọi mã đều cùng order, hoặc bài đọc luôn cuối.
- GDKT&PL P1 có rule **vị trí thay đổi theo đề**; shape hiện cho phép ba cặp, hoặc một cặp cùng một bộ ba. Đây là rule registry hiện hành, chưa phải kết luận bao phủ hết mọi đề tỉnh.
- Ngữ văn có stimulus NGU_LIEU dùng xuyên P1 và câu viết liên quan ở P2. Cần giữ liên kết khi lập kế hoạch, sinh và viết lại.
- Một block độc lập như nhóm sắp xếp câu hoặc tìm lỗi không tự động là một ngữ liệu dùng chung. Bốn ý đúng/sai thuộc một câu không được đếm thành chùm bốn câu.

## Đường truyền đang có

| Đường | Bằng chứng code | Giới hạn |
|---|---|---|
| Registry → plan v2 | plan_v2.shape đọc blocks và block_rule; validate nhóm và chỉ số | Phụ thuộc session dùng v2 |
| Plan v2 → composer | plan_context.role_context chứa groups/order_note; pipeline gắn data_block + COMPOSER_SCOPE | Chưa có replay runtime trong audit này |
| Plan cũ → rule nhóm linh hoạt | stored_plan._ruled_parts và _shape_findings | Rule linh hoạt chỉ chạy khi matrix_round bật |
| Composer block cố định | composer.block_requirement đọc blocks_for | Trả chuỗi rỗng cho phần không có block cố định; không thể lấy nó làm chứng minh rule vị trí tự do đã truyền |
| Assembler | render_blocks tính khoảng câu từ phần thật; printed_headings tách trình bày/địa chỉ | Render marker không chứng minh nội dung các câu thật sự cần chung stimulus |
| Structural gate | Đọc count, địa chỉ, ý và lựa chọn | Không có code block_order/stimulus_dependency trong CODES hiện tại |

Probe công tắc mặc định nằm ở `audit/outputs/block-structure-audit.json`: slot_table bật ở graph mới; matrix_round/stored_plan không tự bật chỉ vì graph mới. Khi session có planning_request, adapter v2 được chọn và vẫn cần envelope được chấp nhận. Không kết luận mọi cách tạo session đã đi qua một đường duy nhất.

## Đầu ra prototype hiện có

| Đối tượng | Quan sát | Cách đọc |
|---|---|---|
| GDKT&PL v3 | Năm cặp có header dùng chung; shape_accepts trả false cho dãy năm cặp | Lệch rule hiện tại; cần đối chiếu đề thật trước khi quyết định sửa rule hay đầu ra |
| Tiếng Anh v2 | Đủ multiset loại/số câu, thứ tự khác canonical | Hoán vị không tự là lỗi của đề; chưa khẳng định tuân prompt canonical hiện tại |
| Tiếng Đức v3, Pháp v3 | Marker và số câu khớp canonical | Chứng cứ đầu ra này, không chứng minh toàn bộ run |
| V-ACT | Các block bốn phần khớp registry | Đã kiểm nguồn MH và R1 ở phần khoa học: đều sáu nhóm ba câu; không dùng R2 thiếu phần cuối để suy bổ sung |

## Cần giữ trong hồ sơ/đề xuất ma trận

- Ghi order **quan sát trên từng đề**, nhóm dùng chung và các thành viên bằng địa chỉ trong phần. Đếm hiện diện theo đề, tách chính thức/tỉnh và ghi rõ bằng chứng ít.
- Phân biệt cố định theo registry, hoán vị được nguồn cho thấy, và vị trí nhóm tự do; không biến một order quan sát thành luật phổ quát.
- Giữ ngữ liệu xuyên phần và các nhánh tự chọn. Cùng chủ đề không đồng nghĩa cùng ngữ liệu.
- _PART_TOPICS vẫn là đề xuất chủ đề theo shape cũ; ràng buộc nhóm/thứ tự được nêu kèm, không tự sửa format hoặc product.
- Bổ sung structural metadata vào cùng EXTRACT chung; các bản đã trích chỉ cần bước cấu trúc bổ sung, không OCR lại hoặc giải lại cả đề.

## Tệp truy nguyên

- /Users/huynguyen/Lecturing_Lab/wt-corpus-merged/audit/outputs/block-structure-audit.json
- /Users/huynguyen/Lecturing_Lab/wt-corpus-merged/audit/outputs/vact-structure-source-check.json
- /Users/huynguyen/Lecturing_Lab/wt-agent-runner/Grading_Tools/exam_formats/blocks.py
- /Users/huynguyen/Lecturing_Lab/wt-agent-runner/Grading_Tools/exam_formats/thptqg_2026.py
- /Users/huynguyen/Lecturing_Lab/wt-agent-runner/Grading_Tools/exam_generator/plan_v2.py
- /Users/huynguyen/Lecturing_Lab/wt-agent-runner/Grading_Tools/exam_generator/plan_context.py
- /Users/huynguyen/Lecturing_Lab/wt-agent-runner/Grading_Tools/exam_generator/slot_prompt.py
- /Users/huynguyen/Lecturing_Lab/wt-agent-runner/Grading_Tools/exam_generator/agents/composer.py
- /Users/huynguyen/Lecturing_Lab/wt-agent-runner/Grading_Tools/exam_generator/output/assembler.py
- /Users/huynguyen/Lecturing_Lab/wt-agent-runner/Grading_Tools/exam_generator/struct_gate.py
