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
Với GPT-6 Luna, CLI THPT dùng JSON mode nếu `EXAM_RESPONSE_FORMAT=json_object`.
Các cấu hình dùng `json_schema` gửi schema riêng từng bước tới API. Cả hai chế độ
đều kiểm tra số câu, đáp án A/B/C/D, bốn ý đúng/sai và đáp án số P3 bằng Pydantic.

### Thời gian và chi phí

Composer mặc định tạo P1, P2 rồi P3 tuần tự. Nếu quota cho phép, dùng
`--composer-concurrency 2` hoặc `3` để chạy song song. Illustrator, Solver và Reviewer
chạy theo thứ tự vì phụ thuộc dữ liệu. Với lỗi tạm thời, lần thử lại tôn trọng
`Retry-After` nếu API gửi header hợp lệ.

RAG chuyển cho Composer nội dung rút gọn theo câu, gồm bài học, mẫu cấu trúc,
lỗi sai điển hình và cảnh báo. Nếu thiếu mẫu cấu trúc, Composer nhận các quan sát
đã trừu tượng hóa và gợi ý biến thể khi có. Dữ liệu RAG đầy đủ vẫn được giữ trong
truy vết của luồng web để đối chiếu nguồn.
Vòng sửa chỉ gửi câu cũ thuộc phần hiện tại cho Composer; Reviewer vẫn thấy toàn đề.

`_internal/result.json` có `elapsed_seconds` (tổng các lượt chạy, bao gồm resume nhưng
không bao gồm thời gian dừng giữa các lượt), `invocation_elapsed_seconds` (lượt hiện tại)
và `metrics` gồm token, số lời gọi, thời gian API theo stage, chi phí USD ước tính.
`api_seconds_sum` là tổng thời gian request, có thể lớn hơn elapsed khi chạy đồng thời.
Phí ước tính theo Standard pricing và token API trả về; không phải hóa đơn. Model chưa có
giá hoặc usage bị thiếu được đánh dấu `estimate_complete=false`. Tier tài khoản không
được suy đoán. Free tier không thu phí token cho usage đủ điều kiện trong hạn mức.

Mốc đo trước tối ưu: đề `test_20261107_080102` có 6 calls, 36,009 giây API,
30.499 input + 11.288 output tokens. Theo giá Gemini 3.1 Flash-Lite xác minh ngày
2026-11-07 ($0,25/M input; $1,50/M output), tương đương $0,02455675/đề khi trả phí.
[Bảng giá Google](https://ai.google.dev/gemini-api/docs/pricing).
Chỉ xét các latency đã đo và bỏ qua retry, song song ba phần Composer có đường đi
dự kiến khoảng 22,6 giây; đây là ước tính, chưa phải benchmark p50/p95.
Lần thử `perf_parallel` đã hoàn thành nhưng có lỗi schema và một vòng sửa nội dung:
14 calls, 65.808 input + 28.251 output tokens, giá quy đổi $0,0588285. Tổng hai lượt
chạy khoảng 61,616 giây (17,548 giây trước khi ngắt + 44,068 giây resume). Không so
trực tiếp với ca 36 giây/6 calls để kết luận mức tăng tốc: nội dung, số vòng sửa và
độ trễ API khác nhau. Muốn benchmark ổn định cần nhiều đề, so p50/p95 cùng cấu hình.

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
