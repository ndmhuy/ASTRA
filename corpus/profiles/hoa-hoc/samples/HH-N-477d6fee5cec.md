# HH-N-477d6fee5cec — T04

Phần P2; dạng true_false. Mẫu synthetic, không thuộc corpus nguồn. Trạng thái: agent_reviewed_usable_with_stated_assumptions; chưa giáo viên duyệt.

## Đề bài

Mô hình và số liệu tự biên soạn, dùng để khảo sát liên kết ngang của polymer; đây là mô hình lí tưởng, không mô tả đầy đủ cơ chế lưu hóa thực tế.

Ban đầu có 68,00 g polyisoprene tinh khiết, với mắt xích –CH2–C(CH3)=CH–CH2–. Khi đưa sulfur vào, chỉ hình thành hai loại cầu nối:

| Loại cầu nối | Cấu trúc liên kết | Sulfur được giữ lại trên mỗi cầu nối | Hydrogen bị tách trên mỗi cầu nối |
|---|---|---:|---:|
| Monosulfide | C–S–C | 1 nguyên tử S | 2 nguyên tử H |
| Disulfide | C–S–S–C | 2 nguyên tử S | 2 nguyên tử H |

Hai carbon ở hai đầu cầu nối có thể thuộc cùng một mạch hoặc hai mạch khác nhau. Mỗi cầu nối hình thành giải phóng đúng một phân tử H2. Không có phản ứng phụ, không có sulfur tự do còn lại và không mất nguyên tử carbon. Khối lượng H2 thu được là 0,0800 g; khối lượng vật liệu sau phản ứng là 69,84 g. Cho C = 12, H = 1, S = 32.

Trong mô hình cơ học, chỉ các cầu nối nối hai mạch khác nhau mới có tác dụng; gọi chúng là cầu nối liên mạch. Đại lượng cơ học E tỉ lệ thuận với số mol cầu nối liên mạch. Một phép xử lí chọn lọc làm mất hoàn toàn tác dụng của mọi cầu nối disulfide, không làm thay đổi cầu nối monosulfide và không gây thay đổi nào khác. Sau xử lí, E còn 40,0% giá trị ban đầu. Giả sử mọi cầu nối liên mạch có cùng đóng góp vào E.

Xác định mỗi phát biểu sau đúng hay sai.

**a** Mắt xích của polyisoprene đã cho có công thức phân tử C5H8.

**b** Tổng lượng cầu nối monosulfide và disulfide hình thành là 0,0800 mol.

**c** Trước phép xử lí chọn lọc, số mol cầu nối monosulfide bằng số mol cầu nối disulfide.

**d** Trước phép xử lí chọn lọc, tỉ số giữa số mol mắt xích và số mol cầu nối liên mạch không thể nhỏ hơn 30; giá trị 30 phù hợp với tất cả dữ kiện.

## Khóa, lời giải và mức nhận thức

- a: **D**; mức **TH**. Đếm nguyên tử trong mắt xích –CH2–C(CH3)=CH–CH2– được 5 carbon và 8 hydrogen, tức C5H8.
- b: **S**; mức **TH**. n(H2) = 0,0800/2 = 0,0400 mol. Mỗi cầu nối giải phóng một H2 nên tổng số mol cầu nối là 0,0400 mol, không phải 0,0800 mol.
- c: **D**; mức **TH**. Khối lượng sulfur giữ lại là 69,84 − 68,00 + 0,0800 = 1,920 g, tương ứng 0,0600 mol nguyên tử S. Gọi x, y lần lượt là số mol cầu nối monosulfide và disulfide: x + y = 0,0400 và x + 2y = 0,0600. Suy ra x = y = 0,0200 mol.
- d: **D**; mức **VD**. Có 68,00/68 = 1,000 mol mắt xích. Gọi B là số mol cầu nối liên mạch ban đầu. E giảm 60% nên cầu nối disulfide liên mạch chiếm 0,60B; lượng này không vượt tổng disulfide 0,0200 mol. Do đó B ≤ 1/30 mol và 1,000/B ≥ 30. Dấu bằng đạt được khi toàn bộ 0,0200 mol disulfide là liên mạch; monosulfide liên mạch bằng 0,40/30 = 0,01333… mol, nhỏ hơn tổng monosulfide 0,0200 mol. Phần monosulfide còn lại nối các vị trí trên cùng một mạch, nên phương án này khả thi trong mô hình.

