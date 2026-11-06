# STRUCTURE — thứ tự, câu chùm và nhánh

## Kết quả quan sát (không phải quy tắc mọi năm)
- Cả **2/2 đề chính thức** và **6/6 đề tỉnh** quan sát theo thứ tự P1 → P2 → P3. Các đề partial vẫn có các phần liên tục nhưng giới hạn đối chiếu đã ghi.
- Mỗi đề ghi P1 **18** câu một đáp án, P2 **4** câu × **4** ý a–d, P3 **6** trả lời ngắn: tổng **28 câu in/28 câu phải làm**, riêng P2 có 16 ý. Số câu trên từng phần được đánh lại từ 1; trường `printed_number` lưu riêng `index_within_part`.
- Không ghi nhận nhánh tự chọn ở 8 đề; `optional_paths=[]`. Điểm chi tiết từng phần không suy diễn từ đề nếu chưa có biểu điểm xác nhận; bảng 10 điểm trong MATRIX-PROPOSAL là **đề xuất**.
- Câu chùm dùng chung giữa **nhiều câu** không giống ngữ liệu cho bốn ý Đúng/Sai của **một câu**. Không cắt ngữ liệu ra khỏi nhóm khi dùng làm đề mẫu.

| Nguồn | P1 | P2 | P3 | Chùm nhiều câu | Nhánh |
|---|---:|---:|---:|---|---|
| `53f7e0c73214` | 18 | 4×4 | 6 | 53f7e0c73214-S1: P1.17, P1.18 | không |
| `30e3a77f6f23` | 18 | 4×4 | 6 | 30e3a77f6f23-S1: P1.16, P1.17 | không |
| `a381d0bc1996` | 18 | 4×4 | 6 | không quan sát | không |
| `7090ca87e657` | 18 | 4×4 | 6 | không quan sát | không |
| `02f028487a62` | 18 | 4×4 | 6 | không quan sát | không |
| `0ccfacf4a5ac` | 18 | 4×4 | 6 | không quan sát | không |
| `cd005a72af60` | 18 | 4×4 | 6 | không quan sát | không |
| `126f1b46d648` | 18 | 4×4 | 6 | 126f1b46d648-S1: P1.17, P1.18 | không |

**Nhóm dùng chung:** [data/stimuli.json](data/stimuli.json) lưu `scope=multiple_questions` đối với cặp câu P1 17–18 (2025 official), P1 16–17 (2026 official), P1 17–18 (Nghệ An); các `scope=statements_within_question` khác ở P2 là ngữ liệu của bốn ý trong một câu.
**Ngoại lệ và vị trí:** có chùm P1 ở ba đề nêu trên, năm đề còn lại P1 được mô tả tách câu. Vị trí chùm không cố định qua các đề; không ép mọi đề ở vị trí 17–18.
**Dấu hiệu thú vị:** mẫu quan sát có thể đặt các câu chùm P1 16–17 trước câu P1 18 độc lập; không diễn dịch thứ tự phần hoặc thứ tự câu chùm là luật phổ quát.

Chi tiết 8 đề, ngữ liệu, phần/câu/ý và thứ tự khối nằm ở [data/structures.json](data/structures.json), [data/stimuli.json](data/stimuli.json), [data/addresses.json](data/addresses.json); gốc theo từng đề trong `evidence/OCR/.../structure.json`.
