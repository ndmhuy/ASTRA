# V-ACT từ template người dùng

## Chạy

```powershell
.\.venv-win\Scripts\python.exe -m exam_baseline.vact.cli --request examples/vact/request.json --output runs/vact/de_01
```

Cấu hình model/key dùng `.env` hiện tại. Bốn agent có prompt/schema riêng, cùng adapter
model. Khi cần tiếp tục sau lỗi, thêm `--resume`, giữ nguyên request và mức concurrency.
Muốn giảm áp lực quota, chọn `--composer-concurrency 1 --solver-concurrency 1` từ đầu.
Đây là project V-ACT 120 câu; không dùng input THPT 22 câu cho CLI này.

## Database template bất biến

`src/exam_baseline/resources/templates/PROTO_vact_vact.tex` là bản sao nguyên byte của
file người dùng cung cấp. SHA-256:
`88929426928a869409f9a422cedf02f1ebc2ca686e4adf208dcb94e4a113147d`.
Registry kiểm hash trước khi gọi API; Git không chuẩn hóa newline của template.

Khung lấy từ file gốc: tiêu đề, thời gian 150 phút, bảng cấu trúc 120 câu, mã đề 9245,
header/footer và tiêu đề các phần giữ nguyên. Chỉ thay năm vùng nội dung TV/TA/TO/
Logic–số liệu/Suy luận khoa học, bắt đầu tại marker block đầu tiên sau tiêu đề và kết
thúc trước khoảng cách chuyển phần hoặc footer. Không thêm placeholder vào file gốc.
`font_profile=unicode_times` mặc định áp dụng hai dòng khai báo font Unicode như THPT,
dùng Times New Roman, fallback TeX Gyre Termes. Compile bằng XeLaTeX/LuaLaTeX.
`font_profile=original_t5` giữ nguyên cả khai báo T5 để dùng pdfLaTeX/VnTeX.

## Ma trận và nhóm ngữ cảnh

