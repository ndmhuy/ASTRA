# gdktpl — S-C2 handoff, CLI thật 06/11/2026

Nhánh `data/sol-gdktpl-20261106`; dữ liệu và index được đọc ở commit `3effc9c1f02975e5dd8b45960899d7e43dfe073c`. Tool nhánh `rel/s-c2-mas-quality`, commit `c2b4ecbdeea7ac2596c7905f34b110afb5f14741` (chứa `adbc2c38`).

Hai dòng stdout nguyên văn từ CLI đã đăng kí:

```json
{"subject": "gdktpl", "papers": 14, "failed": []}
{"subject": "gdktpl", "items": 560, "groups": 31, "patterns": 0, "samples": 0, "problems": 0, "gaps": 0, "revision": "6bc277d9878a20db", "bytes": 571234, "out": "/tmp/sol-gdktpl-pack.json"}
```

Nguồn trùng byte với merged-20261102; mọi git diff bên dưới có stdout rỗng.

Đã hoàn lại 1 de.md; kiểm đúng 31 đoạn instruction/stimulus và cập nhật source_sha256.

```sh
git diff data/merged-20261102 -- transcriptions/gdktpl/2026-provincial/de-thi-thu-tn-2026-mon-kinh-te-phap-luat-so-gd-quang-tri-lan-1/de.md
```

Tất cả lệnh trên có stdout rỗng. Không cần fallback merge-base vì các tệp đều có trên merged-20261102.


[Biên nhận đầy đủ](S-C2-CLI-20261106.json) · [Handoff JSON](S-C2-HANDOFF.json)

Đã chép stdout rồi xóa đúng `/tmp/sol-gdktpl-pack.json`. CLI xanh là kiểm cấu trúc/gói dữ liệu; không phải duyệt nội dung, giáo viên hay runtime.


## Nội dung sau chỉnh lý dùng được — 06/11/2026

Xem [USABILITY-REVIEW](USABILITY-REVIEW.md) và [CLI thật](USABILITY-CLI-20261106.json). Tính đúng/sai tách khỏi mức bằng chứng; không yêu cầu giáo viên duyệt trong lane này, không giả teacher-approved. Giữ nguyên mọi transcription.

```json
{"subject": "gdktpl", "papers": 14, "failed": []}
{"subject": "gdktpl", "items": 560, "groups": 31, "patterns": 0, "samples": 0, "problems": 0, "gaps": 0, "revision": "6bc277d9878a20db", "bytes": 571237, "out": "/tmp/usable-gdktpl-pack.json"}
```
