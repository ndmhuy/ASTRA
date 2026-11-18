# UI-First Agent Acceptance Results

Baseline: `8f12fbb2e9c7b6adb43b20b1966b256da6f45586`. Verdict terms follow `05_ACCEPTANCE_TEST_MATRIX.md`. `UNIT_ONLY` never implies browser or live-model success.

## A — UI actions

| ID | Result | Evidence / limitation |
|---|---|---|
| A01 | `REAL_UI_PASS` | Browser request `Mở màn hình soạn đề` created/opened a real workspace and displayed receipt-confirmed success |
| A02 | `UNIT_ONLY` | `ui.session.open` validates exact workspace ID and verifies resulting active workspace |
| A03 | `UNIT_ONLY` | Deterministic interpreter asks which workspace when multiple summaries match an ambiguous prior-exam reference |
| A04 | `UNSUPPORTED_EXPECTED` | No stable selected-question context; asks/declines rather than inventing a target |
| A05 | `UNSUPPORTED_EXPECTED` | `ui.question.focus` remains unavailable and non-callable |
| A06 | `UNSUPPORTED_EXPECTED` | Word request stops safely before any edit/export substitution |
| A07 | `REAL_UI_PASS` + limitation | Agent opened real setup/catalog; generation remains behind existing modal confirmation and was not clicked |
| A08 | `UNSUPPORTED_EXPECTED` | Agent deletion is not exposed; existing two-step manual UI remains available |
| A09 | `UNIT_ONLY` | Duplicate `actionId` returns cached receipt with `duplicate:true`; side effect count remains one |
| A10 | `UNIT_ONLY` | Mismatched `expectedStateVersion` returns `STALE_CONTEXT` without handler call |

## B — guided exam setup

| ID | Result | Evidence / limitation |
|---|---|---|
| B01 | `REAL_UI_PASS` | Natural request opened real Toán THPT setup modal |
| B02 | `REAL_UI_PASS` | Modal exposed only the real locked catalog; Agent does not invent a difficulty distribution |
| B03 | `UNSUPPORTED_EXPECTED` | V-ACT returns explicit unavailable response; no THPT substitution |
| B04 | `UNIT_ONLY` | Unsupported `20 câu` request falls back to clarification; UI catalog remains 22 |
| B05 | `UNIT_ONLY` | Correction to Lý does not mutate the Toán-only form; asks for clarification/current limitation |
| B06 | `UNIT_ONLY` | Existing `ExamSessions.generate` duplicate-start test remains green; Agent has no generate action |
| B07 | `UNSUPPORTED_EXPECTED` | Word unavailable; help lists PDF/LaTeX/JSON only |
| B08 | `UNIT_ONLY` | Existing UI error handling remains owner; Agent has no direct request constructor/backend call |

## C — generation-time chat and notes

| ID | Result | Evidence / limitation |
|---|---|---|
| C01 | `UNIT_ONLY` | Active-job fixture returns exact stage, percent and provenance with no ETA/per-question claim |
| C02 | `UNIT_ONLY` | `ui.note.add` stores UI-only pending note linked to workspace/job; no backend edit |
| C03 | `UNIT_ONLY` | Remark-like text produces clarification/no note |
| C04 | `UNIT_ONLY` | Store and executor cancel a matching pending note and observe `cancelled` state |
| C05 | `UNIT_ONLY` | Completion with pending notes adds review prompt and explicitly says not auto-applied |
| C06 | `UNSUPPORTED_EXPECTED` | No batch revision action; notes remain reviewable only |
| C07 | `UNIT_ONLY` | Composer no longer binds disabled state to `isGenerating`; duplicate generation guard remains tested |

## I — input and adversarial behavior

| ID | Result | Evidence / limitation |
|---|---|---|
| I01 | `UNIT_ONLY` | 4,001-character request fails request validation; 64 KiB HTTP body returns 413 before interpretation |
| I02 | `UNIT_ONLY` | Empty is blocked by UI/Pydantic; unrelated text clarifies and creates no action |
| I03 | `UNSUPPORTED_EXPECTED` | Attachment control is disabled; no file text enters Agent context or capability registry |
| I04 | `REAL_UI_PASS` | Browser accessibility tree showed attachment disabled and explicitly unsupported |
| I05 | `UNIT_ONLY` | Curated Vietnamese cases cover accented/no-accent forms; uncertain/typo-heavy text clarifies |
| I06 | `UNIT_ONLY` | `Đừng tạo đề, chỉ mở cấu hình` opens setup only; no generation action exists |
| I07 | `UNIT_ONLY` | Missing history action stops the whole dependent request; executor also skips later steps after failure |

## L — model/provider behavior

| ID | Result | Evidence / limitation |
|---|---|---|
| L01 | `REAL_UI_PASS` | Workspace action, setup and help worked with LLM disabled and no key |
| L02 | `UNIT_ONLY` | Fake 429/quota provider returns bounded fallback and no action |
| L03 | `UNIT_ONLY` | Fake `backend.deleteExam` is rejected by service allowlist and UI executor |
| L04 | `UNIT_ONLY` | Provider/parse errors fail through the same no-action fallback; no live malformed model response used |

## S — security and boundary

| ID | Result | Evidence / limitation |
|---|---|---|
| S01 | `REAL_UI_PASS` | Runtime logs show browser `/agent/*`; opening setup caused the React `/api/exam-formats` call. Static scan found no Agent business call |
| S02 | `REAL_UI_PASS` | Production Vite build passed; secret scan found no browser key marker or `VITE_*GEMINI` |
| S03 | `UNIT_ONLY` | Unknown capability is rejected and no roadmap/action is invented |

## K — application knowledge

| ID | Result | Evidence / limitation |
|---|---|---|
| K01 | `REAL_UI_PASS` | `ASTRA làm được gì?` returned verified registry descriptions; source status is registry-only |
| K02 | `UNIT_ONLY` | Word answer says unavailable and gives no invented roadmap |
| K03 | `UNIT_ONLY` | Unknown free text clarifies and does not execute |
| K04 | `UNIT_ONLY` | Explicitly synthetic approved JSON fixture loads with tracked version/baseline |
| K05 | `NOT_VERIFIED` | No official approved document exists; doc/UI planned-feature wording awaits the team artifact |
| K06 | `UNIT_ONLY` | Unapproved, stale/incompatible and corrupt synthetic fixtures fail; runtime stays registry-only |
| K07 | `REAL_UI_PASS` | Registry help worked with no Gemini key and no knowledge document |

## Offline language evaluation

The new curated safety set contains 24 Vietnamese requests not used as prompt examples: accents/no accents, negation, unsupported formats, V-ACT, upload/search, destructive requests, status, ambiguous/casual text and multi-step dependency failure. All 24 expected kind/capability assertions passed; unsafe invented actions were 0/24.

This is an implementation-authored offline candidate set, **not** an independently human-reviewed 100-case evaluation and not a live Gemini score. Therefore:

- deterministic expected-decision accuracy: 24/24 on this candidate set;
- false-positive unsafe action proposals: 0/24;
- live Gemini language accuracy: `NOT_VERIFIED`;
- independent teacher-authored evaluation: `BLOCKED_EXTERNAL` pending reviewers/data.

## Test inventory

- Frontend: 18 tests, including five executor/context/note cases plus completion review.
- Python: 31 Agent service cases, including 24 parametrized language cases; full repository total 406 tests plus 7 subtests.
- Real browser: workspace action, no-key help, and catalog-backed setup modal.
- Live Gemini/live generation: not run.
