# Gaps and Future Work

This list is limited to verified UI/integration gaps. It does not create Backend TODOs or imply that missing business features are committed roadmap items.

## Current unsupported or deliberately unexposed features

| Feature | Current evidence | Required before exposure |
|---|---|---|
| Agent starts generation | Setup's existing button directly calls `handleQuickStart`; no trusted Agent request-summary/hash approval component exists | Product-approved confirmation component and receipt contract that still invokes existing UI service only |
| Agent question edit/regenerate | Real UI editor exists, but conversational target selection and trusted confirmation are not wired | Stable selected question/context, exact revision/hash preconditions, confirmation and observed receipt |
| Agent preview/approve/export | Ordinary UI paths exist; they carry strict revision/hash/preview gates | Narrow UI adapters that preserve every current invariant; no model assertion as approval |
| Workspace deletion | Existing UI has two-step confirmation; Agent action is intentionally absent | Explicit typed destructive proposal plus a trusted UI confirmation surface |
| Question focus | No mounted persistent selected-question action/state | UI owner adds real focus handler and observed selected-question context |
| Word/DOCX | No current UI/service/catalog support | Independent product/backend delivery; do not map to TeX silently |
| V-ACT | No supported current UI flow/catalog option | Independent verified UI workflow; never route to THPT |
| Attachments | No upload/read/extraction path; control is now disabled | Approved storage, privacy/consent, extraction and untrusted-content policy |
| Web search | No execution/citation path; control is now disabled | Explicit search capability, source/citation UI and privacy policy |
| Batch revisions / undo | No mounted handlers | Independent UI/product implementation |
| Per-question generation stream | Real path exposes stage progress only | Backend/UI evidence before wording or context changes |
| Production deployment | Local service has no user identity/tenancy | Auth, authorization, TLS/reverse proxy, rate limits, audit policy and secret management |

## Gemini gaps

- SDK adapter is implemented and official model identity was checked, but the developer's project access, quota and billing/free-tier status were not tested.
- No live inference was run. `AGENT_LLM_ENABLED=false` remains the default.
- The current adapter performs one idempotent inference attempt with a 15-second timeout; it does not retry 429/5xx automatically, preventing retry storms. A future bounded retry policy should respect official `Retry-After` behavior and product latency targets.
- No independent teacher-authored language evaluation exists. The 24-case offline set is implementation-authored and cannot certify natural-language quality.
- Future teacher BYOK needs authenticated identity, encrypted server-side handling, revoke/forget, quota/privacy notices and cross-session isolation. Browser or LocalStorage key persistence is prohibited.

## Official ASTRA knowledge document: pending from team

Status remains `NOT_PROVIDED`. This implementation does not invent the missing file, FAQ, approval owner, version, roadmap or feature claims. Runtime help uses the verified capability manifest and labels its source `verified_ui_registry_only`.

Activation checklist when the team supplies the document:

1. Team names the exact repository/config path, format, approval owner, approval date and version.
2. Document declares compatible merged baseline/UI version and feature status evidence.
3. Configure the read-only `ApplicationKnowledgeSource`; do not crawl arbitrary files.
4. Enforce size, format, approval and compatibility validation before load.
5. Treat text as untrusted descriptive data, never commands or capability registration.
6. Reconcile every executable claim against the live UI registry. Documentation can explain but cannot enable an action.
7. Add tests for relevant retrieval, citations/version evidence, planned-but-not-callable mismatch, stale/corrupt/injected fallback and registry disagreement.
8. Product/UI owner reviews Vietnamese wording before changing source status to `approved_document`.

Synthetic fixture coverage currently proves approval, compatibility and malformed-input rejection only. It is explicitly not an official document.

## Test and quality gaps

- The required real browser interaction was performed manually through Windows accessibility/UI automation. A committed browser CI suite is still absent because the audited Python Playwright dependency was missing.
- Frontend build retains the existing >500 kB chunk warning.
- `npm ci` continues to report five high-severity dependency advisories from the existing Vite/tooling chain; this slice did not perform a breaking dependency upgrade.
- Repository-wide Ruff still contains pre-existing non-Agent debt; new Agent package/tests pass targeted Ruff.
- Starlette's existing TestClient/httpx deprecation warning remains in the full suite.
- LocalStorage retains chats, questions and note ledger. Production retention/privacy design is outside this local MVP.

## Next safe slices

1. Add a trusted setup-summary/approval adapter, then expose `exam.generate` through the existing UI handler only.
2. Add stable question selection and a confirmed single-question edit adapter preserving revision/hash checks.
3. Automate the successful browser trace and no-key/unsupported traces in CI.
4. Run an explicitly opted-in minimal Gemini smoke, then a separate independently reviewed Vietnamese evaluation.
5. Receive and activate the official knowledge document under the checklist above.

Business Backend core, RAG, provider generation, academic presets, database, preview compiler and export gates should remain unchanged for these UI integration slices.
