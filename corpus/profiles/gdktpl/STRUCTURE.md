# STRUCTURE — phát hiện trong 14 đề tỉnh

| Phần | Số câu in | Học sinh làm | Đánh số | Tự chọn |
| --- | --- | --- | --- | --- |
| P1 | 24 câu | 24 câu chọn 1/4 đáp án A–D | 1–24; lưu printed_number | Chưa thấy nhánh |
| P2 | 4 câu × 4 ý | 4 câu, 16 ý đúng/sai | 1–4 và a–d; mức từng ý | Chưa thấy nhánh |

**Tần suất cấu trúc quan sát:** 14/14 đề tỉnh có thứ tự P1 → P2 và đúng 24 + 4 câu (16 ý TF). Đề chính thức 0/0, không ngoại suy từ tỉnh sang quy tắc bắt buộc; nhãn câu P1 và P2 đều bắt đầu lại từ 1. Các bản OCR không ghi nhánh tự chọn.

**Câu chùm/ngữ liệu dùng chung:** nhóm P1 có số lượng khác nhau theo đề; giữ một `stimulus_id` cho toàn nhóm và `addresses[]` cho các câu phụ thuộc, không chia ngữ liệu thành câu tự do. TF P2 là một stem có bốn ý, không phải bốn câu độc lập.

- P01 (Cà Mau): 2 nhóm: P01:P1-S01: P01:P1:17,P01:P1:18; P01:P1-S02: P01:P1:22,P01:P1:23,P01:P1:24
- P02 (Phú Thọ): 2 nhóm: P02:P1-S01: P02:P1:20,P02:P1:21,P02:P1:22; P02:P1-S02: P02:P1:23,P02:P1:24
- P03 (Tuyên Quang): 2 nhóm: P03:P1-S01: P03:P1:15,P03:P1:16; P03:P1-S02: P03:P1:19,P03:P1:20,P03:P1:21
- P04 (Quảng Trị): 2 nhóm: P04:P1-S01: P04:P1:04,P04:P1:05,P04:P1:06; P04:P1-S02: P04:P1:13,P04:P1:14
- P05 (Tuyên Quang): 2 nhóm: P05:P1-S01: P05:P1:10,P05:P1:11; P05:P1-S02: P05:P1:17,P05:P1:18,P05:P1:19
- P06 (Đà Nẵng): 2 nhóm: P06:P1-S01: P06:P1:20,P06:P1:21; P06:P1-S02: P06:P1:22,P06:P1:23,P06:P1:24
- P07 (Hải Phòng): 2 nhóm: P07:P1-S01: P07:P1:15,P07:P1:16; P07:P1-S02: P07:P1:22,P07:P1:23,P07:P1:24
- P08 (Đồng Nai): 2 nhóm: P08:P1-S01: P08:P1:20,P08:P1:21,P08:P1:22; P08:P1-S02: P08:P1:23,P08:P1:24
- P09 (Hải Phòng): 2 nhóm: P09:P1-S01: P09:P1:13,P09:P1:14; P09:P1-S02: P09:P1:23,P09:P1:24
- P10 (Hưng Yên): 2 nhóm: P10:P1-S01: P10:P1:21,P10:P1:22; P10:P1-S02: P10:P1:23,P10:P1:24
- P11 (Nghệ An): 3 nhóm: P11:P1-S01: P11:P1:19,P11:P1:20; P11:P1-S02: P11:P1:21,P11:P1:22; P11:P1-S03: P11:P1:23,P11:P1:24
- P12 (Ninh Bình): 2 nhóm: P12:P1-S01: P12:P1:17,P12:P1:18,P12:P1:19,P12:P1:20; P12:P1-S02: P12:P1:21,P12:P1:22,P12:P1:23,P12:P1:24
- P13 (Sơn La): 4 nhóm: P13:P1-S01: P13:P1:06,P13:P1:07; P13:P1-S02: P13:P1:11,P13:P1:12,P13:P1:13; P13:P1-S03: P13:P1:16,P13:P1:17; P13:P1-S04: P13:P1:22,P13:P1:23,P13:P1:24
- P14 (Vĩnh Long): 2 nhóm: P14:P1-S01: P14:P1:05,P14:P1:06; P14:P1-S02: P14:P1:19,P14:P1:20,P14:P1:21

**Số in và thứ tự dạng:** địa chỉ chuẩn `(part_id,index_within_part,sub)` tách `printed_number`. Cụm hiện đặt ở vị trí thay đổi; không coi một chuỗi chủ đề quan sát là thứ tự cố định. Giới hạn: một số nguồn có cảnh báo in số câu/trang (xem [SOURCE-CORRECTIONS](SOURCE-CORRECTIONS.md)).
