# SOURCES — nguồn và giới hạn

- `PACKAGE.json` xác nhận môn **Hóa học**, baseline tại SHA `de8c614ada6e3ae9f9072cedb7521fb96c1d13e5`, `baseline_is_live_runtime=false`, `limited_evidence=false`.
- Corpus gồm 8 nội dung đề độc lập: 2 official/2, 6 provincial_third_party/6; không có format_only. OCR: 5 complete và 3 partial. Không lấy prototype làm đề thứ 9.
- 2026 chính thức có ảnh JPG bốn trang; 2025 chính thức có PDF và crop OCR; đề tỉnh gốc DOCX. Ở lượt này tái sử dụng OCR, đối chiếu cấu trúc trong OCR, kiểm trực tiếp một crop pin; không OCR lại hàng loạt hoặc khẳng định đối chiếu ký tự toàn bộ.
- Một nội dung prototype SHA `28eb748d17fc...` có hai origin `product`, `corpus` cùng byte-identical; audit một. Bản PDF trong `evidence/prototypes/.../COMPILED-FOR-AUDIT.pdf` được tạo tại lượt này từ LaTeX, không phải PDF nguồn.
- Trạng thái complete chỉ nghĩa đóng gói đọc được; không tương đương khóa khớp đề, duyệt giáo viên hay kiểm thử runtime.

| ID đề | Lớp nguồn | Mã | OCR | Trang quan sát/ghi | Khóa kèm | Nội dung |
|---|---|---|---|---|---|---|
| `53f7e0c73214` | official | 0301 | complete | 4/4 | không | [OCR](evidence/OCR/transcriptions/hoa-hoc/2025-paper/de.md) |
| `30e3a77f6f23` | official | 0323 | complete | 4/4 | không | [OCR](evidence/OCR/transcriptions/hoa-hoc/2026-paper/de.md) |
| `a381d0bc1996` | provincial_third_party | 0301 | complete | 4/4 | có, chưa xác minh độc lập | [OCR](evidence/OCR/transcriptions/hoa-hoc/2026-provincial/de-thi-thu-tn-2026-mon-hoa-so-gd-ca-mau-lan-1/de.md) |
| `7090ca87e657` | provincial_third_party | 0301 | partial | 4/4 | không | [OCR](evidence/OCR/transcriptions/hoa-hoc/2026-provincial/de-thi-thu-tn-2026-mon-hoa-so-gd-quang-ninh-lan-1/de.md) |
| `02f028487a62` | provincial_third_party | 0303 | partial | 6/4 | có, chưa xác minh độc lập | [OCR](evidence/OCR/transcriptions/hoa-hoc/2026-provincial/de-thi-thu-tn-2026-mon-hoa-so-gd-quang-tri-lan-1/de.md) |
| `0ccfacf4a5ac` | provincial_third_party | 0301 | complete | 4/4 | có, chưa xác minh độc lập | [OCR](evidence/OCR/transcriptions/hoa-hoc/2026-provincial/de-thi-thu-tn-2026-mon-hoa-so-gd-son-la-lan-2/de.md) |
| `cd005a72af60` | provincial_third_party | 0301 | complete | 4/4 | có, chưa xác minh độc lập | [OCR](evidence/OCR/transcriptions/hoa-hoc/2026-provincial/de-thi-thu-tn-thpt-nam-2026-mon-hoa-so-gd-da-nang-lan-1/de.md) |
| `126f1b46d648` | provincial_third_party | 0401 | partial | 5/4 | có, chưa xác minh độc lập | [OCR](evidence/OCR/transcriptions/hoa-hoc/2026-provincial/de-thi-thu-tn-thpt-nam-2026-mon-hoa-so-gd-nghe-an-lan-2/de.md) |

**Các cờ trọng yếu:**
- 2025 official: file đáp án nghiên cứu trước không xác minh khớp mã PDF gốc, hiện gói không có `key.json`; không sử dụng để đánh giá độ đúng/sai của nhiễu.
- Quảng Ninh: `partial`, không có bảng khóa khớp mã được xác nhận. Quảng Trị và Nghệ An: sai khác số trang đề khi render DOCX so với ghi đầu đề; không tự coi là mất trang.
- Các bộ đáp án tỉnh còn lại có trong gói không đồng nghĩa đã được giáo viên xác thực. Dấu khoanh bài làm thí sinh không dùng làm khóa.
- Tái sử dụng [existing profile](evidence/existing-profile/NOTE.md) làm bản gắn nhãn cũ; `grade` 10/11/12 biểu thị **lớp học**, không phải nhận thức NB/TH/VD. Mức nhận thức của corpus giữ `unknown` cho tới khi thẩm định item.

Xem [bản gốc PACKAGE](evidence/PACKAGE.json), [OCR manifest](evidence/OCR/manifest.json), [ma trận baseline](evidence/baseline/default-matrix-and-shape.json), [level scheme](evidence/baseline/level-scheme.json), [lịch sử corrections](SOURCE-CORRECTIONS.md) và [issues có địa chỉ](data/input-issues.json).
