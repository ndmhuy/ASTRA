# Kế hoạch triển khai UI/UX để Agent tự động điều phối ứng dụng

Tài liệu giao việc cho UI/UX. Quyết định kỹ thuật dưới đây do owner Agent chốt làm baseline
triển khai; chưa phải xác nhận đã được UI/Backend review. Nếu cần thay đổi, ghi deviation trong PR,
không tự đổi wire contract ở một phía. Ưu tiên tài liệu này hơn ví dụ camelCase trong handoff cũ
đối với đợt tích hợp hiện tại.

## Mục tiêu và thứ tự

Người dùng nói “Mở Tủ đề” → Agent phát instruction → UI tự gọi chức năng mở Tủ đề → trả receipt
→ Agent xác nhận. Không yêu cầu người dùng bấm thêm cho navigation. Hành động tạo đề cần bước
confirmation riêng sau backend validation.

Milestone M1 hoàn tất vòng navigation thật. M2 mở rộng các thao tác UI có sẵn. M3 nối intake,
approval và generation sau khi Backend đáp ứng contract. UI có thể hoàn thành M1 và dựng handler
M2 ngay, không cần đợi generation.

## Các quyết định đã chốt

| Vấn đề | Quyết định triển khai |
|---|---|
| Wire naming | `snake_case` khớp Python hiện tại; UI nội bộ vẫn camelCase, map duy nhất tại adapter |
| Turn version | `agent-turn/0.1` |
| Plan version | `agent-actions/0.1` |
| Response | `kind`, `reply`, `data`, `mock`; action nằm tại `data.plan` |
| Transport | `POST /agent/turns`, `POST /agent/execution-results` đã tồn tại |
| Approval route | Chưa tồn tại; UI không gọi `/agent/confirmation-results` ở M1 |
| Cách gọi chức năng UI | Registered handler dùng chung với nút React; không DOM selector/eval |
| Thực thi | Serial, chờ state commit và quan sát hiệu ứng trước receipt |
| Start generation owner | UI generation adapter là caller duy nhất; Agent chỉ plan approved reference |
| Enabled action M1 | Chỉ `ui.navigate`, target `application` |
| Source contract | OpenAPI từ standalone Agent app và Pydantic hiện tại; TS adapter kiểm tra runtime |
| Network local | Vite proxy `/agent` sang `http://127.0.0.1:8010`; browser gọi cùng origin |
| Dev state | Một process Agent; in-memory; reload/restart không có recovery bền vững |
| Production | Auth/persistence/permissions là milestone riêng trước deployment |

UI không thêm field camelCase hoặc field khác vào request hiện tại: Pydantic `extra=forbid`.
`data` còn generic ở OpenAPI; UI kiểm tra `data.plan` theo plan contract bên dưới. Agent team sẽ
siết typed payload theo hướng tương thích, không đổi envelope giữa lúc UI đang triển khai.

## Bảng giao việc UI/UX

| ID | Công việc và file dự kiến (UI sở hữu) | Phụ thuộc | Tiêu chí nghiệm thu |
|---|---|---|---|
| U01 | `src/integration/agentProtocol.ts`: wire types + runtime parsers cho turn/plan/receipt | Contract trong tài liệu này | Unknown version, extra action key, params sai type, quá 5 action, trùng ID bị từ chối |
| U02 | `src/integration/uiController.tsx`: cung cấp semantic handlers và context từ App/store | U01 | Context phản ánh state đã commit; không tạo state/router cạnh tranh với App |
| U03 | `src/integration/uiCapabilities.ts`: registry + availability | U02 | Chỉ advertise handler đã cài và khả dụng; mobile collapse unavailable |
| U04 | `src/integration/uiExecutor.ts`: validate, serial execution, receipt ledger | U01–U03 | Duplicate plan/action không lặp hiệu ứng; stale state bị chặn; thất bại dừng dependent actions |
| U05 | `src/services/agentService.ts`, `vite.config.ts`: HTTP adapter + proxy | U01 | Parse response runtime; xử lý non-2xx, timeout, retry cùng payload/ID; không tự gửi lại bằng ID mới |
| U06 | `src/state/examSessions.ts`: bỏ canned assistant, tách append user/assistant và turn pending/error | U05 | Tin nhắn không mất khi lỗi; callback cập nhật workspace gốc; retry không thêm user message lần hai |
| U07 | `src/integration/agentController.ts`: vòng turn → execute → report → render | U04–U06 | Action tự chạy; thành công chỉ hiển thị sau receipt; không tạo vòng tool loop không giới hạn |
| U08 | `App.tsx` và chat components: nối controller, tách agent loading/generation | U07 | Chat help/status vẫn gửi khi generation chạy; không khóa toàn composer bằng `isGenerating` |
| U09 | Shell-level helper/history có target rõ khi rời workspace | U06–U08 | Navigation không làm mất final reply; có thể quay lại xem đúng conversation |
| U10 | Tests protocol/executor/store và browser E2E | U01–U09 | Các ca trong checklist dưới pass; command và kết quả được ghi trong PR |
| U11 | Các handler M2: create/open setup/sidebar | M1 pass | Dựng/test handler trên mock plan; chưa advertise live trước khi Agent adapter hỗ trợ |
| U12 | `UI_AGENT_DELIVERY.md`: hướng dẫn chạy, capability đã bật, test evidence, deviations | Tất cả | Agent team có thể checkout và tái hiện không cần đoán |

