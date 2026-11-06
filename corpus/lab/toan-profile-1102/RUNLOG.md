# RUNLOG — TOAN-PROFILE-1102

2026-11-02 ICT. Tiếp tục theo brief; chỉ sửa lab, không sửa/commit sản phẩm hoặc corpus.

- Claude probe: `claude -p --model sonnet`, từ chối: weekly limit, resets 22:00 Asia/Saigon.
- Backend chọn một lần: Codex CLI subscription; model cố định `gpt-6.1-sol` (model trong cấu hình hiện tại). Xóa biến API key khỏi môi trường subprocess.
- Bốn extraction có sẵn p01, p02, p03, HELDOUT_2026: Sonnet, mỗi bản 34 slot duy nhất; giữ nguyên.
- Extraction còn lại, aggregate, coverage, writer A1/A2/B1/B2 và grader dự kiến: Codex CLI `gpt-6.1-sol`. Không có grader mạnh hơn được xác minh; sẽ ghi hạn chế nếu dùng cùng model.
- Product checkout kiểm tra read-only: `claude/agent-runner`, clean. Không chạy suite hoặc UI.
- Executor sandbox không khởi động do writable root Lecturing_Marketing là symlink; các lệnh được chạy qua escalation. Không đổi cấu hình máy.
- Sửa retry lab từ ba xuống tối đa hai lần theo brief. Không xóa dữ liệu.

- Codex probe thành công: OK. Model cấu hình `gpt-6.1-sol`, reasoning effort kế thừa `medium`. Extraction mới đã hoàn tất p04 và p05, mỗi bản 34 slot.
- Chuẩn bị `EVALUATION_PROTOCOL.md` trước khi có đề A/B. Các script mới chỉ qua kiểm tra cú pháp; chưa coi là kiểm chứng hành vi.
- `run_arm.sh` giữ API/proxy/license env trống và `PYTHONDONTWRITEBYTECODE=1`; không có bước build/release.

- Audit p02 Sonnet: hàng thứ 21 bị ghi phần III trong khi là II/3/a. Đối chiếu nguồn xác nhận đúng nội dung; chỉ sửa nhãn `part` từ III sang II, không trích lại, không sửa nhận định. Bản gốc giữ tại outputs/extraction-originals/p02.sonnet.original.json. Sau sửa: 12 + 16 + 6 slot.

- Chủ app điều chỉnh model trước mọi lượt sinh đề: các prompt pipeline thật phải chạy Luna vì Haiku là mặc định cùng tier. Writer/planner/solver/critics/compiler-model trong A1, A2, B1, B2 cố định `gpt-6-luna`, backend `codex-cli`. Trích dữ liệu và aggregate vẫn `gpt-6.1-sol`; grader dùng Sol (model mạnh hơn writer). Chưa có lượt sinh nào trước thay đổi. Phần dự kiến writer Sol ở đầu log được thay thế bởi quyết định này.

- Chủ app xác nhận: đối sánh lập kế hoạch/sinh đề Luna, mọi bước làm mẫu Sol. Grade dùng Sol độc lập với Luna.
- Phát hiện script kế thừa dùng TemporaryDirectory ngoài sb và tự dọn thư mục CLI tạm sau call; đã thay bằng thư mục giữ lại trong sb/cli-cwd, không xóa. Bản extract đang chạy được khởi động trước sửa nên vẫn mang hành vi cleanup kế thừa; không có lệnh xóa corpus/sản phẩm. Đây là sai sót tuân thủ phạm vi dọn tạm cần ghi rõ.

- Luna probe thành công (`gpt-6-luna`, Codex subscription, medium). p08 đã lưu đủ 34 slot. Dừng tiến trình extract cũ lúc p09 mới bắt đầu, khởi động lại phần còn thiếu để mọi scratch mới ở trong sb; không sửa dữ liệu đã hoàn tất.

- Extraction hoàn tất p01–p09: 9 × 34 = 306 slot; HELDOUT_2026 34 slot. `validate_extractions.py` đối chiếu địa chỉ với nguồn: không thiếu/thừa/trùng. Chỉ nhãn p02 II/3/a đã sửa có lưu bản gốc.
- Product revision read-only: `de8c614ada6e3ae9f9072cedb7521fb96c1d13e5`, branch `claude/agent-runner`. Hash 39 tệp đầu vào/prompt/extraction ở outputs/input-sha256.json.
- Aggregate bắt đầu bằng Sol, đọc đúng glob extract/p*.json, không đọc HELDOUT_2026.

- Aggregate Sol hoàn tất: 45 patterns, compact 38,803 ký tự (json.dumps), `bad_refs_dropped=0 / total_refs=342` cho patterns + discrimination_moves. HELDOUT không có trong source_files. Đã đọc 45 mẫu và các phần còn lại: không thấy câu cụ thể/số liệu/tên tình huống; quét 10-gram không có overlap. Các ứng viên số đều là ref IDs, không phải nội dung mẫu.

- A1/B1 thực chạy bằng Luna. A1 plan ready với notices document/scope/other/defaults; B1 ready với defaults. Không thấy synthesis_unavailable trong hai plan.json.
- A1 dừng tự động exit 4 sau hai lỗi provider cùng nguyên nhân: calls/010.json và 015.json, Fatal("images not supported by the dev CLI provider"). B1 có cùng lỗi một lần (012); dừng chủ động theo hard stop toàn thí nghiệm. A2/B2 chưa khởi động.
- A1 có 15 request captures, 11 reply; B1 có 25 request captures, 21 reply. Request không có reply khi tiến trình dừng không phải đầu ra thành công.
- Treatment: B1 synthesis 002 và composer ban đầu 006/008/011 có profile + addendum. Rewrite 018/019 có addendum nhưng thiếu profile. A1 synthesis/composer đã ghi không chứa cả hai. Không chấp nhận full-path treatment.
- Coverage Sol: script lỗi KeyError('part') hai lần vì prompt yêu cầu address lồng, code lại đọc phẳng. Đây là lỗi lab do tác giả script, không phải chứng cứ model kém. Không sửa rồi chạy tiếp vì đã chạm hard stop.
- Không lượt nào DONE. Không chạy chấm mù, xếp hạng hoặc tính chỉ số A/B trên đề dở dang; không có bảng ánh xạ mù đã sử dụng. Các script grade/prepare hiện chỉ chuẩn bị + kiểm tra cú pháp.
- Kiểm tra git cuối: product worktree vẫn clean, branch claude/agent-runner. Không sửa/commit/merge/push sản phẩm/corpus, không mở UI, không chạy full suite. Không có lệnh xóa dữ liệu.
