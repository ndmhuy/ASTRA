# Báo cáo lab hồ sơ đề Toán — 02/11/2026

## Kết luận

Chưa thể kết luận B thắng A: không lượt đối sánh nào đạt DONE.
Chưa đo được B−A ở cả hai lần; A2/B2 chưa chạy, nên cũng chưa có mức dao động A1−A2.
Thí nghiệm dừng theo brief sau hai lỗi cùng nguyên nhân ở A1; đây không phải kết quả âm hoặc bằng chứng Luna đã chạm giới hạn chất lượng.

## Bảng số liệu

“—” nghĩa là chưa đo, không phải bằng không. Chỉ đề đạt DONE mới được tính vào đối sánh.

| Đề | Backend/model cho pipeline | Trạng thái | Điểm chấm mù | Slot phân hóa cao đã chấm | Đáp án dài nhất / độ dài phương án | Sai toán / sai key |
|---|---|---|---|---|---|---|
| A1 | Codex CLI / gpt-6-luna | Dừng, exit 4; chưa DONE | — | — | — | — |
| A2 | Dự kiến cùng Luna | Chưa chạy | — | — | — | — |
| B1 | Codex CLI / gpt-6-luna | Dừng chủ động theo hard stop; chưa DONE | — | — | — | — |
| B2 | Dự kiến cùng Luna | Chưa chạy | — | — | — | — |
| Đề chính thức 2026 | Đề nguồn; extraction Sonnet có sẵn | 34 slot đã trích; chưa chấm mù | — | — | — | — |

Phần đã hoàn thành:

| Hạng mục | Kết quả |
|---|---|
| Đề tỉnh để dựng hồ sơ | 9/9; 306 slot |
| Địa chỉ slot | Khớp nguồn; không thiếu/thừa/trùng sau sửa một lỗi nhãn ở p02 |
| Hồ sơ | 45 patterns; khoảng 38.803 ký tự theo json.dumps |
| Tham chiếu bị loại | 0/342, tính trên patterns + discrimination_moves |
| Tách đề chính thức | HELDOUT_2026 không vào đầu vào aggregate |
| Kiểm tra sao chép hồ sơ | Đã đọc toàn bộ mẫu; không thấy câu/số liệu/tình huống cụ thể. Quét cụm 10 từ: 0 ứng viên trùng; 0 chuỗi số ngoài ref IDs |
| Request được ghi | A1: 15, có 11 reply; B1: 25, có 21 reply. Không tính request đang dở là thành công |

Sonnet đã trích p01, p02, p03 và đề chính thức. Sol trích p04–p09 và dựng hồ sơ. p02 có đúng nội dung II/3/a nhưng nhãn phần bị ghi III; đã đối chiếu nguồn, lưu bản gốc và chỉ sửa nhãn, không trích lại. Extraction đề chính thức gán 6 slot “high” (II: 3, III: 3), lớp 10/11/12 lần lượt 2/6/26 slot; đây là nhận định Sonnet, chưa phải chấm độc lập hoặc xác nhận của giáo viên.

## Điểm nghẽn

**Điểm dừng trực tiếp là khả năng vận chuyển ảnh của backend lab.** A1 calls/010.json và calls/015.json đều trả `Fatal('images not supported by the dev CLI provider')`. Adapter từ chối trước khi gọi model. A1 tự dừng ở lần thứ hai; B1 có một lỗi tương tự và được dừng khi kiểm tra phát hiện hard stop của A1. Không bỏ bước ảnh, không đổi backend, không chạy A2/B2.

Áp dụng bảng “Cách đọc kết quả” trong kế hoạch: chưa đủ bằng chứng để chọn “dữ liệu kém”, “câu vẫn dễ dù kế hoạch tốt”, “B tốt hơn A” hoặc “A/B không khác nhau”. Chưa có đề hoàn chỉnh hay điểm mù. Cần giải quyết đường chạy thí nghiệm trước khi quy kết cho dữ liệu, composer hoặc năng lực model.

**Có bằng chứng hẹp về đường hồ sơ:** B1 synthesis 002 và ba composer ban đầu 006/008/011 đều có exam_profile cùng addendum thích hợp. A1 không có cả hai. Nhưng hai lượt viết lại B1 018/019 có addendum mà thiếu khối hồ sơ; vì vậy chưa thể xác nhận treatment tồn tại xuyên suốt đường composer/rewrite. Không sửa hook rồi chạy tiếp sau hard stop.