Không cần đổi thiết kế/styling toàn App. Giữ UI identity; chỉ thêm controller và các điểm nối nhỏ.

## Context và identity

Wire `ScreenContext` hiện chỉ nhận:

```json
{
  "screen_id": "workspace",
  "state_version": 12,
  "workspace_session_id": "ws-01",
  "selected_question_id": null,
  "question_index_map": {},
  "available_actions": ["ui.navigate"]
}
```

- `screen_id`: welcome/create/library/workspace. Off workspace, context workspace là null.
- `state_version`: số nguyên tăng khi navigation, selection, xóa target hoặc availability đổi;
  không tăng theo progress tick/clock/typing.
- Turn `workspace_session_id` là target của conversation gốc, vẫn `ws-01` sau khi vào library.
- `conversation_id` độc lập workspace/job/exam. Core hiện pin một workspace/conversation; mở
  workspace khác dùng conversation khác. Không rebind conversation cũ ngầm.
- M1 bắt đầu chat từ workspace có thật. Global chat chưa có workspace là extension M2 cần Agent
  bổ sung; không bịa ID để vượt schema hiện tại.
- Question IDs trên wire là string: chuyển number UI bằng `String(id)` với mapping scoped đúng
  workspace; display index không đồng nghĩa stable ID.
- Chỉ đọc mapping question của workspace gốc; không dùng selection workspace mới cho reply cũ.

Sau navigation, controller đọc context mới nhưng receipt vẫn giữ target conversation/workspace
gốc. Nếu người dùng tự chuyển trang trong lúc chờ Agent, reject plan cũ bằng `STALE_CONTEXT`;
không kéo người dùng về tự động.

## Contract M1 khớp code Agent hiện tại

Turn request:

```json
{
  "schema_version": "agent-turn/0.1",
  "request_id": "req-01",
  "conversation_id": "conv-01",
  "workspace_session_id": "ws-01",
  "message": "Mở Tủ đề",
  "screen_context": {
    "screen_id": "workspace", "state_version": 12,
    "workspace_session_id": "ws-01", "selected_question_id": null,
    "question_index_map": {}, "available_actions": ["ui.navigate"]
  }
}
```

Trong response `kind=action_plan`, `data.plan` có shape:

```json
{
  "schema_version": "agent-actions/0.1",
  "plan_id": "plan-req-01",
  "conversation_id": "conv-01",
  "expected_state_version": 12,
  "actions": [{
    "action_id": "action-req-01", "capability_id": "ui.navigate",
    "target": "application", "params": {"screen_id": "library"}
  }]
}
```

Feedback sau UI commit:

```json
{
  "feedback_id": "feedback-01",
  "conversation_id": "conv-01",
  "workspace_session_id": "ws-01",
  "original_request_id": "req-01",
  "results": [{
    "plan_id": "plan-req-01", "action_id": "action-req-01",
    "status": "success", "error_code": null,
    "data": {"screen_id": "library"}, "state_version": 13
  }]
}
```

Agent trả final `kind=reply`. `status` nhận success/failed/skipped; failed/skipped bắt buộc
`error_code`, success bắt buộc error null. Mỗi action có đúng một result theo thứ tự; không bỏ
action thất bại/skipped khỏi report. Sau failure, phần còn lại skipped với `DEPENDENCY_FAILED`.

Error codes UI dùng: `STALE_CONTEXT`, `UNKNOWN_CAPABILITY`, `INVALID_PARAMS`,
`CAPABILITY_UNAVAILABLE`, `SESSION_NOT_FOUND`, `ACTION_FAILED`, `DEPENDENCY_FAILED`.
Không gửi raw exception/DOM/credential vào `data`.

Network timeout khi báo receipt: giữ receipt và retry nguyên feedback ID/payload; không thực thi
lại plan. Ledger key `(conversation_id, plan_id, action_id)` và payload fingerprint. Payload đổi
với cùng key phải reject. Interaction epoch riêng giúp phát hiện thao tác người dùng xen ngang;
stateVersion do action trước trong plan thay đổi không làm bước sau tự stale.

## Handler M2 và giới hạn hiện tại

| Capability | Target | Params theo snake_case | Receipt cần quan sát | Trạng thái |
|---|---|---|---|---|
| `ui.navigate` | application | `screen_id`, workspace target thêm `workspace_session_id` | màn hình + workspace thật sau commit | M1 live chỉ library; core hiện hiểu “Mở Tủ đề” |
| `ui.session.create` | exam-sessions | `mode`: template/custom | `created_workspace_session_id` | UI dựng/test; Agent planner/receipt support làm sau |
| `ui.exam.open_setup` | exam-setup | `workspace_session_id` | dialog visible và đúng target | UI dựng/test; Agent nối sau |
| `ui.sidebar.set_collapsed` | main-navigation | `collapsed`: boolean | effective collapsed sau commit | UI dựng/test; Agent nối sau |
| `exam.generate` | exam-generation | `workspace_session_id`, `approved_request_id` | backend accepted job ID | BLOCKED tới M3 |

