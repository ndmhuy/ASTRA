# Schema và nguồn sự thật — Hóa học

## Các snapshot hiện hành

- `data/source-observations-current.json`: mỗi phần tử `source_rows` là một câu/ý OCR, có ID `paper|part|printed-question|sub`, topic chính/tích hợp, lớp đề, mức và dấu vết nguồn. ID nguồn không dùng số in làm chỉ số câu toàn cục.
- `data/samples-current.json`: bản sao 116 mẫu được nhận trong `data/scoped-final-bank.json`; mọi mẫu synthetic, có khóa/lời giải/mức và trạng thái duyệt. `teacher_approved` là `false`.
- `data/coverage-current.json`: 124 ô `topic_id + part + level`, trạng thái và danh sách sample/support refs. Ô phủ không khẳng định phủ mọi biến thể.
- `COVERAGE.csv` là bảng đọc được tạo từ cùng danh sách cells hiện hành.
- `completion.json` tổng hợp số đếm hiện hành và các giới hạn nghiệm thu.

## Ranh giới bằng chứng

Nguồn OCR/ảnh tạo thống kê; mẫu synthetic chỉ minh họa cách xây câu và không cộng vào tần suất. Mức nguồn có thể `Unknown` nếu ảnh/OCR thiếu dữ kiện quyết định. Các key nguồn chưa được xác thực độc lập toàn bộ. Dossier nghiên cứu chưa phải cấu hình runtime hay đề được giáo viên phê duyệt.