Mắt xích C5H8 có khối lượng mol 68 g/mol, nên mẫu ban đầu chứa 1,000 mol mắt xích. Số mol H2 là 0,0400, bằng tổng số mol cầu nối. Bảo toàn khối lượng, có tính phần hydrogen đã thoát ra, cho khối lượng sulfur giữ lại bằng 1,920 g, tức 0,0600 mol nguyên tử S. Từ x + y = 0,0400 và x + 2y = 0,0600 suy ra mỗi loại cầu nối có 0,0200 mol.

Không được đồng nhất tổng số cầu nối hóa học với số cầu nối liên mạch có tác dụng cơ học. Gọi u, v lần lượt là số mol monosulfide và disulfide liên mạch. Phép xử lí để lại E bằng 40% ban đầu nên u/(u + v) = 0,40, tức v = 1,5u. Đồng thời 0 ≤ u ≤ 0,0200 và 0 ≤ v ≤ 0,0200. Giới hạn v quyết định giá trị lớn nhất của u + v: khi v = 0,0200 thì u = 0,01333… và u + v = 1/30 mol. Vì vậy số mol mắt xích trên một mol cầu nối liên mạch ít nhất bằng 30. Phần monosulfide không liên mạch vẫn phù hợp với dữ kiện hóa học. Kết luận: a đúng, b sai, c đúng, d đúng.

**Căn cứ nhận thức:** Mức hiện hành theo thao tác tối thiểu của lượt giải lại: a: Đếm mắt xích có 5 C và 8 H.; b: n(H2)=0,0800/2=0,0400 mol, bằng tổng cầu nối.; c: S giữ lại 69,84−68+0,08=1,92 g=0,060 mol; x+y=0,040, x+2y=0,060 cho x=y=0,020.; d: Phải tách cầu nội/liên mạch: đặt t liên mạch, mono=0,4t, di=0,6t≤0,020 nên t≤1/30; 1 mol mắt xích/t≥30. Tại t=1/30, mono liên=0,01333≤0,020 nên khả thi.

## Nhiễu và cách làm tương đương


Đối với d, có thể dùng B và các tỉ phần 0,40B, 0,60B hoặc hai biến u, v. Chấp nhận mô hình bất đẳng thức, biểu diễn miền khả thi hoặc lập luận bằng giới hạn số cầu nối disulfide, miễn có kiểm tra khả năng đạt cận. Rubric chấm độc lập từng phát biểu; lời giải dùng để thẩm định cơ sở suy luận.

## Tiêu chí chấm và biến thể

- 0.25 điểm minh họa: Chọn đúng a: D.
- 0.25 điểm minh họa: Chọn đúng b: S.
- 0.25 điểm minh họa: Chọn đúng c: D.
- 0.25 điểm minh họa: Chọn đúng d: D.

Tiêu chí là minh họa nghiên cứu, không thay biểu điểm của đề đích. Với TF, không mặc định chia đều điểm từng ý. Xem [CRITERIA](../CRITERIA.md).

- Dễ hơn: Bỏ dữ kiện cơ học và thay d bằng phát biểu: 'Trung bình có 25 mắt xích ứng với một cầu nối hóa học, tính chung cả hai loại.' Khi đó d chỉ cần dùng tổng số mol cầu nối, ở mức TH.
- Khó hơn: Thay phép xử lí bằng quá trình chỉ làm mất tác dụng của 80% cầu nối disulfide liên mạch và 10% cầu nối monosulfide liên mạch; cho E còn 48% ban đầu. Yêu cầu tìm khoảng khả dĩ của số mol cầu nối liên mạch và chứng minh cận trên đạt được bằng một cách phân bố cụ thể.

## Giải lại và trạng thái

**agent_reviewed_usable_with_stated_assumptions**. Hồ sơ không gọi lượt kiểm tra là teacher-approved.

Đếm mắt xích có 5 C và 8 H. n(H2)=0,0800/2=0,0400 mol, bằng tổng cầu nối. S giữ lại 69,84−68+0,08=1,92 g=0,060 mol; x+y=0,040, x+2y=0,060 cho x=y=0,020. Phải tách cầu nội/liên mạch: đặt t liên mạch, mono=0,4t, di=0,6t≤0,020 nên t≤1/30; 1 mol mắt xích/t≥30. Tại t=1/30, mono liên=0,01333≤0,020 nên khả thi.

Chi tiết: [ngân hàng hiện hành](../data/samples-current.json).
