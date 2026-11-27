# Bàn giao Agent và phục hồi sinh đề

Cho chủ sản phẩm và người review. Ứng dụng thật đang mở tại **http://localhost:8002** từ worktree `../ASTRA.worktrees/longlth2297-agent-reliability-resume`. Phiên8001 cũ được giữ nguyên. Không có yêu cầu inference thật hay đề thi thật nào được tạo khi thực hiện công việc này.

## Nhánh và phạm vi

Base `origin/main` lúc bắt đầu: **98b1df5467255b5de94f0b3191b5613db33bd48a**. Nhánh mới: **feat/longlth2297/agent-reliability-resume**, tạo trực tiếp từ base này. Main đã có semantic Agent, contracts/resolver/memory/receipts, Chat/MAS riêng, các môn THPT mới, upload/web/history/export và stop/continue; không cần merge toàn bộ nhánh Agent cũ. Các worktree cũ và file chưa commit của checkout gốc được giữ nguyên. Chỉ commit local; không push, PR, merge main hay deploy Cloudflare.

Không sửa prompt/schema/thuật toán học thuật, template/môn thi, scoring, RAG, Blind Solver, model, credential hoặc chính sách ngân sách development. Các file của UI/Backend hiện có chỉ được sửa ở phần kết nối, lifecycle/checkpoint/transport và test doubles cần metadata; thiết kế UI của đồng đội được giữ.

## Lỗi đã sửa và tính năng đã nối

- Continue cũ tạo job khác: resume/retry hiện giữ cùng job ID và cấu hình ban đầu, tăng executionVersion.
- Khởi động lại cũ đánh dấu lỗi hoặc không có quyền sở hữu: nay có lease/heartbeat, thu hồi executor hết hạn và chuyển interrupted, không tự gửi AI. Executor cũ không được ghi checkpoint hoặc publish phiên bản mới.
- Checkpoint ghi trực tiếp/thiếu manifest: nay ghi atomic, checksum và kiểm tra request/provider/model/template/version cùng native academic contract khi khôi phục.
- Pause cũ chưa có: nay chờ phản hồi đang gọi được kiểm tra/lưu rồi dừng trước công việc tiếp theo. Cancel vẫn là dừng lượt chạy/transport hiện tại. Pause trong thời gian backoff ngăn lượt retry mới.
- UI cũ coi mất kết nối theo dõi là job thất bại: nay tiếp tục reconnect và báo chưa biết trạng thái mới. SSE/library cũ không được lùi executionVersion; chặn click/control trùng.
- Agent có pause/resume/retry/cancel/status, liệt kê job có thể phục hồi, đọc lý do lỗi/tạm dừng; dùng trạng thái Backend và hỏi rõ khi nhiều job cùng khớp. Receipt phân biệt “đã nhận yêu cầu” với “đã chạy/đã tạm dừng”.
- Đã nối lịch sử phiên bản và tải bản đề Word/Markdown đã duyệt vào adapter hiện có. Hướng dẫn upload/web phản ánh tính năng thực tế. Retry preview vẫn tách khỏi retry sinh đề. Chặn lệnh ghi chú kèm duyệt/xuất bị nhận nhầm thành một ghi chú đơn.
- Local grammar ghép động từ/đối tượng/từ lịch sự, chuẩn hóa dấu và dùng catalog thực tế. Câu hỏi, phủ định, giả định, trích dẫn, nhiều thao tác và `dung` không dấu mơ hồ không tự thực hiện lifecycle.

## Đo local routing

Thêm144 câu/34 nhóm diễn đạt và12 ngữ cảnh chọn job, bên cạnh153 semantic records cũ. Xem [dataset và phương pháp](../../eval/agent-semantic/README.md) và [kết quả sinh bằng script](../../eval/agent-semantic/local-routing-results.json).

| Chỉ số offline | Development | Evaluation |
|---|---:|---:|
| Nhóm / câu |17 /68|17 /76|
| Đúng kỳ vọng đã gán nhãn |68/68|76/76|
| Đúng semantic (loại safety/invalid) |60/60|56/56|
| Độ phủ local |64/68 (94.12%)|66/76 (86.84%)|
| False execution trên câu safety |0/4|0/20|
| Fast path được nhận sai |0|0|
| Model fallback baseline → hiện tại |34→4|37→3|

Chọn job theo ngữ cảnh:12/12.4,320 mẫu đo sau warm-up: p50≈0.008ms, p95≈0.039ms, chỉ parsing/routing. Fallback giảm64/71 (90.14%) trên bộ này là **ước lượng từ quyết định routing**, không phải lưu lượng API thực. Bộ evaluation chia theo nhóm nhưng do engineer soạn và đã xem; một lỗi safety phát hiện ở evaluation đã sửa và giữ làm regression. Các số là kết quả **sau sửa**, không phải đánh giá mù, độ chính xác LLM hay chất lượng đề Gemini.

