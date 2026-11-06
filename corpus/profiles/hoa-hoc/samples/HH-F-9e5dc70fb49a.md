# HH-F-9e5dc70fb49a — T18

Phần P2; dạng true_false. Mẫu synthetic, không thuộc corpus nguồn. Trạng thái: agent_reviewed_usable_with_stated_assumptions; chưa giáo viên duyệt.

## Đề bài

Có ba lọ A, B, C chứa ethanol, ethanal và propanone, mỗi chất đúng một lọ, nhãn bị mất. Mỗi phép thử dùng mẫu mới và cho một kết quả có/không. Có ba phép thử: S (tráng bạc) chỉ dương tính với ethanal; R (cho tiếp xúc sodium trong điều kiện khan, xét có/không khí H2) chỉ dương tính với ethanol; I (iodoform) dương tính với cả ba. Các kết quả theo đúng bảng chọn lọc đã cho, không có sai số. Được chọn phép thử và lọ tiếp theo tùy kết quả trước. Mỗi phép S tốn 1 đơn vị chi phí, mỗi phép R tốn 2 đơn vị, mỗi phép I tốn 1 đơn vị; chi phí cộng dồn, không có chi phí khác. Có thể chọn phép thử và lọ tiếp theo theo các kết quả trước. Khi nói thiết kế lại từ đầu, ba lọ đều chưa được thử, có đủ mẫu cho mọi phép thử và không được dùng hai kết quả đã có. Mục tiêu là xác định cả ba nhãn trong mọi hoán vị có thể, tối thiểu hóa chi phí lớn nhất giữa các nhánh kết quả. Hai phép S liên tiếp đã được thực hiện trên A rồi B và đều âm tính. Xét đúng/sai.

**a** Sau hai kết quả đã có, C chắc chắn là ethanal.

**b** Phép I trên A phân biệt được A là ethanol hay propanone.

**c** Nếu thiết kế lại từ đầu với ba lọ chưa thử, chi phí thấp nhất có thể bảo đảm xác định cả ba nhãn trong trường hợp xấu nhất là 4 đơn vị.

**d** Nếu được thiết kế lại từ đầu, có chiến lược chỉ cần tối đa hai phép thử trong mọi trường hợp.

## Khóa, lời giải và mức nhận thức

- a: **D**; mức **TH**. S âm tính ở A,B loại ethanal tại cả hai; mỗi chất đúng một lần nên C=ethanal.
- b: **S**; mức **TH**. I dương tính với cả ethanol và propanone nên không tách hai khả năng.
- c: **D**; mức **VD**. Cận đạt được: thử S trên A (1 đơn vị). Nếu dương, A=ethanal, dùng R trên B (2) để phân biệt hai lọ còn lại, tổng 3. Nếu âm, thử S trên B (1); dù kết quả nào đều xác định vị trí ethanal, rồi dùng R trên một trong hai lọ còn lại (2), tổng 4. Để chứng minh không thể bảo đảm chi phí≤3: phép I không phân biệt trạng thái nên bỏ. Nếu bắt đầu bằng R (giá 2), nhánh âm còn 4 hoán vị nhưng chỉ còn ngân sách 1 cho tối đa một S, không đủ. Nếu bắt đầu bằng S (giá 1), nhánh âm còn 4 hoán vị; ngân sách 2 chỉ đủ một R (hai kết quả không đủ phân biệt 4 trạng thái), hoặc hai S (không bao giờ phân biệt hai cách đổi ethanol và propanone khi vị trí ethanal như nhau). Vậy chi phí tối ưu xấu nhất đúng 4.
- d: **S**; mức **VD**. Có 3!=6 hoán vị nhãn; mỗi phép chỉ có hai kết quả, cây sâu tối đa hai có nhiều nhất 4 lá, không thể phân biệt 6 trạng thái. Ba phép đủ: S trên A; nếu dương thì R trên B. Nếu âm thì R trên A xác định A, sau đó S trên B xác định hai lọ còn lại. Vậy tối ưu xấu nhất là 3, không phải 2.

a: S âm tính ở A,B loại ethanal tại cả hai; mỗi chất đúng một lần nên C=ethanal.
b: I dương tính với cả ethanol và propanone nên không tách hai khả năng.
c: Cận đạt được: thử S trên A (1 đơn vị). Nếu dương, A=ethanal, dùng R trên B (2) để phân biệt hai lọ còn lại, tổng 3. Nếu âm, thử S trên B (1); dù kết quả nào đều xác định vị trí ethanal, rồi dùng R trên một trong hai lọ còn lại (2), tổng 4. Để chứng minh không thể bảo đảm chi phí≤3: phép I không phân biệt trạng thái nên bỏ. Nếu bắt đầu bằng R (giá 2), nhánh âm còn 4 hoán vị nhưng chỉ còn ngân sách 1 cho tối đa một S, không đủ. Nếu bắt đầu bằng S (giá 1), nhánh âm còn 4 hoán vị; ngân sách 2 chỉ đủ một R (hai kết quả không đủ phân biệt 4 trạng thái), hoặc hai S (không bao giờ phân biệt hai cách đổi ethanol và propanone khi vị trí ethanal như nhau). Vậy chi phí tối ưu xấu nhất đúng 4.
d: Có 3!=6 hoán vị nhãn; mỗi phép chỉ có hai kết quả, cây sâu tối đa hai có nhiều nhất 4 lá, không thể phân biệt 6 trạng thái. Ba phép đủ: S trên A; nếu dương thì R trên B. Nếu âm thì R trên A xác định A, sau đó S trên B xác định hai lọ còn lại. Vậy tối ưu xấu nhất là 3, không phải 2.