A1 plan ready có notices document/scope/other/defaults; B1 có defaults. Không thấy synthesis_unavailable trong hai plan.json. “Ready” không xác nhận chất lượng kế hoạch.

**Coverage chưa có kết quả được chấp nhận.** Script tôi viết yêu cầu model trả địa chỉ lồng trong `address`, nhưng lại đọc trường `part` ở cấp ngoài. Cả hai lần trả lời có 34 hàng với cấu trúc address đều làm script lỗi KeyError('part'). Đây là lỗi code lab, không phải lỗi suy luận của Sol. Hai reply thô được giữ để duyệt; chưa dùng chúng công bố tỷ lệ bao phủ hoặc độ phủ nhóm high.

## Ví dụ

Chưa có 2–3 cặp A/B hợp lệ: cả hai đề còn dở và chưa chấm độc lập. Không chọn các đoạn thuận lợi trong đề dở để minh họa hiệu quả. Nội dung đề nguồn không được trích trong báo cáo này.

## Giới hạn và phần chưa kiểm chứng

- Thiết kế chỉ có hai đề mỗi nhánh; thực tế hiện có **0 đề sinh hợp lệ**. Không có suy luận thống kê hay kết quả null.
- Theo điều chỉnh của chủ app: prompt pipeline đối sánh dùng Luna; các bước làm mẫu dùng Sol. Claude đã từ chối do weekly limit. Mọi model call mới dùng Codex CLI subscription, không dùng API key có tính phí. Kết quả tương lai trên Luna không chứng minh hiệu quả trên Haiku chỉ vì cùng tier.
- Bốn extraction cũ từ Sonnet được giữ lại, với một sửa nhãn có lưu dấu; các bản còn lại dùng Sol. Phân tích mẫu vì thế có nguồn model hỗn hợp.
- Extraction chỉ đọc văn bản/mô tả hình, không đọc ảnh. Có mẫu tổng hợp ghi rõ hình thiếu hoặc dữ liệu mâu thuẫn; chưa có thẩm định toán từng đề nguồn. Đề tỉnh có thể khó hơn đề chính thức.
- Quét trùng chữ không chứng minh không sao chép về cấu trúc; kiểm tra đọc hồ sơ vẫn là đánh giá của agent.
- Chưa thực hiện chấm mù, giải độc lập, xếp hạng, phân bố key/đúng-sai, đo lặp chủ đề/cấu trúc, số bước hoặc so trùng từng câu sinh. grade.py và các helper mới chỉ được chuẩn bị/kiểm tra cú pháp, chưa được xác nhận qua một lượt đánh giá đầy đủ. Giám khảo dự kiến là Sol, vẫn là model chứ không phải giáo viên.
- Helper kế thừa dùng TemporaryDirectory và đã tự dọn scratch ngoài sb trong các call ban đầu, trái giới hạn dọn tạm của brief. Đã ghi sai sót vào RUNLOG, đổi helper sang thư mục giữ lại trong sb và khởi động lại p09 chưa hoàn tất. Không có lệnh xóa corpus, checkout hoặc thư mục làm việc của người dùng; không khẳng định đã kiểm toán mọi thao tác tạm nội bộ của sản phẩm/CLI.
- Không sửa/commit/merge/push sản phẩm hoặc corpus. Product checkout vẫn clean ở revision de8c614ada6e3ae9f9072cedb7521fb96c1d13e5, branch claude/agent-runner. Không chạy full suite, không mở UI, không build/release.

## Đề xuất bước tiếp theo

1. Xác minh đường ảnh dùng được với Luna/Codex subscription trong lab, giữ nguyên các bước pipeline; nếu không hỗ trợ thì cần chủ app quyết định ràng buộc backend trước khi đối sánh lại.
2. Sửa schema địa chỉ coverage và hook đưa hồ sơ vào lượt rewrite trong lab; kiểm tra bằng request capture trước lần thử tiếp theo.
3. Khi đường chạy đã thông, chạy lại đủ bốn đề cùng Luna đến DONE rồi chấm mù bằng Sol theo tiêu chí đã ghi trước. Chưa có cơ sở đưa prompt vào sản phẩm hay mở rộng môn.

## Tệp để chủ app duyệt

Tất cả nằm trong `/Users/huynguyen/Lecturing_Lab/agent-review/TOAN-PROFILE-1102/`. Không commit gì.

**Prompt thực tế đã dùng:**