Các hàng M2/M3 là contract mục tiêu, chưa phải capability Agent đã triển khai. Handler không
được coi enabled chỉ vì type đã viết. Agent sẽ mở rộng registry sau khi nhận delivery UI.
Tạo workspace trả ID mới: dừng plan, báo receipt, chờ plan tiếp theo có ID thật; không `$lastResult`.

## Checklist nghiệm thu UI

| Test | Kỳ vọng |
|---|---|
| “Mở Tủ đề” từ workspace | instruction tự thực thi; final reply xem được cả khi workspace chat unmount |
| Turn retry cùng ID/payload | Một user message, một effect, không canned response |
| User đổi workspace trước response | Plan cũ bị từ chối; workspace mới không bị tác động |
| Unknown/disabled action, extra param | Zero side effect và typed error |
| Hai action, action 2 fail | Giữ success action 1; không rollback tưởng tượng |
| Double-delivery plan/receipt | Không lặp effect; trả kết quả đã lưu |
| Network fail sau UI commit | Retry feedback nguyên ID; không chạy action lần hai |
| Generating + help/status | Composer gửi được; generation request không đổi |
| StrictMode remount | Không launch action/job trong mount effect |
| Không có handler hoặc backend readiness | Không advertise; thông báo khả năng thực tế |
| Reload | Nêu state-loss thực tế; không phát lại job tự động |

## Nhánh, ownership và quy trình bàn giao giảm conflict

1. UI tạo `feat/<github-user>/agent-ui-executor` từ latest
   `origin/feat/longlth2297/agent-ui-integration` sau khi fetch. Không code trực tiếp branch chung.
2. UI chỉ sửa `astra-frontend/**` và thêm delivery report trong cùng thư mục. Không sửa
   `src/exam_baseline/**`, `tests/agent/**`, `docs/agent/**` hoặc handoff cũ.
3. Agent team sở hữu Python source/tests, contract exports và `docs/agent/**`; không sửa frontend
   trong lúc UI đang làm task này.
4. Không merge/update branch chung bằng force push. UI push feature branch rồi mở PR về branch
   integration, gửi branch/SHA + delivery report. Không đưa node_modules/dist/.env vào Git.
5. Agent fetch, review và test PR đó; sau khi team review mới merge. Agent tiếp tục adapter/planner
   riêng, không đổi wire name/version ngầm. Mọi breaking change tăng protocol version.

## Agent làm tiếp sau UI push

| ID | Công việc Agent | Đầu vào từ UI |
|---|---|---|
| A01 | Đối chiếu OpenAPI/fixture với parsers UI, siết typed response payload | U01 + fixtures |
| A02 | Dev bootstrap enable navigation chỉ khi handler thật được cài; mặc định core vẫn tắt | U02–U04 delivery |
| A03 | Chạy browser E2E qua HTTP thực, sửa correlation/receipt bugs phía Agent | U05–U10 |
| A04 | Mở rộng intent, registry và receipt cho create/setup/sidebar; final reply theo action | U11 handler tests |
| A05 | Thêm global conversation chưa có workspace và binding explicit workspace mới | UI global helper + create receipt |
| A06 | Tích hợp descriptor/evaluator/approval/jobs thật khi Backend cung cấp | Contract Backend M3 |

Current standalone Agent mặc định không enable navigation: UAT có thể dùng fake Agent adapter
cho UI component tests và enabled registry fixture cho Agent contract tests. Agent team sẽ cung cấp
dev bootstrap A02 khi handler UI đã có; không tự advertise từ client là đủ để bypass registry.

Không cần chờ Backend cho M1/M2. Các chức năng generation/progress/edit thật vẫn cần Backend;
UI và Agent không tự dựng matrix hay gọi sync `/v2` như async job.

## Lệnh kiểm tra và delivery report

UI chạy `npm ci`, `npm run build`, `npm run lint`, store tests và tests mới executor/protocol;
thêm browser E2E theo stack test UI lựa chọn, ghi lệnh chính xác để Agent tái hiện.
Delivery report phải có branch/SHA/base SHA, file thay đổi, handler installed/enabled/blocked,
fixture turn/receipt, test pass/fail/warning và các deviation khỏi bảng này.

Agent local chạy:

```powershell
.\.venv-agent\Scripts\python.exe -m uvicorn exam_baseline.agent.http:create_agent_app --factory --host 127.0.0.1 --port 8010
```

M1 được nghiệm thu khi browser thật chạy đủ vòng message → instruction → UI effect → receipt
→ final reply. Build riêng hai project thành công chưa đáp ứng tiêu chí này.
