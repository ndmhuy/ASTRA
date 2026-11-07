# Toán THPT với template gốc

## Chạy

```powershell
.\.venv-win\Scripts\python.exe -m exam_baseline.thpt.cli --request examples/thpt/request.json --output runs/thpt/de_01
```

Nếu bị ngắt/lỗi API, tiếp tục cùng output và cùng request bằng cách thêm `--resume`.
Bước đã có checkpoint hợp lệ được dùng lại, bao gồm kết quả Reviewer; chỉ gọi model
cho phần còn thiếu. Input thay đổi bị từ chối. Các lần chạy trước khi có tính năng
checkpoint không thể khôi phục tự động các bước cũ.

Dùng `EXAM_PROVIDER=chat_completions`, model/key/endpoint trong `.env` hiện có.
Không ghi cứng tên model hay quota từ file Composer tham khảo. Cả bốn vai trò dùng
cấu hình này qua CLI; Python cho phép truyền provider riêng từng vai trò vào Orchestrator.
CLI THPT dùng `response_format=json_schema` và gửi schema riêng của từng bước tới API.
Provider cần hỗ trợ chế độ này. Schema P1/P2/P3 buộc số câu, đáp án A/B/C/D,
bốn ý đúng/sai và trường đáp án số P3; không chỉ mô tả các yêu cầu này trong prompt.

## Template bất biến

File `src/exam_baseline/resources/templates/PROTO_thptqg_toan_v2.tex` là bản sao
nguyên byte của file người dùng cung cấp, SHA-256:
`e1af472a5363364814072625c40c98f7e6a77a00093d709568068826feacfdb7`.

Không thêm placeholder, package, font hay sửa macro trong file gốc. Registry kiểm hash
trước khi gọi model; nếu sai thì dừng. Renderer ghép bằng bytes, không chuẩn hóa newline.
Mọi byte **ngoài ba vùng nội dung câu hỏi** được giữ nguyên khi chọn
`"font_profile": "original_t5"` trong request (dành cho pdfLaTeX/VnTeX).
Mặc định là `"font_profile": "unicode_times"`: theo điều chỉnh font người dùng đã duyệt,
output thay đúng hai dòng `inputenc`/`fontenc[T5]` bằng `fontspec` và chọn Times New Roman
(fallback TeX Gyre Termes nếu môi trường không có Times New Roman). Dùng XeLaTeX/LuaLaTeX.
Các byte khung còn lại giữ nguyên; file template gốc trong resources không bị sửa.
Ba vùng bắt đầu tại `\noindent \textbf{Câu 1:}` của từng phần và kết thúc trước
`\vspace{0.5cm}` chuyển phần / `\vspace{0.6cm}` cuối đề. Câu mẫu và hình minh họa
trong ba vùng này được thay bằng câu mới; bố cục nội dung mới do renderer quản lý.
Tiêu đề phần, hướng dẫn, đầu/cuối đề, header/footer, năm 2026 và mã đề 1034 giữ nguyên.
Preamble chỉ có thay đổi font nêu trên. Không gửi khung cho Composer chỉnh sửa.

## Ma trận

