# Gói hồ sơ nghiên cứu dùng cho truy xuất

Entrypoint: [profile.bundle.json](profile.bundle.json), schema `research-generation-profile-v1`. Đây là đề xuất hợp đồng dữ liệu; chưa có adapter hoặc phép thử tương thích pipeline thật.

- `topic_packs`: các đơn vị truy xuất riêng. `topic_key` giữ khóa đối chiếu nội bộ, `topic` là nhãn hiển thị đã có rà bổ sung nếu cần. Không dùng nhãn hiển thị để thay ID của biên nhận đã lưu.
- `path` của mỗi gói và các con trỏ như `paper_structure`/`acceptance` tính từ thư mục chứa bundle. `source_evidence[].path`, ref tới biên nhận model và ref nguồn trong từng gói tính từ gốc corpus. `corpus_root_hint` chỉ là gợi ý vị trí hiện tại, không phải đường dẫn portable bắt buộc.
- Hash SHA-256 trong manifest xác định đúng byte của từng gói tại lần xuất. `completion.json` lưu hash các đầu vào; cần đọc đồng thời để tránh ghép hai phiên bản khác nhau.
- `shape_defaults` lấy từ snapshot cấu hình đã ghim. Đó là mặc định, không phải quy tắc cấm một đề riêng đổi số câu. Thứ tự phần và dữ kiện dùng chung của từng nguồn ở `paper-structures.json`; thứ tự quan sát không suy thành quy luật mọi mã đề.

Một gói chủ đề chứa các lớp riêng:

1. `topic`: phân bố theo nguồn/phần, lớp, pattern đã tổng hợp, ref hỗ trợ, đối chiếu ma trận/prototype và ghi chú tên họ.
2. `construction_observations`: khái quát cấu trúc câu nguồn đã chấp nhận; không có câu gốc hoặc dữ liệu số đặc trưng của câu gốc. Đây là bằng chứng để học cách dựng, không phải câu đưa thẳng vào đề.
3. `level_assignments`: NB/TH/VD trên bản khái quát, kèm lý do và confidence; null vẫn là chưa rõ. Phân hóa thấp/vừa/cao nằm ở lớp quan sát và không tự chuyển thành NB/TH/VD.
4. `examples`: chỉ các ví dụ mới đã khớp khóa, mức, biên nhận và kiểm tra hiện tại. Mỗi ví dụ giữ đề, đáp án, lời giải, cơ chế sai, biến thể và lượt tự giải. `origin` xác định đây là nội dung tổng hợp, không phải nguồn tần suất.
5. `unready_example_ids` và `missing_example_ids`: ô còn cờ hoặc chưa có ví dụ. Không dùng chúng như ví dụ chuẩn và không đổi “thiếu” thành “chủ đề không xuất hiện”.

Địa chỉ câu nguồn là `(paper_id, part, idx, sub)`: `idx` tính trong phần; `sub` là ý khi có. Không chuyển thành số câu toàn đề. Các ý TF và dữ kiện chung thuộc cùng một câu phải đi cùng nhau. Một câu tích hợp có thể hỗ trợ nhiều chủ đề; không cộng các bảng hiện diện thành tổng số câu.

Bộ thích nghi tương lai cần truy xuất những gói liên quan, giữ riêng chính thức/tỉnh và ví dụ mới, đồng thời truyền cả giới hạn bằng chứng. Không nên đưa toàn bộ hàng của mọi chủ đề vào một prompt. Đối sánh lập kế hoạch/sinh đề trong pipeline dùng Luna theo chỉ đạo chủ app; các ví dụ trong hồ sơ này dùng Sol.
