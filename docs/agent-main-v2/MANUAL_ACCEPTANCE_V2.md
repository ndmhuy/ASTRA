# ASTRA Agent V2 manual acceptance

For the teacher or operator validating the product on the current feature branch. Use a new conversation for unrelated scenarios. Leave MAS in demo mode.

## Observed offline evidence

| Case | Evidence before manual acceptance |
| --- | --- |
| 1 and 2. “Tạo đề thi thử tốt nghiệp” then “Toán” | Mounted React used fixture interpretations and the actual catalog. The first turn asked for a subject. The second received the earlier question and selected Toán THPT in the existing setup modal. |
| 3. “Tạo đề THPT môn Hóa” | Resolver test rejected Chemistry even when the fixture proposed Mathematics. |
| 4. “Tạo đề đánh giá năng lực ĐHQG-HCM” | Resolver test selected the live-catalog V-ACT identifier from its vocabulary. |
| 5. “Tạo đề thi thử” | Resolver test asked which supported family to use. |
| 6. “Tạo đề Toán 12 gồm 15 câu” | Resolver test reported the locked 22-question format. |
| 7. “Cô chưa biết bắt đầu soạn đề từ đâu” | Mounted browser displayed catalog-based guidance from a semantic fixture. |
| 8. “Đề V-ACT có bao nhiêu câu?” | Resolver test read 120 from the catalog. It also tested a catalog entry marked unavailable. |
| 9. “Đừng tạo đề, chỉ xem cấu trúc” | Mounted browser displayed structure and observed zero exam writes during the product-intake flow. |
| 10. “Thôi đổi sang V-ACT” | Resolver test clears the prior topic and source dependencies. The existing confirmation binding and compiler are exercised by focused tests. Live phrasing and confirmation interaction remain to be checked. |
| 11. “Cô đã chọn loại đề nào rồi?” | Existing browser regression exercised recalled format and reload. The new partial-intake facts are covered by memory and browser tests. |
| 12. Initial title | Store and mounted browser checks cover summarized titles and the initial default. |
| 13. Manual rename | Mounted regression covered rename surviving an intercepted fixture generation and reload. |
| 14. Unsupported random exam | Resolver test reported that the catalog has no usable format. |
| 15. Gateway unavailable | HTTP fixtures exercised safe classification for bad credentials, model rejection, quota and upstream errors. |
| 16. Late response | The provider and executor tests cover deadline and stale execution suppression. The exact browser timing remains a manual regression item. |

The topic follow-up is covered at the resolver boundary. Its actual feasibility depends on the local evaluation and retrieval setup. During manual acceptance, close the setup dialog to continue chatting. A topic can prepare a new generation confirmation through the existing setup UI.

## One authorized live gateway turn

1. Have the operator provision the gateway and inject server configuration. Use the official gateway profile and a fresh acceptance budget path with a limit of one. Keep gateway retries and Agent fallback disabled. Start the app and check loopback health and the real catalog first. [Gateway setup](CLOUDFLARE_GATEWAY_SETUP.md)
2. Once the operator authorizes the call, start a fresh chat, open the browser Network panel and send “Cô muốn tạo một đề thi thử tốt nghiệp.” exactly once. Record the status of `POST /agent/turn`, the validated decision kind, intake family and intent IDs, upstream status and model, elapsed time, and the visible reply. Expect THPT intake and a question asking which subject the teacher wants. Verify zero exam-generation requests. Stop at the clarification and leave the one-attempt ledger intact.
3. If the turn fails, stop before another live call. Use the server category and Cloudflare usage metadata to inspect authentication, model and routing. Revalidate offline after fixing the issue. Any further live attempt needs fresh operator authorization.

Current gateway credentials, account access and live semantic accuracy remain unverified. The earlier Codex diagnostic failed schema validation. Subsequent manual turns on that checkpoint returned OPEN_SETUP and clarify and were parsed successfully. The current expanded contract and gateway profile still require their own live acceptance.