## Retry và tính toàn vẹn

`resources/agent/recovery-policy.json` là cấu hình versioned. MAS RecordingProvider sở hữu transport retry: mặc định tối đa2 attempt cho một lần yêu cầu schema; Reviewer vẫn chỉ1. Native Agent sở hữu lượt sửa schema/học thuật như trước, không bị thay thế bằng transport retry. HTTP adapter, Worker và Gateway không retry thêm. Schema repair có thể tạo lượt yêu cầu mới trong giới hạn học thuật hiện có;2 không phải trần mọi lượt gọi của toàn đề.

Backoff có jitter, tôn trọng Retry-After, deadline operation400s, trace operation fingerprint ổn định và attempt UUID khác nhau. Chat Router chỉ retry khi kết nối thất bại hoặc Worker xác nhận chưa admission/chưa có upstream attempt; giữ turn ID và deadline gốc. Không tự lặp inference đã admission nhưng chưa rõ kết quả.

| Loại lỗi | Xử lý |
|---|---|
| Connect timeout/error | Retry có giới hạn |
| Overload500/502/503, capacity, rate limit có bằng chứng | Retry có backoff; hết lượt thì paused |
| Response timeout/504/network không rõ đã xử lý | Interrupted, chờ người dùng tiếp tục |
|429 không đủ metadata | Không auto retry; yêu cầu thao tác sau khi xem trạng thái |
| Daily quota/budget, auth, model, request | Không auto retry; hiện lỗi cần xử lý cấu hình/quota |
| JSON/schema hoặc kiểm định học thuật | Native repair/validators hiện có; không coi là lỗi transport |

Không cam kết exactly-once inference ở nhà cung cấp. Timeout có thể đã tiêu quota. UI/application commit được bảo vệ bằng job ID, version, lease/owner và transaction. Retry-After lưu qua pause/restart và chặn resume quá sớm.

## Checkpoint và khởi động lại

- `runs/ui/jobs.sqlite3`: job gốc, request hash, trạng thái, executionVersion/owner/lease, retry/not-before và chỉ mục checkpoint.
- `runs/ui/<jobId>/_generation/_internal/request.json`, `checkpoint-manifest.json`, `checkpoints/<operation>.json`: cấu hình và **response học thuật thật đã validate**, role/revision/part/ID câu hỏi/checksum. Report giữ attempt accounting. File JSON ghi fsync rồi atomic replace; quyền executor được kiểm tra trong SQLite transaction.
- Các stage/batch Composer/Illustrator/Solver/Reviewer hoàn tất được khôi phục và kiểm tra lại native contract/dependency. Không chỉ lưu phần trăm. THPT dùng section, V-ACT dùng batch hiện có; chưa có checkpoint bên trong một phản hồi API đang chạy.
- Pause là cooperative: API request đang chạy chưa được “đóng băng”. Phản hồi hợp lệ được lưu trước khi paused. Cancel có thể khiến phần đang gọi chưa lưu phải làm lại khi chủ động tiếp tục.
- Sau crash, executor hết lease30s được chuyển interrupted khi Backend/status/library kiểm tra. Lease còn sống không bị chiếm. Reload/restart không schedule inference. Job cũ không có checkpointVersion hợp lệ hoặc checkpoint hỏng/khác model/template/config bị từ chối; không tự migrate/regenerate.
- Kiểm thử trên SQLite/file thật cho thấy pause sau P2 giữ16 câu; restart/resume cùng job chỉ gọi Composer P3, không gọi lại P1/P2. Cùng kịch bản với durable record giả lập process chết/hết lease cũng phục hồi đúng. Duplicate resume chỉ schedule một executor; control cũ và late write bị chặn. Chat giả vẫn trả lời trong pausing/paused.

## Cloudflare

Chat và MAS vẫn đi qua hai Worker/Gateway riêng. Không sửa/deploy Worker Chat hay canonical contract hashes. Các goal mới nằm trong local sidecar; UI và câu lệnh local dùng ngay. LLM của Chat Worker đang deploy chưa biết các goal lifecycle mới; cách diễn đạt phức tạp ngoài local grammar có thể cần hỏi rõ. Một bản cập nhật protocol được phối hợp riêng mới mở rộng AI interpretation cho chúng.

MAS Worker có thay đổi **local** để giữ metadata lỗi/quota và Retry-After đã sanitize, phân biệt capacity/budget và log operation/attempt. Worker đang deploy vẫn dùng được nhưng chưa có metadata mới; Backend xử lý lỗi không rõ một cách thận trọng. Không tự deploy theo yêu cầu hiện tại.

