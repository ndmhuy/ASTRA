# Cấu trúc từng đề

Địa chỉ chuẩn `(part, index_within_part, sub)`; lưu `printed_number` riêng; mã đề gắn với `paper_id`. **Thứ tự quan sát không phải luật cố định cho mọi đề.**

| Paper ID | Lớp | P1 câu in/phải làm | P2 câu in/phải làm | P2 ý | Nhánh | OCR |
|---|---|---:|---:|---:|---|---|
| `26827f57f9f0` | official | 24/24 | 4/4 | 16 | Không thấy tự chọn | complete |
| `acc23c4ca4f8` | provincial_third_party | 24/24 | 4/4 | 16 | Không thấy tự chọn | complete |
| `686833f78102` | provincial_third_party | 24/24 | 4/4 | 16 | Không thấy tự chọn | complete |
| `5a9dffb03ca8` | provincial_third_party | 24/24 | 4/4 | 16 | Không thấy tự chọn | complete |
| `dff65825f390` | provincial_third_party | 24/24 | 4/4 | 16 | Không thấy tự chọn | partial |
| `08c8696055dd` | provincial_third_party | 24/24 | 4/4 | 16 | Không thấy tự chọn | complete |

**Quan sát 6/6:** thứ tự P1 → P2, P1 chọn 1 trong A–D; P2 4 nhóm tư liệu, mỗi nhóm có 4 ý a–d. Không có nhánh tự chọn được phát hiện trong sáu đề; không suy rộng sang toàn bộ ngân hàng đề.

**Câu chùm/ngữ liệu:**
- `26827f57f9f0`: hồ sơ cấu trúc trước đây ghi 4 ngữ liệu/nhóm shared_stimuli; xem [dữ liệu nhóm](data/stimulus-groups.json) và [bản gốc của đề](evidence/OCR/transcriptions/lich-su/2026-paper/de.md). Nhóm có thể nằm trong một câu TF hoặc nhiều câu; **không chia ý TF thành nhiều câu in**.
- `acc23c4ca4f8`: hồ sơ cấu trúc trước đây ghi 5 ngữ liệu/nhóm shared_stimuli; xem [dữ liệu nhóm](data/stimulus-groups.json) và [bản gốc của đề](evidence/OCR/transcriptions/lich-su/2026-provincial/de-thi-thu-tot-nghiep-2026-lich-su-so-gd-an-giang/de.md). Nhóm có thể nằm trong một câu TF hoặc nhiều câu; **không chia ý TF thành nhiều câu in**.
- `686833f78102`: hồ sơ cấu trúc trước đây ghi 5 ngữ liệu/nhóm shared_stimuli; xem [dữ liệu nhóm](data/stimulus-groups.json) và [bản gốc của đề](evidence/OCR/transcriptions/lich-su/2026-provincial/de-thi-thu-tot-nghiep-2026-lich-su-so-gd-bac-ninh-lan-2/de.md). Nhóm có thể nằm trong một câu TF hoặc nhiều câu; **không chia ý TF thành nhiều câu in**.
- `5a9dffb03ca8`: hồ sơ cấu trúc trước đây ghi 5 ngữ liệu/nhóm shared_stimuli; xem [dữ liệu nhóm](data/stimulus-groups.json) và [bản gốc của đề](evidence/OCR/transcriptions/lich-su/2026-provincial/de-thi-thu-tot-nghiep-2026-lich-su-so-gd-can-tho/de.md). Nhóm có thể nằm trong một câu TF hoặc nhiều câu; **không chia ý TF thành nhiều câu in**.
- `dff65825f390`: hồ sơ cấu trúc trước đây ghi 5 ngữ liệu/nhóm shared_stimuli; xem [dữ liệu nhóm](data/stimulus-groups.json) và [bản gốc của đề](evidence/OCR/transcriptions/lich-su/2026-provincial/de-thi-thu-tot-nghiep-2026-lich-su-so-gd-dien-bien/de.md). Nhóm có thể nằm trong một câu TF hoặc nhiều câu; **không chia ý TF thành nhiều câu in**.
- `08c8696055dd`: hồ sơ cấu trúc trước đây ghi 5 ngữ liệu/nhóm shared_stimuli; xem [dữ liệu nhóm](data/stimulus-groups.json) và [bản gốc của đề](evidence/OCR/transcriptions/lich-su/2026-provincial/de-thi-thu-tot-nghiep-2026-lich-su-so-gd-gia-lai/de.md). Nhóm có thể nằm trong một câu TF hoặc nhiều câu; **không chia ý TF thành nhiều câu in**.

**Ngoại lệ có nghĩa:** các đề An Giang, Bắc Ninh, Cần Thơ, Điện Biên, Gia Lai có nhóm P1 ngữ liệu/bảng dùng cho nhiều câu theo phân tích cũ; đề chính thức không ghi câu chùm P1. Một số cấu trúc `structure.json` chỉ biểu diễn stimulus_id của vài nhóm; cần giữ đối chiếu `paper-structures.json` để không làm mất nhóm, không coi 0 của trường cấu trúc là bằng chứng không có ngữ liệu.

Lượng điểm không được rút ra trực tiếp từ trường cấu trúc OCR; **điểm ở MATRIX-PROPOSAL là thang minh họa được đề xuất**.

Dữ liệu: [data/structure.json](data/structure.json), [data/addresses.json](data/addresses.json), [data/stimulus-groups.json](data/stimulus-groups.json).
