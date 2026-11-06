# Duyệt nội dung Lịch sử — 06/11/2026

**Dùng được 73 mẫu; không loại câu đúng vì chưa đủ bằng chứng về mức.** Lượt này phân xử các điểm còn treo trên các kết quả kiểm có sẵn, không làm lại OCR hoặc giả có lượt giáo viên duyệt.

| Đối tượng | Giá trị nội dung | Bằng chứng/mục đích | Quyết định |
|---|---|---|---|
| LS-V-004, LS-V-007 | Đúng, khóa duy nhất C/D | Reviewer cũ xác nhận TH, chưa đạt VD | Phục hồi vào ngân hàng TH |
| LS-V-002 bản trước | Yêu cầu hai miền nhưng không đáp án nào trả đủ | Lỗi yêu cầu/đáp án xác định được | Sửa câu dẫn để chỉ hỏi hạn chế giảm đối thủ ở Bắc; giữ khóa B/TH |
| LS-V-001/003/005/006/008 | Nội dung và khóa dùng được | Nhãn VD có đường tắt TH trong chính phiếu reviewer | Giữ mẫu; không dùng riêng làm bằng chứng quota VD nghiêm |
| T06/T08/T16 P1/VD | Ô đề xuất, chưa có mẫu đạt mức | Không có ô nguồn observed tương ứng | Giữ trong catalog đề xuất; không bắt buộc phủ mọi đề |
| Một hàng nguồn unknown, một nguồn chưa ghép chắc mã/khóa | Chưa đủ bằng chứng, không kết luận sai | Giữ văn bản gốc và giới hạn suy luận | Không xóa hoặc coi khóa tham khảo là khóa xác nhận |

## Sửa thực chất

LS-V-002 đã bỏ tiêu chí đồng thời xử lí hai miền mà B không đáp ứng. Tác vụ mới hỏi đúng cơ chế giảm số đối thủ trực tiếp ở miền Bắc: quân Trung Hoa Dân quốc không rút thì tạm hòa với Pháp không tự loại bớt lực lượng ấy. A chuyển sang hiệu quả với chống đối/ngừng chiến Nam; C chuyển công nhận của Pháp thành sức ép lên chủ thể khác; D thay mục tiêu bằng tiếp tục chiến sự Nam. Không phương án nào ngoài B nêu đúng hạn chế được hỏi. Đây là TH, không cần nâng thành VD.

Rubric JSON của bốn mẫu TF trước có `points_each=0.25`, mâu thuẫn với chấm theo số ý đúng của cả câu. Đã bỏ giá trị cộng điểm từng ý trong dữ liệu dùng hiện hành, ghi rõ đây là đối chiếu đáp án để giải thích; điểm bài thi lấy từ đề/format. Mọi rubric TF trong ngân hàng hiện hành dùng cùng cách diễn giải.

## Độ phủ phải đọc theo hai trục

- Theo nhãn kế thừa: 64/67 ô có mẫu, 3 ô VD đề xuất chưa có.
- Theo bằng chứng mức không điều kiện: 59 ô supported, 5 conditional, 3 proposed_unfilled.
- 73/73 mẫu dùng được về nội dung. Không cộng 5 ô conditional thành VD chắc chắn và không loại 5 mẫu đúng khỏi ngân hàng.

72 mẫu có lượt giải tách từ trước (70 mẫu cũ + 2 bản nháp đúng ở TH). LS-V-002 sau sửa được phân xử trực tiếp ở lượt này; không tuyên bố đã có model blind mới. Mức nhận thức là phân tích tác vụ, chưa phải độ khó thực nghiệm.

## Đối chiếu nguồn

Đối chiếu cơ chế hòa hoãn và thay quân với [Biên niên Đảng, tập 3, mục ngày 6-3 và 9-3](https://tulieuvankien.dangcongsan.vn/van-kien-tu-lieu-ve-dang/book/lich-su-dang/lich-su-bien-nien-dang-cong-san-viet-nam-tap-3-176); định hướng đa dạng hóa, phá cấm vận và mở quan hệ với [Bộ Ngoại giao](https://mofa.gov.vn/tin-chi-tiet/chi-tiet/6-dau-moc-trong-75-nam-ngoai-giao-viet-nam-48977-251.html); mốc quân Mĩ rút năm1973 với [tư liệu Chính phủ](https://vanban.chinhphu.vn/giai-doan-1955-1975-xay-dung-cnxh-va-dau-tranh-thong-nhat-dat-nuoc/5-hoi-nghi-pari-ve-viet-nam-cuoc-dam-phan-hoa-binh-gay-go-nhat-the-ky-xx-10001595). Các giả định phản thực tế vẫn ghi tự biên soạn, không gán cho nguồn. Không dùng ngày Hiệp ước Hoa–Pháp trên trang biên niên làm chứng cứ vì cách ghi ở đó khác niên biểu thông dụng; câu sửa không đòi nhớ ngày này.

Toàn bộ quyết định, hash đầu vào, kiểm đồng bộ và biên nhận CLI ở [JSON](USABILITY-REVIEW.json). Không sửa OCR, rows, khóa nguồn, prototype đã biên dịch hoặc chính sách runtime.

## CLI thật sau chỉnh lý

```json
{"subject": "lich-su", "papers": 6, "failed": []}
{"subject": "lich-su", "items": 240, "groups": 5, "patterns": 32, "samples": 73, "problems": 0, "gaps": 0, "revision": "9ca0494260aadf49", "bytes": 568369, "out": "/tmp/usable-lich-su-pack.json"}
```

Dựng từ commit `8b66755088fbe1c48313f4dc122ff8e57d6d36b9`, tool `293398fe7abca1fd6419e80ef6eae16cb7dd7f50`; đọc lại pack có đủ3 mẫu TH phục hồi và5 statusVD có điều kiện. Chỉ mục không đổi. Tệp tạm pack đã xóa sau ghi hash và stdout. Consumer chưa được thử ở runtime về việc không dùng nhãn có điều kiện cho quota cứng.