**Căn cứ nhận thức:** a,b là TH. Ở c, học sinh phải dựng cây thử thích nghi theo chi phí không đều, tìm chiến lược đạt cận và bác mọi loại bước đầu dưới ngân sách thấp hơn; không thể suy đáp số chỉ từ số phép thử hay đọc một hàng bảng chọn lọc. d vẫn VD vì đánh giá tính khả thi của mọi chiến lược từ 6 hoán vị.

## Nhiễu và cách làm tương đương


Chấp nhận cây quyết định, liệt kê hoán vị hoặc phân hoạch tập trạng thái; ở c phải có cả chiến lược chi phí 4 và lập luận mọi chiến lược ngân sách 3 đều thất bại.

## Tiêu chí chấm và biến thể

- 0.25 điểm minh họa: a: S âm tính ở A,B loại ethanal tại cả hai; mỗi chất đúng một lần nên C=ethanal.
- 0.25 điểm minh họa: b: I dương tính với cả ethanol và propanone nên không tách hai khả năng.
- 0.25 điểm minh họa: c: Cận đạt được: thử S trên A (1 đơn vị). Nếu dương, A=ethanal, dùng R trên B (2) để phân biệt hai lọ còn lại, tổng 3. Nếu âm, thử S trên B (1); dù kết quả nào đều xác định vị trí ethanal, rồi dùng R trên một trong hai lọ còn lại (2), tổng 4. Để chứng minh không thể bảo đảm chi phí≤3: phép I không phân biệt trạng thái nên bỏ. Nếu bắt đầu bằng R (giá 2), nhánh âm còn 4 hoán vị nhưng chỉ còn ngân sách 1 cho tối đa một S, không đủ. Nếu bắt đầu bằng S (giá 1), nhánh âm còn 4 hoán vị; ngân sách 2 chỉ đủ một R (hai kết quả không đủ phân biệt 4 trạng thái), hoặc hai S (không bao giờ phân biệt hai cách đổi ethanol và propanone khi vị trí ethanal như nhau). Vậy chi phí tối ưu xấu nhất đúng 4.
- 0.25 điểm minh họa: d: Có 3!=6 hoán vị nhãn; mỗi phép chỉ có hai kết quả, cây sâu tối đa hai có nhiều nhất 4 lá, không thể phân biệt 6 trạng thái. Ba phép đủ: S trên A; nếu dương thì R trên B. Nếu âm thì R trên A xác định A, sau đó S trên B xác định hai lọ còn lại. Vậy tối ưu xấu nhất là 3, không phải 2.

Tiêu chí là minh họa nghiên cứu, không thay biểu điểm của đề đích. Với TF, không mặc định chia đều điểm từng ý. Xem [CRITERIA](../CRITERIA.md).

- Dễ hơn: Giữ hai kết quả S âm tính đã có, hỏi một phép R trên A xác định nhãn A,B thế nào; đây là TH.
- Khó hơn: Thay chi phí R bằng một tham số dương và tìm chiến lược có chi phí xấu nhất nhỏ nhất theo từng miền tham số.

## Giải lại và trạng thái

**agent_reviewed_usable_with_stated_assumptions**. Hồ sơ không gọi lượt kiểm tra là teacher-approved.

S âm ở A và B loại ethanal khỏi cả hai lọ, nên C là ethanal. I dương với cả ethanol và propanone nên không phân biệt hai khả năng của A. Phải tối ưu cây quyết định có chi phí: thử S trên A rồi, nếu âm, S trên B để định vị ethanal (tối đa 2 đơn vị), sau đó R trên một lọ còn lại (2 đơn vị), tổng tối đa 4. Không thể bảo đảm với 3: bắt đầu R tốn 2 có nhánh âm còn 4 hoán vị mà ngân sách 1 chỉ cho một thử nhị phân; bắt đầu S tốn 1 có nhánh âm còn 4 hoán vị, ngân sách 2 hoặc chỉ cho một R, hoặc hai S vốn không bao giờ phân biệt ethanol với propanone sau khi định vị ethanal. I không cung cấp thông tin. Phải xét mọi hoán vị: 6 nhãn gán khác nhau cần 6 lá quyết định, nhưng tối đa hai phép thử nhị phân chỉ tạo tối đa 4 lá, dù lựa chọn thích ứng.

Chi tiết: [ngân hàng hiện hành](../data/samples-current.json).
