# Nhật ký đợt dữ liệu 2026-11-02

- Nhánh chủ app chỉ định: `data/merged-20261102`, sạch khi bắt đầu. Không tạo nhánh khác vì yêu cầu đích danh nhánh này.
- Chỉ ghi trong corpus worktree; product read-only; không merge/push, không full suite, không UI cũ, không khóa API tính phí.
- Chủ app xác nhận cho phép gửi nội dung và ảnh đề riêng tư qua Codex subscription sau khi bộ duyệt tự động chặn probe đầu. Probe bị chặn chưa gửi ảnh. Probe được cho phép sau đó đọc ảnh thành công.
- Model làm mẫu/OCR/profile/audit: gpt-6.1-sol. Không chạy đối sánh pipeline trong đợt này. Lượt OCR hai dùng context mới cùng model; sẽ công khai giới hạn chưa có đối chiếu khác model/giáo viên.
- Bằng chứng tỉnh, chính thức, tham khảo, app-generated tách riêng. Không lấy `provincial-toan-unverified` làm bằng chứng.
- Đã đọc corpus README, registry, schema phiên âm, OCR HANDOFF, prompt OCR cũ và EXTRACT/AGGREGATE lab. Quy tắc nguồn và công thức MathType được giữ.
- Phạm vi đọc thêm: đề Haiku chủ app đính kèm ở product; chỉ coi là prototype để audit, không coi là đề thật.
- Thiếu trang xác nhận từ STATUS trước đợt này: Sử 2025 trang 1 (câu 1–10); Sinh 2025 trang 1 (câu 1–10); GDKT&PL 2025 trang 1 (câu 1–8); Vật lí 2026 trang 4. Sử/Sinh 2026 đã có đủ bốn trang, không phải stub.

- OCR thử Cà Mau: lượt kiểm hai trang có một sửa chữ nhưng trả pass=false vì ngoài phạm vi; đã mở rộng sang toàn bộ bốn trang + khóa, giữ giới hạn cùng model, không đổi nội dung để đạt. Lượt toàn bộ trang còn một sửa chữ. Mô hình đề nghị chép thêm khóa/lời giải vào de.md; đã loại đề nghị đó vì quy ước chỉ chép phần đề. Khóa giữ key.json. Đã xem năm crop, đủ khung và nhãn; không xem đây là giáo viên duyệt.
- Snapshot ma trận ban đầu thiếu module parsers trong môi trường pure-data. Đọc hằng LADDER_BY_CORRECT bằng AST từ parsers.py rồi nạp module dữ liệu; không chạy chấm bài/app; snapshot thành công đủ mười tám môn.
- Sửa reader tổng quát để nhận Question, Câu kèm ngoặc điểm và phần Đọc/Viết. Tin học chính thức in sáu câu TF nhưng structure ghi bốn: giữ địa chỉ in trên nguồn, không ép về metadata.

- Hóa Huế không dùng như đề đầy đủ: nguồn chuyển PDF có ký hiệu phương trình lỗi, câu hình cấu tạo peptide chỉ có dòng giữ chỗ, không có hình thực. Giữ `[?]`, STATUS incomplete; không tự tái tạo hình/công thức. Bổ sung đề Nghệ An lần hai để đạt ít nhất năm tỉnh dùng được, nếu nguồn này đạt.

- Đã mở ảnh mạng xã hội Tiếng Hàn: là trang một mã 1727, không phải trang ba/bốn mã 1725. Nguồn tin cậy thấp, nhiều bút khoanh và che một phần đầu trang; không ghép với mã 1725.
- Kiểm footer Nhật cục bộ: mã 1603 có trang 1/4 và 4/4; mã 1628 có 1/4 đến 3/4, thiếu trang bốn. Mã 1630 có footer 4/4. Mã 1625/1627 footer chưa đọc được bằng OCR cục bộ, không kết luận đủ chỉ từ bốn trang PDF.
- Sinh Cà Mau: bản PDF chuyển đổi có vùng bảng câu III/5 trống; lượt hai còn phát hiện thiếu hình minh họa rái cá ở I/5. Tạm loại khỏi mẫu đầy đủ, không tự dựng bảng; cần phân biệt lỗi chuyển đổi với gốc thiếu dữ liệu. Có danh sách dự phòng để bổ sung đủ năm đề/môn nếu đủ nguồn đọc được.

