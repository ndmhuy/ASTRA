# Trạng thái tiếp tục — 03/11/2026

Đây là tiến độ đang làm, chưa phải nghiệm thu cuối. Chủ sở hữu đã chỉ ra bản tóm tắt chưa đủ nội dung; tiêu chí đầy đủ được ghi tại `profiles/DOSSIER-SPEC.md`. Trạng thái đạt kiểm kỹ thuật chỉ áp dụng lớp trích xuất, không phải hồ sơ ra đề hoàn chỉnh. [Danh sách hồ sơ](../profiles/README.md) được cập nhật tự động; trạng thái chi tiết ở `audit/outputs/profile-publication.json` và `profile-queue.json`.

- Ưu tiên chủ sở hữu: hoàn tất hồ sơ các môn có ít nhất năm đề thật dùng được. Sinh và Sử đã có aggregate tách chính thức/tỉnh, mỗi môn sáu đề và 240 câu/ý; kiểm kỹ thuật hiện không có cờ chặn, nhận định vẫn chờ giáo viên.
- Toán đã hoàn tất profile 22 đề (hai chính thức, hai mươi tỉnh), 748 câu/ý; đủ cả aggregate và cấu trúc. Mười trên hai mươi đề tỉnh có khóa khớp; các lựa chọn chưa biết đúng/sai không được tính vào tỷ lệ nhiễu đã phán đoán. Hóa đang trích từng đề. Không trích hoặc OCR lại phần đã có.
- Kế tiếp: Hóa tám đề, Địa bảy, Vật lí tám, Tin sáu, GDKTPL mười bốn, Anh mười sáu, Văn mười một. Mỗi môn xong sẽ có hồ sơ đọc nhanh và cấu trúc câu chùm/thứ tự.
- Giữ 83 bản phiên âm Antigravity. Các lượt OCR mới chỉ bổ sung/kiểm đúng chỗ thiếu; provenance và sửa nguồn có receipt riêng. Sinh Cà Mau còn một bảng thí nghiệm không có trong ảnh: hàng liên quan ghi bất định, không suy mức phân hóa từ khóa đơn thuần.
- Đã sửa bảng Hóa Nghệ An lần hai và các tham chiếu hình va chạm theo địa chỉ (part, idx), có lưu bản trước sửa. Các môn chưa đủ năm đề không có khẳng định tần suất.
- Hồ sơ phân biệt các ý TF trong một câu, chùm nhiều câu và tư liệu xuyên phần. Thứ tự quan sát không tự thành luật cố định. Audit product hiện chỉ là đọc code/probe dữ liệu; chưa có chứng minh runtime áp dụng toàn bộ.
- Checkout product cũ đã không còn ở đường dẫn ban đầu. Đã khôi phục bản lưu đọc theo revision `de8c614ada6e3ae9f9072cedb7521fb96c1d13e5` từ Git cục bộ trong scratch corpus; cả mười lăm prototype sản phẩm khớp hash inventory. Receipt: `audit/outputs/product-snapshot-recovery.json`. Không đổi sang bản product mới và không sửa checkout sản phẩm.
- Kiểm corpus tập trung mới nhất: 97 mục đạt, không lỗi. Đây không phải kiểm định đúng/sai chuyên môn hay nghiệm thu product.
- Đã bắt đầu chạy audit ma trận cho Toán/Sinh/Sử và audit prototype mù môn Sử; chưa nghiệm thu kết quả các bước này. Chưa có phân bố NB/TH/VD của đề thật hoặc bộ câu mẫu mới theo từng chủ đề. Mẫu ngoại ngữ mới cũng chưa hoàn tất. Không push/merge; mọi ghi chỉ trong nhánh corpus được chỉ định.

Hồ sơ gồm `rows.json`, `distributions.json`, `profile.compact.json`, `paper-structures.json`, `verification.json` và `NOTE.md`. Kết quả cơ học và nhận định model được ghi riêng; số đề và số câu/ý không dùng lẫn nhau.

## Bổ sung hồ sơ — checkpoint tiếp tục

