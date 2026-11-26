# ASTRA Agent V2 acceptance results

For ASTRA reviewers. Each ID refers to the corresponding case in the supplied acceptance specification. Baseline was `7523c79556a9935df5008c92043f1e38d6e5d2a2`. The exercised application code is pinned to `fbc951bade177dcea0d6e19079d17238dcd5b495`. Fixtures use disposable browser storage, generated session and job IDs, and a synthetic exam. Browser tests assert visible state, actual route effects, and intercepted request counts. Their job, edit, preview, approval and download responses are simulated. The catalog and evaluate requests run through the native FastAPI implementation.

Evidence counts for current cases: 20 REAL_UI_FIXTURE, 37 UNIT, 21 PARTIAL, 10 STATIC, 2 BLOCKED_EXTERNAL.

Commands used for the observations include `npm.cmd test`, `python -m pytest -q`, `python scripts/agent_browser_smoke.py`, and the local routing measurement `node --experimental-strip-types scripts/agent-benchmark.mjs` from the frontend. [Browser setup and operator test](DEPLOY_RUNBOOK.md)

| Case | Observed or outstanding | Status |
| --- | --- | --- |
| A01 | Browser greeting; no modal or Agent HTTP. | REAL_UI_FIXTURE |
| A02 | Fixture OPEN_SETUP mounted the actual dialog. | REAL_UI_FIXTURE |
| A03 | Accentless recent intent and deterministic created-at order in App; browser exercised named open. | UNIT |
| A04 | Exact correction targets B; all other negated plans fail closed. | UNIT |
| A05 | Hypothetical help branch. | UNIT |
| A06 | Question about capability resolves to help. | UNIT |
| A07 | Teacher comment rejected as an action. | UNIT |
| A08 | Stable target resolver asks for question and part. Exact paraphrase with live interpreter unverified. | PARTIAL |
| A09 | Mounted list/shrink chain, named workspace open and answer focus verified independently. | PARTIAL |
| A10 | Local weather redirect. | STATIC |
| A11 | Accentless, mixed command corpus and guard fixtures. Live semantics unverified. | PARTIAL |
| A12 | Blank, C0/Unicode control, repeated noise, 4001 chars and oversized HTTP body tested. | UNIT |
| A13 | Replay uses same ID and identical fingerprint; conflicting reuse returns 409. | UNIT |
| A14 | Burst and 12/min IP quota return 429 with Retry-After; local process scope. | UNIT |
| A15 | Quoted and bypass directives fail closed. | UNIT |
| A16 | Invented action and extra transport arguments rejected. | UNIT |
| A17 | Success prose in model response violates the transport contract. | UNIT |
| A18 | Offline unsupported patterns and absent product paths. Browser JSON export exercised. | PARTIAL |
| A19 | Approval and export report current prerequisites. | REAL_UI_FIXTURE |
| A20 | Failure stops dependent tail; no third dispatch. | UNIT |
| B01 | Workspace creation uses current ExamSessions.create. Landing greeting uses one workspace. | STATIC |
| B02 | Mounted wide-screen sidebar collapsed via multi-step plan; mobile gate source only. | REAL_UI_FIXTURE |
| B03 | Unique title open observed after reload. Duplicate disambiguation is source-checked. | PARTIAL |
| B04 | Actual catalog selection of V-ACT, expanded sections and 120/150 in mounted setup. | REAL_UI_FIXTURE |
| B05 | 22/90 lock conflict shown without a start. | REAL_UI_FIXTURE |
| B06 | Current catalog drives grouped format clarification. | STATIC |
| B07 | Escape closes mounted setup. Stale-bound executor unit check; delayed catalog case not run. | PARTIAL |
| B08 | Unit verified topic-only payload. Mounted THPT evaluated a standard prompt with real API. | PARTIAL |
| B09 | Random request takes unsupported local route. | UNIT |
| B10 | Select V-ACT and cancel summary before THPT selection verified; exact interleaving untested. | PARTIAL |
| B11 | Mounted confirmation sent one request; store duplicate start test, simultaneous keyboard and chat case untested. | PARTIAL |
| B12 | Exact confirmations require current pending action. | STATIC |
| B13 | Token binding and stale executor tests; exact form-edit-and-confirm browser race untested. | PARTIAL |
| B14 | Existing manual template button selected V-ACT and submitted to the test fixture. | REAL_UI_FIXTURE |
| B15 | Existing network-error retry reuses the idempotency key; Agent refuses mismatched payload. | UNIT |
| B16 | Files and web flags are explained and omitted from generation. | STATIC |
| C01 | Mounted composer accepted status while job fixture was active. Last known progress shown. | REAL_UI_FIXTURE |
| C02 | Note recorded while job active with no revision request. | REAL_UI_FIXTURE |
| C03 | Cancel and replace same question note observed. | REAL_UI_FIXTURE |
| C04 | Existing same-instance active job duplicate guard. Local cross-tab Web Locks added. | UNIT |
| C05 | Terminal fixture triggered review notice and the resolved note awaited review. | REAL_UI_FIXTURE |
| C06 | Job failure retains job-bound unresolved note. | STATIC |
| C07 | Sequential controller and per-note outcomes implemented. Mid-batch failure unverified. | PARTIAL |
| C08 | Repeated display number without part is ambiguous; stale revision fails resolution. V-ACT browser question targeting unverified. | UNIT |
| C09 | Verify uses native one-question API and reports observed answerCheck. Confirmed mutation not exercised in browser. | PARTIAL |
| C10 | Agent prefilled a draft, teacher saved it, fixture advanced revision, and export was blocked. | REAL_UI_FIXTURE |
| C11 | Existing API tests enforce optimistic revision across requests to one process. | UNIT |
| C12 | Agent opened PDF in browser. Pending and failed preview states supported but not exercised in browser. | PARTIAL |
| C13 | Existing preview tests cover compiler failure and recovery. | UNIT |
| C14 | Agent opening ready preview did not unlock approval; teacher UI action and separate confirmation did. | REAL_UI_FIXTURE |
| C15 | Post-edit export blocked on new unapproved revision. | REAL_UI_FIXTURE |
| C16 | JSON download event observed. PDF/TEX bindings and gates checked in source; those browser downloads unverified. | PARTIAL |
| C17 | Agent delete blocks a currently active job. | STATIC |
| C18 | Pending action cancellation does not invoke a business endpoint. | STATIC |
| C19 | A lost start receipt reuses idempotency key in the store. | UNIT |
| C20 | Existing jobs finishing out of order update origin session; stale interpretation dispatch refused. | UNIT |
| C21 | Monotonic progress checks and terminal guard are implemented. SSE race not reproduced in browser. | PARTIAL |
| C22 | Existing API storage tests cover interrupted-job behavior. Reload never auto-starts a job. | UNIT |
| C23 | Unknown edit outcome retained; no automatic retry. Timeout reconciliation scenario untested. | PARTIAL |
| C24 | Main warnings retained. Question mismatch behavior covered by existing API tests; chat warning narration source-checked. | PARTIAL |
| D01 | Greeting leaves title default; meaningful goal creates deterministic title. | UNIT |
| D02 | Conversational rename and reload observed. | REAL_UI_FIXTURE |
| D03 | Manual conversation title survived completed exam package. | REAL_UI_FIXTURE |
| D04 | Legacy store restored and then persisted without replacing transcript. | UNIT |
| D05 | Reload, title open, and recent format recall from linked message. | REAL_UI_FIXTURE |
| D06 | Latest selection replaces prior intake and old pending action. Exact correction wording and history recall not exercised. | PARTIAL |
| D07 | Recall reads the original message. Exact quote scenario not run in browser. | STATIC |
| D08 | Opened a saved conversation by title after browser reload. | REAL_UI_FIXTURE |
| D09 | Retract drops dependent intake and preserves job state; user-facing message source-checked. | UNIT |
| D10 | Branch copies prefix and clears operation/job bindings. | UNIT |
| D11 | Stale dispatch rejects outdated context and manual lifecycle aborts current turn. Delayed interpreter case untested in browser. | PARTIAL |
| D12 | Malformed store preservation unit tested; quota and separate account/session isolation have partial or missing coverage. | PARTIAL |
| D13 | Bounded latest plus lexical older context and source-linked facts. | UNIT |
| D14 | No authenticated multi-user title access. Explicit cross-person requests receive a local-scope answer. | BLOCKED_EXTERNAL |
| E01 | Status command changed the chat while job active, with no Agent transport. Standalone timing harness measured local route only. | REAL_UI_FIXTURE |
| E02 | Natural paraphrase traveled via local HTTP to a semantic fixture and actual UI handler. Live intent unverified. | REAL_UI_FIXTURE |
| E03 | Only one injected fallback, explicit quota reserve. | UNIT |
| E04 | Cancellation-resistant primary could not replace the fallback result. | UNIT |
| E05 | Configuration, 401/403/schema/quota never trigger fallback. | UNIT |
| E06 | 429 and Retry-After respected; cooldown checked. | UNIT |
| E07 | Attempt budget is charged before provider request. Cancellation discards late result. | UNIT |
| E08 | Scanned built assets for direct provider URLs and gateway authorization/configuration markers. | STATIC |
| E09 | Cloudflare auth header wire fixture; non-loopback and incoming credential headers rejected by configured turn route. | UNIT |
| E10 | Wire fixtures assert no provider key header or token in body. Repository checker scans tracked candidates. | UNIT |
| E11 | Strict schema and fixed upstream endpoint; invalid model path and incoming auth header rejected. | UNIT |
| E12 | Web Locks/storage checks for same-origin browser. Backend lacks atomic workspace ownership across devices. | PARTIAL |
| E13 | Default budget zero; SQLite attempts correctly exhausted and persisted. | UNIT |
| E14 | Bounded transport timeout and late plan suppression via fixture. | UNIT |
| E15 | Existing backend persistence/restart tests ran. Local native startup checked. | UNIT |
| E16 | Operator provisioning and authorized live requests remain pending. | BLOCKED_EXTERNAL |

