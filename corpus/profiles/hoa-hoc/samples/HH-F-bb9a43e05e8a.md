# HH-F-bb9a43e05e8a — T04

Phần P3; dạng short_answer. Mẫu synthetic, không thuộc corpus nguồn. Trạng thái: agent_reviewed_usable_with_stated_assumptions; chưa giáo viên duyệt.

## Đề bài

Một mô hình trùng ngưng mạch thẳng chỉ tạo liên kết amide, không tạo vòng và không có phản ứng phụ. Cấp 0,120 mol H2N–R–NH2, 0,100 mol HOOC–R′–COOH và 0,0300 mol CH3COOH (chất chặn đầu mạch một chức). Tất cả nhóm –COOH phản ứng hết, –NH2 được phép dư. Mỗi liên kết amide hình thành giữa hai phân tử đang tách rời và làm mất một H2O. Mỗi phân tử hữu cơ cuối là một mạch thẳng có hai đầu; đầu mạch chỉ có thể là –NH2 tự do hoặc đầu acetyl từ CH3COOH. Monomer còn dư cũng được tính là một phân tử mạch thẳng. Không áp đặt chiều dài tối thiểu; các cách phân bố liên kết phù hợp bảo toàn đều được phép. Số mol phân tử có CẢ HAI đầu là acetyl ít nhất bằng bao nhiêu? Ghi mol, 3 chữ số thập phân.

## Khóa, lời giải và mức nhận thức

- Đáp án: **0.01**; mức **VD**. Số mol liên kết amide là 2×0,100+0,030=0,230; số mol phân tử ban đầu 0,120+0,100+0,030=0,250. Không vòng nên còn B=0,020 mol mạch. NH2 còn 2×0,120−0,230=0,010 mol, còn đầu acetyl là 0,030 mol. Đặt d là mol mạch hai đầu acetyl. Các mạch khác mang tối đa một đầu acetyl nên 0,030≤2d+(0,020−d), suy ra d≥0,010. Cận đạt được bằng 0,010 mol mạch hai acetyl và 0,010 mol mạch một acetyl–một NH2; có thể phân bổ đủ 0,100 mol diacid vào các mạch này và không tạo vòng. Đáp số 0,010 mol.

Số mol liên kết amide là 2×0,100+0,030=0,230; số mol phân tử ban đầu 0,120+0,100+0,030=0,250. Không vòng nên còn B=0,020 mol mạch. NH2 còn 2×0,120−0,230=0,010 mol, còn đầu acetyl là 0,030 mol. Đặt d là mol mạch hai đầu acetyl. Các mạch khác mang tối đa một đầu acetyl nên 0,030≤2d+(0,020−d), suy ra d≥0,010. Cận đạt được bằng 0,010 mol mạch hai acetyl và 0,010 mol mạch một acetyl–một NH2; có thể phân bổ đủ 0,100 mol diacid vào các mạch này và không tạo vòng. Đáp số 0,010 mol.

**Căn cứ nhận thức:** VD: suy số thành phần mạch từ biến đổi liên kết, bảo toàn hai loại đầu mạch, dựng cận đếm đầu cho mạch hai acetyl và chứng minh cận có thể đạt; không chỉ tính số mol nước.

## Nhiễu và cách làm tương đương


Chấp nhận lập luận hóa học tương đương, bảo toàn và đổi đơn vị nhất quán; kết quả phải thỏa toàn bộ điều kiện đề.

## Tiêu chí chấm và biến thể

- 0.4 điểm minh họa: Tính đúng 0,020 mol mạch và 0,030 mol đầu acetyl, 0,010 mol NH2.
- 0.3 điểm minh họa: Lập cận d≥0,010 bằng số đầu mạch, không mặc định phân bố ngẫu nhiên.
- 0.3 điểm minh họa: Chỉ ra phân bố mạch đạt cận và ghi 0,010 mol.

Tiêu chí là minh họa nghiên cứu, không thay biểu điểm của đề đích. Với TF, không mặc định chia đều điểm từng ý. Xem [CRITERIA](../CRITERIA.md).

- Dễ hơn: Chỉ hỏi số mol nhóm NH2 còn sau trùng ngưng.
- Khó hơn: Cho giới hạn chiều dài mạch khác nhau và kiểm tra cận còn đạt được không.

## Giải lại và trạng thái

**agent_reviewed_usable_with_stated_assumptions**. Hồ sơ không gọi lượt kiểm tra là teacher-approved.

Phải bảo toàn số mạch và hai loại đầu: 0,250−0,230=0,020 mol mạch; có 0,030 acetyl và 0,010 NH2. Tối đa 0,010 mạch một đầu acetyl, còn ít nhất 0,010 mạch hai đầu acetyl; phân bố này khả thi.

Chi tiết: [ngân hàng hiện hành](../data/samples-current.json).