- Kiểm cục bộ phép đo độ dài trên bản Sử v4 đang có: 24 MCQ đọc được bằng grammar layout gốc. Theo từ: khóa dài nhất kể hoà 16, duy nhất 7; theo ký tự: 15 và 11. Không tái hiện số 22/24 của phản ánh ban đầu trên bản này; chưa kết luận phản ánh cũ sai vì có thể khác bản và khác phép đo. Nguồn/hash và từng câu lưu history-local-length-check.json. Đây là kiểm bộ đo trước stage audit, chưa phải chấm chất lượng hoặc đối chiếu chính thức.

## Tiếp tục sau quota, 2026-11-02 chiều

- Batch Sol CLI cũ đã hết quota; wrapper đang chạy đã nạp bản cũ nên chưa có dừng chung, dẫn đến nhiều bước kế tiếp lặp cùng lỗi quota. Đây là lỗi điều phối, không phải lỗi chất lượng đề. Giữ log gốc; wrapper mới dừng toàn bộ bước phụ thuộc sau hai lỗi quota/xác thực.
- Chủ app yêu cầu tiếp tục sau mốc reset được CLI báo, và sửa phân công: model nhỏ OCR, Sol chỉ cho việc cần suy luận. OCR và đối chiếu bản chép mới chuyển sang gpt-6-luna; giữ kết quả Sol đã xong, không chạy lại chỉ để đổi nhãn. Phân tích hồ sơ, tự giải, audit nhiễu và đề xuất vẫn Sol.
- “Một model trích mỗi môn” ở stage profile sẽ áp dụng cho EXTRACT phân tích cấu trúc câu hỏi, khác với model OCR provenance. Không trộn lẫn hai khái niệm này.

## QA được quyết định bằng bằng chứng nguồn

- Cảnh báo quota chiều đã được đính chính: ba lượt Luna được dẫn đều returncode=0, có reply mới và không có usage-limit trong CLI log. Agent đã nhầm errors lịch sử trong stop record resolved với lỗi mới. Không có bằng chứng quota mới ở các lượt đó; giữ audit/outputs/quota-review-20261102.json. Mốc “2:39 PM” từ lỗi cũ không có múi giờ, không dùng để kết luận thời điểm reset.
- Bảng khóa nhiều mã Hà Nội: đã mở/zoom cột đúng, sửa một ô đọc sai và bổ sung sáu ô trả lời ngắn bị bỏ sót. Raw/model reads/key cũ giữ nguyên. source_key_resolution có ảnh/hash và read hiệu lực để QA vẫn kiểm khớp source; đây không phải tự giải để sửa key.
- Sinh Phú Thọ: ba đề nghị đổi đường dẫn hình của lượt Luna kiểm lại đều nhầm câu cùng số ở phần khác. Contact sheet cho thấy crop/structure ban đầu khớp nguồn; parent đã quyết định khôi phục theo địa chỉ phần III tương ứng. Không được tự áp dụng đổi filename từ model khi model chưa được xem nội dung các crop.
- Một nguồn trường đã bị chọn vì header có Sở là cơ quan quản lý trên tên trường. Đã dừng và giữ ngoài mẫu Sở; không đổi trường thành Sở chỉ để đủ số lượng.
- Auto-review từng chặn một checkpoint vì dùng nhầm ràng buộc cấm commit của thí nghiệm trước. Đã đọc lại brief hiện tại: dòng một yêu cầu commit, dòng mười hai/mười tám chỉ định corpus/nhánh, dòng mười chín chỉ cấm product. Checkpoint e221702 được duyệt sau khi đối chiếu phạm vi; không bypass, không push/merge.

