# lich-su — S-C2 handoff, CLI thật 06/11/2026

Nhánh `data/sol-lich-su-20261106`; dữ liệu và index được đọc ở commit `a11c8e995f98f896f9abe1faa11348a4ab7f82de`. Tool nhánh `rel/s-c2-mas-quality`, commit `c2b4ecbdeea7ac2596c7905f34b110afb5f14741` (chứa `adbc2c38`).

Hai dòng stdout nguyên văn từ CLI đã đăng kí:

```json
{"subject": "lich-su", "papers": 6, "failed": []}
{"subject": "lich-su", "items": 240, "groups": 5, "patterns": 32, "samples": 70, "problems": 0, "gaps": 0, "revision": "71be840640528e2a", "bytes": 553391, "out": "/tmp/sol-lich-su-pack.json"}
```

Không có yêu cầu hoàn nguyên văn bản ở môn này; chỉ dựng lại bằng CLI đã đăng kí.


[Biên nhận đầy đủ](S-C2-CLI-20261106.json) · [Handoff JSON](S-C2-HANDOFF.json)

Đã chép stdout rồi xóa đúng `/tmp/sol-lich-su-pack.json`. CLI xanh là kiểm cấu trúc/gói dữ liệu; không phải duyệt nội dung, giáo viên hay runtime.

## Cập nhật nội dung06/11/2026 — nhánh data/usable-lich-su-20261106

[USABILITY-REVIEW](USABILITY-REVIEW.md) thay thế số mẫu/hold trong snapshot bên trên:73 mẫu nội dung dùng được; phục hồi LS-V-004/007 ởTH, sửa lỗi yêu cầu LS-V-002 và dùngTH. Không loại mẫu đúng do chưa chắc nhãnVD. Coverage nhãn cũ64/67, bằng chứng mức không điều kiện59/67+5conditional+3proposed_unfilled. Không cần một gate giáo viên mới; không giảteacher-approved hoặc runtime-tested. Pack thật đã đọc lại đủ73 mẫu và5status có điều kiện.

```json
{"subject": "lich-su", "papers": 6, "failed": []}
{"subject": "lich-su", "items": 240, "groups": 5, "patterns": 32, "samples": 73, "problems": 0, "gaps": 0, "revision": "9ca0494260aadf49", "bytes": 568369, "out": "/tmp/usable-lich-su-pack.json"}
```