Cấu trúc 12 câu chọn một trong A/B/C/D, 4 câu đúng/sai (mỗi câu bốn ý), 6 câu trả lời
ngắn, 90 phút theo template và [cấu trúc Bộ GDĐT công bố trên Cổng Chính phủ](https://xaydungchinhsach.chinhphu.vn/cau-truc-de-thi-tot-nghiep-thpt-tu-nam-2025-119240308200554932.htm).
Không đánh đồng 4 câu đúng/sai với 16 câu độc lập.

`examples/thpt/request.json` khai báo 22 slot theo thứ tự P1-1..12, P2-1..4, P3-1..6:

- `topic`: nội dung/chủ đề.
- `objective`: yêu cầu kiến thức, kỹ năng cụ thể.
- `level`: NB, TH, VD hoặc VDC.
- `statement_levels`: riêng P2, mức độ cho bốn ý a/b/c/d.
- `reference_material`: tài liệu tham chiếu đã được giáo viên lựa chọn.

Ma trận mẫu là **đề xuất luyện tập**, không phải ma trận phân bố chủ đề/mức độ chính thức
của Bộ. Người dùng cần duyệt nó theo năm thi và chương trình. Code kiểm cấu trúc/ID/số
lượng; Reviewer kiểm sự phù hợp nội dung và mức độ. Việc đánh giá mức độ nhận thức của
một bài toán vẫn cần giáo viên, không thể chứng minh bằng nhãn model tự gán.

## Luồng và output

Composer tạo từng phần theo ma trận → Illustrator viết TikZ → ghép template → Solver
giải độc lập → Reviewer kiểm một lần. Nếu cần sửa: Composer tạo lại ba phần theo feedback
→ Illustrator → Solver → chuyển người dùng kiểm tra; không gọi Reviewer lần hai.
Luồng thường có 6 lượt gọi, luồng sửa có 11 lượt. Composer/Illustrator/Solver được sửa
JSON/schema tối đa một lần cho mỗi bước; Reviewer không gọi lại kể cả lỗi schema.
Chỉ bóc Markdown fence khi bên trong là JSON object hợp lệ, không đoán/sửa dữ liệu toán.
Nếu vẫn lỗi thì dừng và không xuất final. Lỗi HTTP 429/500/502/503/504, timeout hoặc
mất kết nối được retry tối đa một lần, đợi một giây. Reviewer không retry để giữ
giới hạn một lượt gọi. Không tự đổi model ngầm.
`_internal/responses/` lưu raw response; `result.json` ghi stage/part, mọi lần gọi
(kể cả thất bại), lỗi contract và đường dẫn phản hồi để chẩn đoán.

- `de_thi.tex`: đề học sinh, không chứa đáp án/lời giải của Composer.
- `loi_giai.md`: đáp án và lời giải chi tiết của Composer, kèm lời giải độc lập của Solver.
- `dap_an_va_loi_giai.json`: bản có cấu trúc phục vụ tích hợp.
- `KIEM_TRA.txt`: yêu cầu người dùng kiểm tra.
- `_internal/`: request, từng revision, candidate LaTeX, review và kết quả chạy.

Mọi kết quả đều `pending_human_review`; chưa tự động compile. Mở `de_thi.tex` trong
trình LaTeX với các package của template gốc để biên dịch và kiểm tra hình/bố cục.
Không tự thay package khác ngoài font profile đã khai báo. File lời giải không phải đề đã duyệt.

## Vị trí code và nguồn tham khảo

`src/exam_baseline/thpt/`: `models.py` quản lý ma trận/contracts; `agents.py` chứa bốn
vai trò; `template.py` giữ registry/hash/vùng nội dung; `rendering.py` dựng nội dung;
`orchestrator.py` quản lý luồng và artifacts; `cli.py` là entry point.

Thiết kế Composer dựa trên file `composer.py` người dùng cung cấp: tạo theo phần,
shape requirement riêng từng dạng câu, ma trận theo phần, tham chiếu để hiệu chỉnh
độ khó và tách câu hỏi khỏi đáp án. Không import nguyên file vì phụ thuộc `BaseAgent`,
`exam_formats`, `prompt_strategy`, `prompt_text_gate` và prompt bên ngoài chưa được cung cấp.
Không dùng thuật toán đảo đáp án tham chiếu của file đó vì cần giữ đáp án/lời giải nhất quán.

Luồng THPT dùng contracts riêng cho bốn ý đúng/sai và bốn mức nhận thức, tránh ép vào
schema baseline cũ chỉ có ba độ khó và đúng/sai đơn. CLI baseline/pipeline tổng quát vẫn
là các luồng khác; để tạo đề theo template này dùng `exam_baseline.thpt.cli`.
