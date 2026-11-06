# Evaluation protocol (prepared before generation)

- Only a run ending DONE is eligible. Verify captured PLAN_SYNTHESIS and composer requests in both arms before interpreting differences.
- Primary descriptive endpoint: mean blind per-slot quality score (1–5), paired deltas B1−A1 and B2−A2; compare each with absolute A1−A2. Also report counts of independently judged separating slots and wrong/unverified mathematics. No statistical significance claim with n=2.
- Random opaque paper codes; separate mapping file and no arm labels, source names, part markers, comments or LECTURING tags in grader payload. Preserve mathematical notation and shared stimuli. Mapping never included in grader prompt or accessible through tools (grader instructed to return text only).
- Same grader model for all five papers. Existing held-out source answer JSON is a supplied key, not independent validation; solve again.
- Report by-part metrics by joining blind IDs to separate address mapping after grading. Slot identity is (part, index, sub).
- Longest-option share counts ties explicitly; report strict longest and ties separately. Length uses normalized plain mathematical text; ratio = longest/mean across offered options. No options means not applicable.
- Repetition and source similarity are descriptive diagnostics, not content gates. Similarity max per question over p01–p09 only, never held-out. Literal overlap does not alone establish copying.
- Extraction has no access to image bytes. Grading must mark questions needing unavailable figures unverified.