## Historical regression pool

V-ACT is available in the current catalog. Its old absence expectation was updated in B04. Linked rows show related current evidence. Historical wording and setups were not directly re-run. Item-bank and random assembly cases require a separate product contract.

| Historical case | Current evidence or dependency | Status |
| --- | --- | --- |
| NL01 | Current A02 | PARTIAL |
| NL02 | Current A08 | PARTIAL |
| NL03 | Current A03 | PARTIAL |
| NL04 | Current A09 | PARTIAL |
| NL05 | Current A04 | PARTIAL |
| NL06 | Current A07 | PARTIAL |
| NL07 | Current C08 | PARTIAL |
| NL08 | Current D05 | PARTIAL |
| NL09 | Current A09 | PARTIAL |
| NL10 | Current A12 | PARTIAL |
| NL11 | Current D11 | PARTIAL |
| NL12 | Current D06 | PARTIAL |
| IN01 | Current B08 | PARTIAL |
| IN02 | Current B04 | PARTIAL |
| IN03 | Current B05 | PARTIAL |
| IN04 | Current B09 | PARTIAL |
| IN05 | Historical setup has no direct recorded run | NOT_VERIFIED |
| IN06 | Historical setup has no direct recorded run | NOT_VERIFIED |
| IN07 | Historical setup has no direct recorded run | NOT_VERIFIED |
| IN08 | Historical setup has no direct recorded run | NOT_VERIFIED |
| IN09 | Historical setup has no direct recorded run | NOT_VERIFIED |
| IN10 | Current B13 | PARTIAL |
| IN11 | Current B11 | PARTIAL |
| IN12 | Current B12 | PARTIAL |
| IN13 | Historical setup has no direct recorded run | NOT_VERIFIED |
| IN14 | Historical setup has no direct recorded run | NOT_VERIFIED |
| SRC01 | Item-bank or random assembly contract | BLOCKED_EXTERNAL |
| SRC02 | Item-bank or random assembly contract | BLOCKED_EXTERNAL |
| SRC03 | Item-bank or random assembly contract | BLOCKED_EXTERNAL |
| SRC04 | Item-bank or random assembly contract | BLOCKED_EXTERNAL |
| SRC05 | Item-bank or random assembly contract | BLOCKED_EXTERNAL |
| SRC06 | Item-bank or random assembly contract | BLOCKED_EXTERNAL |
| SRC07 | Item-bank or random assembly contract | BLOCKED_EXTERNAL |
| SRC08 | Item-bank or random assembly contract | BLOCKED_EXTERNAL |
| SRC09 | Item-bank or random assembly contract | BLOCKED_EXTERNAL |
| SRC10 | Item-bank or random assembly contract | BLOCKED_EXTERNAL |
| SRC11 | Item-bank or random assembly contract | BLOCKED_EXTERNAL |
| SRC12 | Item-bank or random assembly contract | BLOCKED_EXTERNAL |
| SRC13 | Item-bank or random assembly contract | BLOCKED_EXTERNAL |
| SRC14 | Item-bank or random assembly contract | BLOCKED_EXTERNAL |
| JOB01 | Current C01 | PARTIAL |
| JOB02 | Current C04 | PARTIAL |
| JOB03 | Current E12 | PARTIAL |
| JOB04 | Current D14 | PARTIAL |
| JOB05 | Current C22 | PARTIAL |
| JOB06 | Current C21 | PARTIAL |
| JOB07 | Current C21 | PARTIAL |
| JOB08 | Current E07 | PARTIAL |
| JOB09 | Current E15 | PARTIAL |
| JOB10 | Historical setup has no direct recorded run | NOT_VERIFIED |
| JOB11 | Historical setup has no direct recorded run | NOT_VERIFIED |
| JOB12 | Current E06 | PARTIAL |
| JOB13 | Current C01 | PARTIAL |
| JOB14 | Current E12 | PARTIAL |
| JOB15 | Historical setup has no direct recorded run | NOT_VERIFIED |
| JOB16 | Historical setup has no direct recorded run | NOT_VERIFIED |
| REV01 | Current C02 | PARTIAL |
| REV02 | Current C03 | PARTIAL |
| REV03 | Current C08 | PARTIAL |
| REV04 | Current C08 | PARTIAL |
| REV05 | Current C03 | PARTIAL |
| REV06 | Current C05 | PARTIAL |
| REV07 | Current B13 | PARTIAL |
| REV08 | Current C07 | PARTIAL |
| REV09 | Current C11 | PARTIAL |
| REV10 | Current C15 | PARTIAL |
| REV11 | Current C14 | PARTIAL |
| REV12 | Current C15 | PARTIAL |
| REV13 | Current C13 | PARTIAL |
| REV14 | Current C17 | PARTIAL |
| SAFE01 | Current B16 | PARTIAL |
| SAFE02 | Historical setup has no direct recorded run | NOT_VERIFIED |
| SAFE03 | Current A15 | PARTIAL |
| SAFE04 | Current A12 | PARTIAL |
| SAFE05 | Historical setup has no direct recorded run | NOT_VERIFIED |
| SAFE06 | Current D14 | PARTIAL |
| SAFE07 | Current E10 | PARTIAL |
| SAFE08 | Current A14 | PARTIAL |
| SAFE09 | Current A18 | PARTIAL |
| SAFE10 | Current A19 | PARTIAL |
| RND01 | Item-bank or random assembly contract | BLOCKED_EXTERNAL |
| RND02 | Item-bank or random assembly contract | BLOCKED_EXTERNAL |
| RND03 | Item-bank or random assembly contract | BLOCKED_EXTERNAL |
| RND04 | Item-bank or random assembly contract | BLOCKED_EXTERNAL |
| RND05 | Item-bank or random assembly contract | BLOCKED_EXTERNAL |
| RND06 | Item-bank or random assembly contract | BLOCKED_EXTERNAL |
| RND07 | Item-bank or random assembly contract | BLOCKED_EXTERNAL |
| RND08 | Item-bank or random assembly contract | BLOCKED_EXTERNAL |
| RND09 | Item-bank or random assembly contract | BLOCKED_EXTERNAL |
| RND10 | Item-bank or random assembly contract | BLOCKED_EXTERNAL |