- `/Users/huynguyen/Lecturing_Lab/agent-review/TOAN-PROFILE-1102/prompts/EXTRACT.txt`
- `/Users/huynguyen/Lecturing_Lab/agent-review/TOAN-PROFILE-1102/prompts/AGGREGATE.txt`
- `/Users/huynguyen/Lecturing_Lab/agent-review/TOAN-PROFILE-1102/prompts/PLAN_ADDENDUM.txt`
- `/Users/huynguyen/Lecturing_Lab/agent-review/TOAN-PROFILE-1102/prompts/COMPOSER_ADDENDUM.txt`
- `/Users/huynguyen/Lecturing_Lab/agent-review/TOAN-PROFILE-1102/prompts/COVERAGE.txt`
- Full system/user prompt và reply từng lời gọi pipeline: `/Users/huynguyen/Lecturing_Lab/agent-review/TOAN-PROFILE-1102/outputs/run-A1/calls/` và `/Users/huynguyen/Lecturing_Lab/agent-review/TOAN-PROFILE-1102/outputs/run-B1/calls/`.

**Prompt mới chuẩn bị, chưa chạy:** NORMALIZE.txt, GRADE.txt, RANK.txt trong thư mục tuyệt đối `/Users/huynguyen/Lecturing_Lab/agent-review/TOAN-PROFILE-1102/prompts/`.

**Test case và giao thức:**

- Danh mục đề: `/Users/huynguyen/Lecturing_Lab/agent-review/TOAN-PROFILE-1102/papers/INDEX.txt`; văn bản p01.md–p09.md cùng thư mục.
- Đề giữ riêng: `/Users/huynguyen/Lecturing_Lab/agent-review/TOAN-PROFILE-1102/papers/HELDOUT_2026.md`.
- Danh sách đường dẫn tuyệt đối và SHA đầu vào/prompt/extraction: `/Users/huynguyen/Lecturing_Lab/agent-review/TOAN-PROFILE-1102/outputs/input-sha256.json`.
- Giao thức ghi trước khi sinh: `/Users/huynguyen/Lecturing_Lab/agent-review/TOAN-PROFILE-1102/EVALUATION_PROTOCOL.md`.

**Đầu ra thật và bằng chứng lỗi:**

- `/Users/huynguyen/Lecturing_Lab/agent-review/TOAN-PROFILE-1102/outputs/profile.raw.json`
- `/Users/huynguyen/Lecturing_Lab/agent-review/TOAN-PROFILE-1102/outputs/profile.compact.json`
- `/Users/huynguyen/Lecturing_Lab/agent-review/TOAN-PROFILE-1102/outputs/profile-audit.json`
- `/Users/huynguyen/Lecturing_Lab/agent-review/TOAN-PROFILE-1102/outputs/extraction-validation.json`
- `/Users/huynguyen/Lecturing_Lab/agent-review/TOAN-PROFILE-1102/outputs/STOP-SUMMARY.json`
- Hai plan.json và treatment-observations.json trong `/Users/huynguyen/Lecturing_Lab/agent-review/TOAN-PROFILE-1102/outputs/run-A1/` và `/Users/huynguyen/Lecturing_Lab/agent-review/TOAN-PROFILE-1102/outputs/run-B1/`.
- Session dở A1: `/Users/huynguyen/Lecturing_Lab/agent-review/TOAN-PROFILE-1102/sb/A1/state/exam_generator/sessions/LAB_A1_gen_1793589219.json`.
- Session dở B1: `/Users/huynguyen/Lecturing_Lab/agent-review/TOAN-PROFILE-1102/sb/B1/state/exam_generator/sessions/LAB_B1_gen_1793589219.json`.
- Coverage reply đã giữ: `/Users/huynguyen/Lecturing_Lab/agent-review/TOAN-PROFILE-1102/outputs/coverage-attempts/`; inventory đường dẫn: `/Users/huynguyen/Lecturing_Lab/agent-review/TOAN-PROFILE-1102/outputs/coverage-attempt-inventory.json`.
- `/Users/huynguyen/Lecturing_Lab/agent-review/TOAN-PROFILE-1102/run-A1.log`
- `/Users/huynguyen/Lecturing_Lab/agent-review/TOAN-PROFILE-1102/run-B1.log`
- `/Users/huynguyen/Lecturing_Lab/agent-review/TOAN-PROFILE-1102/coverage.log`
- `/Users/huynguyen/Lecturing_Lab/agent-review/TOAN-PROFILE-1102/RUNLOG.md`

Mở báo cáo bằng liên kết tệp trong chat, hoặc `open '/Users/huynguyen/Lecturing_Lab/agent-review/TOAN-PROFILE-1102/REPORT.md'`.
