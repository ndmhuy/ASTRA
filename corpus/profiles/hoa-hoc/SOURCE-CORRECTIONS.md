# SOURCE-CORRECTIONS — Không sửa raw OCR

Không tạo chỉnh sửa mới vào `evidence/OCR/` ở lượt này. Mọi raw `de.md`, `structure.json`, `CHANGES.md`, hình cắt và `issues.json` được sao chép nguyên vẹn từ đầu vào.

| Nguồn | Dấu hiệu/vấn đề | Chứng cứ | Quyết định |
|---|---|---|---|
| `53f7e0c73214` | thiếu khóa trong gói khớp nguồn | [STATUS/CHANGES](evidence/OCR/transcriptions/hoa-hoc/2025-paper/CHANGES.md) và [issues](evidence/OCR/transcriptions/hoa-hoc/2025-paper/issues.json) | Giữ OCR, đánh cờ và không tự suy diễn khóa |
| `30e3a77f6f23` | thiếu khóa trong gói khớp nguồn | [STATUS/CHANGES](evidence/OCR/transcriptions/hoa-hoc/2026-paper/CHANGES.md) và [issues](evidence/OCR/transcriptions/hoa-hoc/2026-paper/issues.json) | Giữ OCR, đánh cờ và không tự suy diễn khóa |
| `a381d0bc1996` | không phát hiện thay đổi bổ sung có chứng cứ | [STATUS/CHANGES](evidence/OCR/transcriptions/hoa-hoc/2026-provincial/de-thi-thu-tn-2026-mon-hoa-so-gd-ca-mau-lan-1/CHANGES.md) và [issues](evidence/OCR/transcriptions/hoa-hoc/2026-provincial/de-thi-thu-tn-2026-mon-hoa-so-gd-ca-mau-lan-1/issues.json) | Giữ OCR, đánh cờ và không tự suy diễn khóa |
| `7090ca87e657` | OCR partial, không kết luận đã kiểm mọi ký tự; thiếu khóa trong gói khớp nguồn | [STATUS/CHANGES](evidence/OCR/transcriptions/hoa-hoc/2026-provincial/de-thi-thu-tn-2026-mon-hoa-so-gd-quang-ninh-lan-1/CHANGES.md) và [issues](evidence/OCR/transcriptions/hoa-hoc/2026-provincial/de-thi-thu-tn-2026-mon-hoa-so-gd-quang-ninh-lan-1/issues.json) | Giữ OCR, đánh cờ và không tự suy diễn khóa |
| `02f028487a62` | OCR partial, không kết luận đã kiểm mọi ký tự; phân trang DOCX/PDF render 6 ≠ 4 trang ghi đầu đề; chưa chắc thiếu trang | [STATUS/CHANGES](evidence/OCR/transcriptions/hoa-hoc/2026-provincial/de-thi-thu-tn-2026-mon-hoa-so-gd-quang-tri-lan-1/CHANGES.md) và [issues](evidence/OCR/transcriptions/hoa-hoc/2026-provincial/de-thi-thu-tn-2026-mon-hoa-so-gd-quang-tri-lan-1/issues.json) | Giữ OCR, đánh cờ và không tự suy diễn khóa |
| `0ccfacf4a5ac` | không phát hiện thay đổi bổ sung có chứng cứ | [STATUS/CHANGES](evidence/OCR/transcriptions/hoa-hoc/2026-provincial/de-thi-thu-tn-2026-mon-hoa-so-gd-son-la-lan-2/CHANGES.md) và [issues](evidence/OCR/transcriptions/hoa-hoc/2026-provincial/de-thi-thu-tn-2026-mon-hoa-so-gd-son-la-lan-2/issues.json) | Giữ OCR, đánh cờ và không tự suy diễn khóa |
| `cd005a72af60` | không phát hiện thay đổi bổ sung có chứng cứ | [STATUS/CHANGES](evidence/OCR/transcriptions/hoa-hoc/2026-provincial/de-thi-thu-tn-thpt-nam-2026-mon-hoa-so-gd-da-nang-lan-1/CHANGES.md) và [issues](evidence/OCR/transcriptions/hoa-hoc/2026-provincial/de-thi-thu-tn-thpt-nam-2026-mon-hoa-so-gd-da-nang-lan-1/issues.json) | Giữ OCR, đánh cờ và không tự suy diễn khóa |
| `126f1b46d648` | OCR partial, không kết luận đã kiểm mọi ký tự; phân trang DOCX/PDF render 5 ≠ 4 trang ghi đầu đề; chưa chắc thiếu trang | [STATUS/CHANGES](evidence/OCR/transcriptions/hoa-hoc/2026-provincial/de-thi-thu-tn-thpt-nam-2026-mon-hoa-so-gd-nghe-an-lan-2/CHANGES.md) và [issues](evidence/OCR/transcriptions/hoa-hoc/2026-provincial/de-thi-thu-tn-thpt-nam-2026-mon-hoa-so-gd-nghe-an-lan-2/issues.json) | Giữ OCR, đánh cờ và không tự suy diễn khóa |

**Không chuẩn hóa raw OCR**; danh pháp mới trong mẫu/đánh giá được xử lý riêng theo `TERMINOLOGY.md`. Chưa kiểm thêm từng ký tự bằng PDF/Word toàn bộ; không tuyên bố “không có lỗi” ở nguồn partial.

## Bổ sung: phân biệt lỗi prototype với OCR

Nhận xét giáo viên được ghi vào [TEACHER-FEEDBACK.md](TEACHER-FEEDBACK.md) cho prototype `28eb748d17fc`, **không** phải chứng cứ sửa OCR của 8 đề corpus. Do đó `evidence/OCR/` và file LaTeX prototype gốc đều được giữ nguyên; sửa prototype phải thực hiện trên **bản dẫn xuất riêng** sau này, chưa có bản đó ở đợt này.
