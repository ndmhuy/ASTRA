# Kế hoạch chạy OCR song song (2026-10-29)

Đang chạy: **OCR-4** (Toán tỉnh, 75 đề, nhánh `ocr-4-20261029`, worktree `wt-ocr-4`). Giữ nguyên, không dừng.

## 1. Các làn (mỗi làn một nhánh, một worktree, một thư mục `transcriptions/` riêng)

| Làn | Phạm vi | Số tài liệu | Prompt | Nhánh |
|---|---|---|---|---|
| OCR-4 | Toán tỉnh | 75 | AG-OCR-4 (đang chạy) | ocr-4-20261029 |
| OCR-5A | Vật lí, Hóa, Sinh tỉnh (docx) | 12 + 14 + 14 = 40 | AG-OCR-5A | ocr-5a-20261029 |
| OCR-5B | Sử, Địa, GDKT&PL tỉnh (docx) | 14 x 3 = 42 | AG-OCR-5B | ocr-5b-20261029 |
| OCR-5C | Anh, Văn, Tin, Công nghệ tỉnh (docx) | 14 + 14 + 4 + 3 = 35 | AG-OCR-5C | ocr-5c-20261029 |
| OCR-6 | V-ACT: Đợt 1, Đợt 2, minh họa 2026, minh họa 2025 (4 đề, 120 câu) | 4 | AG-OCR-6 | ocr-6-20261029 |
| OCR-7 | Bộ 25 đề V-ACT Moon (scan 614 trang) | ~25 | AG-OCR-7 | ocr-7-20261029 |
| OCR-8 | Nhật 5 mã, Hàn 1725 (thiếu trang 3-4), Nga 1225 (độ phân giải thấp) | 7 | AG-OCR-8 | ocr-8-20261029 |

Các làn không dùng chung tệp nào ngoài `SHA256SUMS.txt` (gộp bằng cách giữ cả hai phía rồi sắp xếp). Tất cả cắt từ `docs-matrix-rules-20261029`.

## 2. Giới hạn: đĩa và hạn mức, không phải số làn

- Đĩa trống hiện 5,2 GB; quy tắc trong prompt: dưới 5 GB mỗi làn chỉ một worker. Vì vậy chạy cùng lúc **4 làn x 1 worker**, trừ khi giải phóng thêm đĩa (khi đó 2 worker mỗi làn).
- Mỗi làn xóa thư mục scratch của đề vừa xong (đường dẫn tường minh).
- Chiều ảnh: OCR-7 nặng nhất (614 trang). Chỉ chạy làn này khi đã có một làn khác xong.

## 3. Các đợt

- **Đợt 1 (bắt đầu ngay):** OCR-4 (đang chạy) + OCR-6 (V-ACT, giá trị cao, chỉ 4 đề) + OCR-5A + OCR-5B.
- **Đợt 2 (khi một làn của đợt 1 xong):** OCR-5C và OCR-8.
- **Đợt 3:** OCR-7, ban đầu chỉ Giai đoạn 1 (tìm ranh giới đề) và đề 1-5 để chủ app duyệt chất lượng, rồi mới chạy 20 đề còn lại.
- Làn nào xong thì làn kế tiếp bắt đầu; không chờ cả đợt.

## 4. Việc không chạy được bằng agent (chờ chủ app)

1. Chụp lại 4 trang thiếu của OCR-3: GDKT&PL 2025 trang 1, Sử 2025 trang 1, Sinh 2025 trang 1, Vật lí 2026 trang 4, rồi chạy lại 4 đề đó.
2. Đề thật còn thiếu: Trung, Pháp, Đức, Công nghệ của Bộ, Hàn trang 3-4, GDKT&PL 2026, đáp án Vật lí 2025.
3. Phiên âm Toán, Lí, Hóa 2025 từ file scan trong `official/2025-web` (một làn riêng, OCR-9, chưa soạn prompt vì chưa chốt nguồn bản gõ).

## 5. Sau khi OCR: kiểm và gộp

1. Mỗi làn tự báo cáo. Master kiểm: số câu từng phần so với khung đăng ký, mở ảnh, đối chiếu 5 câu (báo cáo không phải bằng chứng).
2. Gộp nhánh theo thứ tự: ocr-1, ocr-2, ocr-3, ocr-4, 5A, 5B, 5C, 6, 7, 8 vào `main` của corpus, chỉ khi chủ app nói gộp; không đẩy.
3. **TAG-1 (đếm chủ đề kinh điển) bắt đầu ngay khi có >= 20 đề Toán tỉnh đã phiên âm và qua kiểm**, không chờ OCR-4 xong; sau đó sửa ma trận mẫu theo số đếm thật (các đề tỉnh là bằng chứng nội bộ, ghi rõ khi trích tần suất).
4. Tin học: trước khi dùng số liệu, chia câu chung và câu theo định hướng (đề in 6 câu đúng/sai, thí sinh làm 4).
5. V-ACT: kiểm 4 x 30 trên từng đề trước khi dùng cho ma trận V-ACT.

## 6. Cách khởi động mỗi làn

Dán nội dung tệp prompt tương ứng trong `prompts/` vào một phiên Antigravity mới. Các tệp: AG-OCR-5A-vat-li.txt, AG-OCR-5B-lich-su.txt, AG-OCR-5C-tieng-anh.txt, AG-OCR-6-vact.txt, AG-OCR-7-vact-moon-bundle.txt, AG-OCR-8-foreign-languages.txt. Bản sao nằm trong corpus tại `docs/ocr-provincial/`.