- Đã xuất audit ma trận Toán, Sinh, Sử ở `audit/matrices/`; chỉ đề xuất, chưa sửa product. Phải đọc giới hạn bước ánh xạ và mẫu số nguồn riêng.
- Đã chấm mù prototype Sử. Sau chuẩn hóa ký hiệu D/Đ bằng utility canonical không còn bất đồng khóa do ký hiệu; một cờ cách hiểu cần giáo viên. Nhiễu liên hệ được lỗi 72/72 nhưng 14 phương án vẫn bị model đánh dấu dễ loại qua lời văn; tiêu chí kết hợp đạt 58/72 theo model, không phải dữ liệu học sinh.
- Audit prototype Sinh và Toán đang chạy; không coi số đo độ dài trước đó là chấm nội dung.
- Sinh đã có nhãn nhận thức cho 240/240 câu/ý theo thang đã đóng băng; phân loại trên khái quát, còn chờ rà đề gốc. Sử và Toán đang tiếp tục.
- Bộ câu mẫu mới đã có công cụ sinh theo ô chủ đề/phần/mức và tự giải mù. Chưa có bộ mẫu hoàn tất tại checkpoint này; worker nối sau phân loại, giữ mọi cờ và không đưa câu app sinh vào tập bằng chứng. Phủ mọi dạng trong cùng ô còn cần rà riêng.
- Trang `profiles/README.md` nay báo riêng từng thành phần, không còn gọi một môn là hồ sơ hoàn chỉnh chỉ vì trích xuất qua kiểm kỹ thuật.

## Giới hạn subscription và nối tiếp

Subscription chạm quota khi chấm PDF Haiku; mọi model step phụ thuộc đã dừng. Supervisor lên lịch probe mới sau 20:44 ngày 03/11/2026 (giờ Việt Nam); thời gian này không phải bảo đảm khả dụng, chỉ tiếp tục sau probe thành công. Trích xuất Hóa đã đủ tám đề, 320 câu/ý và aggregate hai lớp, kiểm kỹ thuật không có cờ chặn. Phân loại nhận thức hiện có: Sinh 240/240 đã xét; Sử 120/240; Toán chưa xét. Đây là phân loại trên khái quát, không là xác nhận trên toàn bộ câu gốc.

Độ phủ audit prototype hiện ba trên mười sáu bản độc lập, tại mười chín đường dẫn. Bản Toán Haiku còn thiếu; các bản tổng hợp Sinh/Toán bị dừng trước khi chạy vì quota. Sử cần cập nhật bảng phủ về mapping canonical mới; các lượt chấm từng câu vẫn được giữ. Worker hồ sơ sẽ ưu tiên nối các phần này từ cache, rồi mức nhận thức và câu mẫu; nó cũng kiểm các prototype ngoài nhóm môn đủ năm đề nhưng báo thiếu chuẩn neo riêng.

Chưa có câu mẫu mới hoàn tất tại checkpoint này. Các worker không coi file partial rỗng là đã có nhãn/mẫu, và hồ sơ đầy đủ vẫn chờ rà. Trang tiến độ nay hiển thị đủ các môn và đưa môn đã đủ nguồn lên trước.

## Quota được chủ sở hữu báo đã phục hồi

Diagnostic `continuous-availability-probe/attempt-2.meta.json` đã thành công; guard quota được bỏ có lưu lịch sử. Đã khởi động lại supervisor đang ngủ theo hạn cũ để chạy tiếp ngay, không chờ 20:44 nữa. Worker hồ sơ đang ưu tiên tổng hợp prototype và bộ câu mẫu Sinh trước. Hiện chưa có môn nào được nghiệm thu đầy đủ theo `profiles/DOSSIER-SPEC.md`; không gắn nhãn hoàn chỉnh cho bản chỉ có trích xuất/audit một phần.

## Khung hồ sơ được chủ sở hữu chấp nhận

Chủ sở hữu đồng ý tiếp tục cấu trúc hồ sơ Sinh làm khung cho các môn còn lại. Đã có những mẫu mới đầu tiên và kiểm tự giải; một mẫu trùng chữ với nguồn và một mẫu lệch mức đã được viết lại có giới hạn, giải mù lại và qua kiểm model, vẫn chờ giáo viên. Bản đầu và mọi receipts được giữ. Lớp hiển thị ghép bản sửa đã kiểm mà không ghi đè manifest của lượt sinh đang chạy. Các môn tiếp theo có cùng bước sửa có giới hạn; trường hợp vẫn không đạt sau sửa được giữ cờ, không tự tiếp tục thử vô hạn.
