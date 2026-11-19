# Remaining capability gaps

The current change fixes the answer-view contract, catalog reload loop, focus mode regression and incomplete receipt handling, and exposes 31 of 32 inventoried executable UI families (96.9%). See `FULL_UI_CAPABILITY_INVENTORY.md` for the exact counting scope.

- Still manual: external PDF/log new-tab links (asynchronous popup permission cannot be guaranteed). Question and warning disclosures can be expanded as groups; individual disclosure targeting remains manual.
- Editor patch support is limited to the existing fields (stem, key, explanation, choices, statements); Backend remains the authoritative business validator. It does not synthesize missing generation capabilities.
- Availability hints currently cover major exam/setup/job prerequisites. Executor validation remains authoritative for all parameter-specific conditions.
- A failed/ambiguous plan stops; automatic Gemini replanning is not implemented.
- Full browser acceptance coverage is narrower than adapter coverage. Approval/export/save/delete still require additional fixture-controlled browser cases.
- No Backend cancellation handler, DOCX, V-ACT flow, web search or file upload exists in the reachable application. The Agent must explicitly report those as unsupported.
- The official Application Knowledge document remains absent and is not invented.

The implementation does not claim 100% capability completion or live language understanding verification. No live inference was spent in this task.
