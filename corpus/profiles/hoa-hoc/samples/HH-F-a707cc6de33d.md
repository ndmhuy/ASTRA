# HH-F-a707cc6de33d — T09

Phần P3; dạng short_answer. Mẫu synthetic, không thuộc corpus nguồn. Trạng thái: agent_reviewed_usable_with_stated_assumptions; chưa giáo viên duyệt.

## Đề bài

Một cơ sở có 12 mẻ nước cứng độc lập. Mỗi mẻ chứa 0,010 mol Ca2+ và 0,010 mol Mg2+, không có bicarbonate. Hai cách xử lí hoàn toàn: C dùng 0,020 mol Na2CO3; L dùng 0,010 mol Ca(OH)2 để loại Mg2+ thành Mg(OH)2, sau đó dùng 0,020 mol Na2CO3 để loại toàn bộ Ca2+ (kể cả calcium mới đưa vào). Chỉ dùng hai cách này, mỗi mẻ phải xử lí nguyên mẻ. Kho có 0,180 mol Na2CO3 và 0,050 mol Ca(OH)2. Nhà cung cấp đề nghị cách M dùng 0,020 mol NaOH để loại Mg2+ rồi 0,010 mol Na2CO3 để loại Ca2+; có sẵn 0,080 mol NaOH. Trong mô hình này mỗi bước kết tủa hoàn toàn và chọn lọc ion được nêu; bỏ qua độ tan và phản ứng phụ; các hóa chất không thay thế công đoạn khác. Tối đa bao nhiêu mẻ được xử lí hoàn toàn? Ghi số nguyên.

## Khóa, lời giải và mức nhận thức

- Đáp án: **11**; mức **VD**. C và L đều tốn 0,020 mol carbonate mỗi mẻ; L không tiết kiệm carbonate nên có thể bỏ khỏi tối ưu. M tốn 0,010 mol carbonate và 0,020 mol NaOH, nên tối đa 4 mẻ M. Với m mẻ M và c mẻ C, 0,010m+0,020c≤0,180; m≤4; m+c≤12. Để xử lí 12 mẻ cần carbonate tối thiểu khi m=4: 0,040+0,160=0,200 mol, không đủ. Chọn 4M+7C dùng 0,180 mol carbonate, đạt 11 mẻ.

C và L đều tốn 0,020 mol carbonate mỗi mẻ; L không tiết kiệm carbonate nên có thể bỏ khỏi tối ưu. M tốn 0,010 mol carbonate và 0,020 mol NaOH, nên tối đa 4 mẻ M. Với m mẻ M và c mẻ C, 0,010m+0,020c≤0,180; m≤4; m+c≤12. Để xử lí 12 mẻ cần carbonate tối thiểu khi m=4: 0,040+0,160=0,200 mol, không đủ. Chọn 4M+7C dùng 0,180 mol carbonate, đạt 11 mẻ.

**Căn cứ nhận thức:** VD: phải theo dõi calcium do thuốc thử đưa thêm, loại tuyến bị trội và dùng hai nguồn lực độc lập chứng minh cận 11; thao tác đơn thuần nồng độ không giải quyết lựa chọn.

## Nhiễu và cách làm tương đương


Chấp nhận lập luận hóa học tương đương, bảo toàn và đổi đơn vị nhất quán; kết quả phải thỏa toàn bộ điều kiện đề.

## Tiêu chí chấm và biến thể

- 1 điểm minh họa: C và L đều tốn 0,020 mol carbonate mỗi mẻ; L không tiết kiệm carbonate nên có thể bỏ khỏi tối ưu. M tốn 0,010 mol carbonate và 0,020 mol NaOH, nên tối đa 4 mẻ M. Với m mẻ M và c mẻ C, 0,010m+0,020c≤0,180; m≤4; m+c≤12. Để xử lí 12 mẻ cần carbonate tối thiểu khi m=4: 0,040+0,160=0,200 mol, không đủ. Chọn 4M+7C dùng 0,180 mol carbonate, đạt 11 mẻ.

Tiêu chí là minh họa nghiên cứu, không thay biểu điểm của đề đích. Với TF, không mặc định chia đều điểm từng ý. Xem [CRITERIA](../CRITERIA.md).

- Dễ hơn: Chỉ dùng C, hỏi số mẻ tối đa.
- Khó hơn: Thêm giá mỗi thuốc thử và yêu cầu chi phí tối thiểu để xử lí đủ 12 mẻ khi được mua bù.

## Giải lại và trạng thái

**agent_reviewed_usable_with_stated_assumptions**. Hồ sơ không gọi lượt kiểm tra là teacher-approved.

Phải so sánh nguồn lực: L không tiết kiệm carbonate so với C. Dùng tối đa 4 mẻ M tiết kiệm 0,040 mol carbonate; 4 M+7 C dùng 0,180 mol carbonate và 0,080 mol NaOH. 12 mẻ dù 4 M vẫn cần 0,200 mol carbonate nên bất khả thi.

Chi tiết: [ngân hàng hiện hành](../data/samples-current.json).