Theo template, và phù hợp [cấu trúc V-ACT 2026 do Trung tâm Khảo thí công bố](https://cetqa.vnuhcm.edu.vn/tin-tuc/cau-truc-de-thi-dgnl-nam-2026-nhu-the-nao-p-43.html):

| Câu | Phần | Số câu |
| --- | --- | --- |
| 1–30 | Tiếng Việt | 30 |
| 31–60 | Tiếng Anh | 30 |
| 61–90 | Toán học | 30 |
| 91–102 | Logic và phân tích số liệu | 12 |
| 103–120 | Suy luận khoa học | 18 |

Tất cả là trắc nghiệm bốn lựa chọn A/B/C/D, một đáp án đúng. Không suy ra điểm chính
thức chỉ bằng cách nhân số câu đúng với một số cố định; hệ thống này tạo đề luyện tập.
`examples/vact/request.json` có 120 slot, với topic/objective/NB–TH–VD–VDC. Phân bố
mức độ trong file là ví dụ luyện tập, cần giáo viên duyệt; không phải ma trận chính thức.

Các nhóm được đọc từ marker và số câu của chính template, không áp dụng danh sách
passage của baseline cũ: 21 nhóm dùng chung, gồm hai văn bản Việt, hai văn bản Anh,
bảy tình huống Toán và mười nhóm tư duy khoa học. Mỗi nhóm bắt buộc có passage đúng ID;
các câu được Python bind vào đúng passage theo template nếu model bỏ metadata; ID sai
tường minh bị từ chối. Không tự tạo passage còn thiếu. Bảng dữ liệu có columns/rows, kiểm số cột và render
trực tiếp bằng tabular. Không nhúng PNG/hex vào LaTeX.
Các ID tương đương có cùng phạm vi như `p73_74` được chuẩn hóa thành `g73_74`.
Schema truyền API chỉ cho chọn ID nhóm trong template; không đoán ghép passage có
tên mơ hồ `p1/p2` theo thứ tự xuất hiện. Lỗi còn lại hiển thị rõ expected/received IDs.

Tiếng Anh giữ dạng điền từ 31–35, tìm lỗi 36–40, viết lại câu 41–45 và đọc hiểu
46–52/53–60. Tìm lỗi dùng bốn đoạn đánh dấu [A]..[D] ngay trong câu để giữ đầy đủ dữ kiện.
Không gán nguồn/tác giả giả cho bài đọc mới. Dữ kiện, kiến thức và tính duy nhất của
đáp án cần Reviewer và giáo viên kiểm tra; các kiểm tra schema không chứng minh chất lượng.

## Agent, điều phối và tốc độ

Composer tạo 12 batch, mỗi batch tối đa 12 câu, không cắt đôi nhóm đọc hiểu/tình huống.
Mặc định tối đa ba batch Composer đồng thời; Solver tối đa hai batch đồng thời. Các
batch Solver nhận đủ passage/table và hình tương ứng, không nhận đáp án/lời giải của
Composer. Illustrator viết TikZ theo batch tối đa bốn hình; không gọi model nếu không có
yêu cầu hình. Thiếu hình cần thiết thì dừng xuất đề, không để câu trỏ tới hình không có.

Reviewer xem toàn bộ 120 câu, ngữ cảnh, lời giải độc lập, đáp án riêng của Composer và
LaTeX ghép hoàn chỉnh, đúng một lượt. Nếu cần sửa, Composer nhận một feedback cùng
câu/passage cũ thuộc đúng batch, rồi Illustrator/Solver chạy lại. Không gọi Reviewer
lần hai. Mọi kết quả đều `pending_human_review` và cần kiểm tra bằng mắt.

Cơ chế retry, sửa JSON/schema giới hạn, checkpoint, hash, trace thời gian/token và chi
phí dùng chung với THPT qua các hook profile. V-ACT gửi schema truyền tải rút gọn
để giảm lỗi xử lý schema ở API; schema đầy đủ vẫn nằm trong prompt và kiểm bằng
Pydantic/Python, gồm số câu/ID/passage/đáp án/hình. Schema truyền tải không thay thế
validation, và không chấp nhận đề sai cấu trúc chỉ vì API đã trả JSON.
Kiểm tra định dạng áp dụng cả bài đọc, dữ kiện dùng chung và ô bảng: công thức/lệnh
LaTeX để ngoài `$...$`, số mũ/chỉ số thô và escape JSON bị hỏng bị từ chối để model sửa.
Không tự đoán biến đổi một công thức text thành công thức toán. Chỗ trống `___` hoặc
`\underline{\hspace{2cm}}` được xuất thành chỗ trống LaTeX, không in nguyên mã.

Trong trường hợp không có hình và không
cần sửa, có 12 calls Composer + 12 Solver + 1 Reviewer; số calls tăng khi có hình,
retry/schema correction hoặc vòng sửa. V-ACT lớn hơn THPT nhiều lần; không coi mốc
thời gian/chi phí của đề THPT là cam kết cho V-ACT. Xem metrics của từng lần chạy.

## Kết quả và vị trí code

- `de_thi.tex`: đề học sinh, đủ 120 câu, không lộ answer/solution riêng.
- `dap_an_va_loi_giai.json`: câu hỏi, đáp án/lời giải Composer, passage và lời giải Solver.
- `loi_giai.md`: lời giải đọc được; dữ kiện passage đầy đủ nằm trong JSON/private artifacts.
- `_internal/`: từng batch, passage trong batch, bản candidate, trace API, checkpoint,
  review một lượt và `result.json`. Lỗi không xuất final mới.

`src/exam_baseline/vact/`: models, template registry/plan, agents, validation, renderer,
profile Orchestrator và CLI. Orchestrator kế thừa chính sách chạy chung ở
`thpt/orchestrator.py`; không sao chép một vòng điều phối hai revision khác. Có regression
cho cả hai profile. LaTeX cần compile để kiểm tra bố cục; CLI không tự compile PDF.
