# HH-F-d0302a9ae7b7 — T14

Phần P3; dạng short_answer. Mẫu synthetic, không thuộc corpus nguồn. Trạng thái: agent_reviewed_usable_with_stated_assumptions; chưa giáo viên duyệt.

## Đề bài

Có ba bình kín A, B, C, mỗi bình chứa đúng một trong ba dung dịch không màu NaCl, Na2CO3, Na2SO4, cùng nồng độ mol, không trùng nhau. Chỉ được nhỏ HCl loãng vào một mẫu riêng của đúng một bình; phép thử phân biệt duy nhất là có/không sủi CO2. Sau đó được thử BaCl2 trên một mẫu mới của đúng một bình (không có HCl từ phép đầu); hiện tượng duy nhất là có/không kết tủa. Biết carbonate và sulfate đều kết tủa với Ba2+, chloride không; HCl chỉ làm carbonate sủi khí. Được chọn bình thử thứ hai tùy kết quả thứ nhất. Trong trường hợp xấu nhất, cần ít nhất bao nhiêu phép thử bổ sung cùng hai thuốc thử trên để xác định chắc chắn cả ba nhãn, sau khi đã thực hiện hai phép như quy định? Ghi số nguyên.

## Khóa, lời giải và mức nhận thức

- Đáp án: **1**; mức **VD**. Một phép thử HCl có nhánh không sủi gồm 4 hoán vị. Ở nhánh đó, phép BaCl2 tốt nhất chỉ tách thành nhóm 1 và 3 hoặc 2 và 2; không thể xác định tất cả trong hai phép (mỗi phép chỉ có hai kết quả, tổng 6 hoán vị >4 lá). Có chiến lược ba phép: thử HCl trên A. Nếu sủi, A=carbonate; thử BaCl2 trên B phân biệt B,C nên không cần thêm. Nếu A không sủi, thử BaCl2 trên A: không kết tủa thì A=chloride; có thì A=sulfate. Khi đó thử HCl trên B phân biệt carbonate với chất còn lại. Do đó xấu nhất cần đúng 1 phép bổ sung.

Một phép thử HCl có nhánh không sủi gồm 4 hoán vị. Ở nhánh đó, phép BaCl2 tốt nhất chỉ tách thành nhóm 1 và 3 hoặc 2 và 2; không thể xác định tất cả trong hai phép (mỗi phép chỉ có hai kết quả, tổng 6 hoán vị >4 lá). Có chiến lược ba phép: thử HCl trên A. Nếu sủi, A=carbonate; thử BaCl2 trên B phân biệt B,C nên không cần thêm. Nếu A không sủi, thử BaCl2 trên A: không kết tủa thì A=chloride; có thì A=sulfate. Khi đó thử HCl trên B phân biệt carbonate với chất còn lại. Do đó xấu nhất cần đúng 1 phép bổ sung.

**Căn cứ nhận thức:** VD: xây cây quyết định thích nghi, kết hợp tính chọn lọc hóa học với chứng minh giới hạn thông tin; không chỉ nhận ra một kết tủa quen thuộc.

## Nhiễu và cách làm tương đương


Chấp nhận lập luận hóa học tương đương, bảo toàn và đổi đơn vị nhất quán; kết quả phải thỏa toàn bộ điều kiện đề.

## Tiêu chí chấm và biến thể

- 1 điểm minh họa: Một phép thử HCl có nhánh không sủi gồm 4 hoán vị. Ở nhánh đó, phép BaCl2 tốt nhất chỉ tách thành nhóm 1 và 3 hoặc 2 và 2; không thể xác định tất cả trong hai phép (mỗi phép chỉ có hai kết quả, tổng 6 hoán vị >4 lá). Có chiến lược ba phép: thử HCl trên A. Nếu sủi, A=carbonate; thử BaCl2 trên B phân biệt B,C nên không cần thêm. Nếu A không sủi, thử BaCl2 trên A: không kết tủa thì A=chloride; có thì A=sulfate. Khi đó thử HCl trên B phân biệt carbonate với chất còn lại. Do đó xấu nhất cần đúng 1 phép bổ sung.

Tiêu chí là minh họa nghiên cứu, không thay biểu điểm của đề đích. Với TF, không mặc định chia đều điểm từng ý. Xem [CRITERIA](../CRITERIA.md).

- Dễ hơn: Cho A đã biết là carbonate, hỏi cách phân biệt B và C.
- Khó hơn: Cho phép hỗn hợp hai muối trong mỗi bình và xét liệu cùng thuốc thử có còn xác định duy nhất không.

## Giải lại và trạng thái

**agent_reviewed_usable_with_stated_assumptions**. Hồ sơ không gọi lượt kiểm tra là teacher-approved.

Phải thiết kế cây thử: thử HCl trên A; nếu dương, Ba trên B phân biệt hai nhãn còn. Nếu âm, thử Ba trên chính A: xác định A là chloride hay sulfate, rồi một thử thích hợp trên B phân biệt hai nhãn còn. Hai thử nhị phân không đủ phân biệt 6 hoán vị nên cần ít nhất một thử bổ sung trong trường hợp xấu nhất.

Chi tiết: [ngân hàng hiện hành](../data/samples-current.json).