## Kiểm tra lại theo yêu cầu chủ app

- Đối chiếu đủ bảy nhánh Antigravity: đều là tổ tiên mốc 8848ac5; 83 de.md cũ không đổi, thêm 51 de.md. Hash source.json và ba câu đầu không có trùng chính xác; không suy diễn thành kiểm gần trùng đầy đủ. Không chạy OCR thêm.
- Phát hiện và sửa cả sáu crop Toán 2025 sai/thiếu vùng từ ảnh gốc; đã mở contact sheet sau sửa. Giữ file trước sửa.
- Chốt profile-inputs.json trước model judgement, Toán tối đa hai mươi tỉnh, khóa còn QA không được đưa vào phán đoán nhiễu. EXTRACT dùng trang ảnh gốc khi capture còn sẵn vì filename/crop tồn tại chưa chứng minh đúng vùng.
- 38 focused checks đạt. Bắt đầu EXTRACT Sinh học bằng Sol subscription; chưa công bố profile khi mới có request.

- Tiến độ tiếp theo: ba extraction Sinh học hoàn tất, 120 slot, chưa aggregate. Hàng đợi profile_queue.py đợi PID hiện tại rồi chạy tuần tự các môn; có khóa chống trùng và checkpoint mỗi 25 phút/mỗi môn. Các môn dưới năm đề đã có NOTE, không gọi model. Công cụ progress không coi profile thiếu một lớp aggregate là hoàn chỉnh.
- Lượt Sinh chính thức đầu tiên chỉ có bản chép/mô tả hình, nên nhận định liên quan hình còn giới hạn. Các lượt mới có thể tái dùng ảnh trang chính thức đã tồn tại trong corpus; không OCR lại. Giữ nguyên receipt giới hạn của extraction đã xong, không gắn nhãn nó đã được xem ảnh.

## Tiếp tục 03/11/2026

- Queue đã hoàn tất aggregate Sinh/Sử và trích mười hai đề Toán rồi dừng đúng prerequisite quota hai lần. Probe vô hại mới returncode=0; lưu lịch sử và mở lại bằng chứng mới, không nhầm stop cũ với lỗi mới.
- Kiểm đủ ý phát hiện ba đoạn bỏ sót ở ranh giới trang: Sinh ba ý, Sử hai ý, Hóa bốn ý và phần dẫn. Luna đọc đúng đoạn, parent mở ảnh xác nhận; bổ sung có giữ trước/sau. Không OCR lại toàn bộ đề.
- Parser bỏ sót (a), và heading tiếp trang cùng phần từng cắt mất ý. Đã sửa; địa chỉ địa phương giữ số in riêng. EXTRACT cache được tái dùng, chỉ trích bù địa chỉ thiếu.
- Sửa scanner kiểm narrative theo từng leaf, bỏ year/refs metadata, kiểm cả *_refs. Các cụm thuật ngữ chung đã được diễn đạt lại, giữ raw model receipts và bản trước sửa trong audit.
- Queue đã nối, Sinh trích bù thành công và hiện có 240 rows; đang cập nhật aggregate. Audit/prototype các stage sau chưa được báo hoàn thành.

- Checkpoint tiếp: quét shape toàn bộ đầu vào đã chốt không còn thiếu ý. Sinh đủ 240 rows, aggregate mới đang hợp nhất; compact cũ Sinh/Sử lưu archive để không bị hiểu là bản nghiệm thu. Bộ focused checks có 84 check, 82 đạt; hai cờ coverage còn mở là Sử đang chờ hai ý và Toán đang chờ chuẩn hóa địa chỉ/trích bù. Không báo suite xanh khi dữ liệu vẫn đang chạy.