Đã chuẩn bị ignored profile `workers/astra-mas-proxy/.wrangler/reliability-development.jsonc` từ development profile của operator; chỉ đổi đường dẫn entry point sang worktree mới, giữ vars/bindings/namespace/model/keep_vars. Dry-run đã qua. **Sau khi chủ sản phẩm duyệt deployment riêng**, tại worktree này:

```powershell
Set-Location workers/astra-mas-proxy
npm run check
npm test
npx wrangler deploy --config .wrangler/reliability-development.jsonc
```

Profile ignored chỉ có trên máy hiện tại. Trên máy khác cần lấy lại active operator config qua quy trình sẵn có, chỉ đổi `main` tới `src/index.ts` của checkout mới và giữ nguyên tất cả vars/bindings. Không deploy trực tiếp tracked `wrangler.jsonc`: mặc định của nó đóng forwarding và bật ngân sách. Không đặt lại Secrets/counters, không tạo resource/billing mới. Sau deployment chỉ GET health để kiểm tra; mọi inference vẫn do chủ sản phẩm thao tác.

GET health thực bằng httpx ở thời điểm bàn giao: cả Chat/MAS HTTP200, forwarding=true, budgetsEnabled=false; MAS configured/callerAuthorization=true. Đây chỉ là metadata, chưa chứng minh Gemini trả được đề.

## Kiểm tra đã chạy

-544 Python tests và7 subtests qua, với socket guard chặn kết nối ngoài loopback trong process pytest; toàn bộ providers/HTTP upstream kiểm thử là fixture/fake. Bao gồm THPT/các môn/V-ACT, Blind Solver, RAG, preview/export, API Chat và persistence/recovery. Test doubles được bổ sung metadata đúng interface; không nới manifest hoặc academic assertions.
-71 frontend tests qua; build/lint qua. TypeScript Worker qua;14 Miniflare fake-upstream groups qua; prepared-config deploy **dry-run** qua.
-23 file Python đã thay đổi qua Ruff check và format check.
-`scripts/verify.sh`: compile qua, dừng ở89 lỗi lint có sẵn trong14 file không đổi so với base. Không tuyên bố common verification xanh. Có một warning deprecation Starlette/httpx và advisory frontend chunk>500kB.
-Actual `start.cmd --port8002 --no-browser` đã chạy; Edge hiện start screen/catalog “Dùng AI thật”. Health local: demoMode=false, providerConfigured=true, LaTeX available,8 formats. Runtime DB vẫn0 jobs/0 workspaces. Không gửi Chat/generation POST.

Chạy lại test offline trong worktree: `./.venv-win/Scripts/python.exe -m pytest -q`; frontend: vào `astra-frontend`, chạy `npm test`, `npm run build`, `npm run lint`. Benchmark: `node --experimental-strip-types astra-frontend/scripts/agent-benchmark.mjs --save`.

## Chủ sản phẩm tự nghiệm thu

1. Mở **http://localhost:8002**, chọn mẫu và tự bấm tạo đề. Đối chiếu stage, số câu và tốc độ; thử chat song song.
2. Bấm **Tạm dừng** hoặc nhắn “Tạm nghỉ tí”. Khi đang gọi phải hiện pausing; chỉ hiện paused sau khi Backend lưu phản hồi hợp lệ. Thử “Đừng tạm dừng”/“Cách tạm dừng?” để kiểm tra không đổi job.
3. Reload trang khi paused: phải còn số câu đã lưu và nút tiếp tục. Nhắn “Làm tiếp phần đang dở”, kiểm tra cùng job ID, executionVersion tăng và không lặp section/batch đã hợp lệ.
4. Khi gặp lỗi recoverable, xem lý do và Retry-After; tự chọn thử lại/tiếp tục. Bấm nhiều lần không được tạo job/executor thứ hai. Có nhiều job khớp thì Agent phải hỏi rõ.
5. Muốn kiểm tra restart: tự dừng server rồi chạy lại `start.cmd --port8002 --no-browser` trong worktree này. Chờ tối đa lease30s nếu lần trước tắt đột ngột. Phải interrupted/paused, chưa tự có inference; chỉ tiếp tục sau lệnh của bạn.
6. Sau khi hoàn tất, kiểm tra đáp án/preview, tự duyệt và tải PDF/Word/Markdown như luồng cũ; xem lịch sử phiên bản.

Chưa kiểm chứng live: Gemini generation/quality/throughput, lỗi thực upstream, tương tác chat với một đề thật và UI trong lúc nhận response thật. Các phần này dành cho thao tác của chủ sản phẩm. Không có blocker local còn lại; remote metadata mới và semantic AI lifecycle expansion cần các deployment riêng đã mô tả.
