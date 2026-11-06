# Prompt cho Codex: xử lí dữ liệu đề, rà prototype và ma trận mặc định

Dán toàn bộ phần dưới đường kẻ vào Codex.

---

You are processing the exam data of the Lecturing app, an exam generator for Vietnamese teachers. Reply to the owner in Vietnamese, in plain short reports. Read this whole brief first. Work through the stages in order, and commit after each finished stage and at least every 30 minutes.

## Why

Teachers say generated papers lack hard, high-discrimination questions: multi-step calculation, real situations, combined thinking. Three concrete cases:
- Toán: the default matrix has no probability in Part III, though 9 of 10 papers extracted so far do.
- Sinh học: papers are heavy on genetics and miss harder thinking questions from real papers, such as regulation mechanisms. A keyword count, rough only: prototype 19 of 28 questions on genetics, official 2026 12 of 29. The default topics are three genetics chapters plus evolution and ecology, with no physiology, while official 2026 Câu 7 is about homeostasis.
- Lịch sử: in one generated paper the key was the longest option in 22 of 24 multiple-choice questions, against 8 of 24 in the official 2026 paper.

The owner's direction: derive what is asked and how it is built from real papers, official papers first. No code gate that blocks questions; the fix must stay generic so that a new subject needs papers, not rules. The owner's position on distractors: **every wrong option must come from a mistake or confusion students really make.** Audit against that.

## Where things are

- Your repo for all writes: worktree `~/Lecturing_Lab/wt-corpus-merged`, branch `data/merged-20261102`. Registry: `registry/README.md`, `registry/papers.csv`, `registry/build.py`. Read the corpus `README.md` first; the first line convention of transcriptions and the rights note apply.
- Earlier OCR format: read several `transcriptions/*/*/STATUS.md`, `structure.json`, `key.json`, and `docs/ocr-provincial/HANDOFF.md`.
- Finished profile method: `~/Lecturing_Lab/agent-review/TOAN-PROFILE-1102/` (`prompts/EXTRACT.txt`, `prompts/AGGREGATE.txt`, `aggregate.py`, `verify_profile.py`, `outputs/profile.compact.json`, `REPORT.md`).
- Product code, READ ONLY: `~/Lecturing_Lab/wt-agent-runner/Grading_Tools`. Default matrices: `exam_formats/default_matrices.py`. Formats: `exam_formats/thptqg_2026.py`. Prototypes: `docs/prototypes/<subject>/`.
- Sample matrices, reference only: `~/Lecturing_Lab/wt-agent-runner/docs/mas-cloud/matrix-samples/`, and `~/Lecturing_Source/docs/release/next/matrix-samples-v3/toan/matrix-thuc-toan.md`. The writing rules: `~/Lecturing_Source/docs/release/next/matrix-writing-rules.md`.

## Hard limits

- Write only in the corpus worktree above, on that branch. No merge into corpus `main`. No push anywhere.
- Do not edit or commit in any product checkout. Default matrices and prototypes in the product are audited and proposed, never changed.
- No paid API or billed key. Use your Codex subscription.
- `provincial-toan-unverified/` is app-made and is never evidence. Anything this app generated is never evidence, prototypes included.
- `*-reference` papers are for format only, never content or frequency evidence.
- Keep evidence classes apart: official sets the difficulty bar; provincial shows topics and forms and may run harder than official. Never mix them in one count.
- Papers are private internal evidence. Reports and profiles must not contain a paper's sentences, numbers or named situations, apart from one very short quote per report.
- Delete nothing except files you created. Skip any folder holding `DO_NOT_DELETE.txt`. No wildcard deletes. Do not run the app's full test suite, and do not open the app's old UI.
- If a step fails twice for the same cause, stop that step, record it, and move to the next stage that does not depend on it.
- Never guess. A page you cannot read is marked unreadable. A subject with no real paper is reported as a gap.

## Stage 1: transcribe papers

Using the existing OCR format, second pass included:

1. At least 5 provincial papers each for Hóa học, Sinh học, Lịch sử, Địa lí, from `official/2026-provincial-*`, with their keys. Choose varied provinces; note why any is skipped.
2. More Toán provincial papers from `official/2026-provincial-toan`, up to 20 in total, because the registry notes 20 papers before any default-change recommendation.
3. Official papers that are stubs or absent: Lịch sử, Sinh học, GDKT&PL 2025 and Vật lí 2026 are stopped for missing pages. Toán, Vật lí, Hóa 2025 exist as scans in `official/2025-web`. Transcribe what is complete and readable. Report precisely which pages are missing so the owner can find them.
4. Official 2026 Tiếng Nga, Nhật, Hàn from `official/2026-papers-extra`. Check each for complete pages. A photo from a social post counts as low-trust evidence; say so.

Afterwards rerun `registry/build.py`, fix its rows if needed (ignore non-subject rows such as `README.md`), and commit.

## Stage 2: build profiles

For each subject with at least 5 usable non-reference papers, run the same generic extract and aggregate with no subject-specific rules. Store under `profiles/<subject>/`: rows, `profile.compact.json`, and a one-page `NOTE.md`.

Add these to each profile, derived by code from the rows:
- A topic distribution per part, by grade, counted per distinct paper, separately for official and provincial. Show lớp 10 and 11 content explicitly.
- For high-discrimination rows: what they ask, reasoning steps, knowledge combined. Report official separately.
- Distractor construction: what share of wrong options reward an identifiable mistake, and what kinds of mistake.
- How memorised facts such as dates are used.

Verify as in `verify_profile.py`: refs resolve, no reference paper in the input, no copied text or numbers. Subjects under 5 papers get a NOTE saying so and no frequency claim. Keep one extraction model per subject, and record it.

## Stage 3: audit the default matrices

For each THPTQG subject with data, compare the default topics in `default_matrices.py`, part by part, with the real distributions. Toán's matrix was placed by hand by the owner on 2026-10-30, so show the evidence and let the owner decide.

Write `audit/default-matrices.md`: one section per subject with a table of topic, default count, official papers with it, provincial papers with it. List topics missing from the default, including lớp 10 and 11, and topics over-weighted. Check specifically: Toán Part III probability; Sinh học genetics weight and missing physiology or regulation; history topics outside lớp 12. End each subject with a concrete proposed part-by-part topic list as data in `audit/proposed-matrices.json`, with evidence counts per topic, in the existing `_PART_TOPICS` shape. This is a proposal only. Mark subjects with thin evidence "chưa đủ bằng chứng" and propose nothing for them.

## Stage 4: audit all prototypes

For every paper in the product's `docs/prototypes/`, plus `prototypes/` in the corpus, grade question by question against the subject's profile and the official paper. Grade blind to the app's level tags where possible. Record:
- topic coverage compared with the real distribution
- for every multiple-choice question, per wrong option: which mistake it rewards, or "không rõ lỗi" when it is merely absurd or eliminable from wording
- key is the longest option; extreme words only in wrong options; option length imbalance
- true/false statements: is the falsehood a real misconception or an obvious exaggeration?
- correctness: solve independently; flag wrong keys and historical or scientific errors, marked as needing a teacher
- questions labelled Vận dụng that are in fact routine; count of truly high-discrimination questions against the official paper
- direct recall such as asking for a year, where the real paper would give the year as a cue

Code computes what it can; the model judges the rest. Write `audit/prototypes/<subject>.md` and a summary `audit/prototypes/SUMMARY.md` ranked worst first, with counts, and at most three concrete fixes per subject. Do not rewrite any prototype in this stage.

## Stage 5: new prototypes for Tiếng Nga, Nhật, Hàn

Tiếng Trung has no paper: do not create it, and report that it is waiting on a paper from the owner.

For the other three, follow the existing prototypes' file set and format (`.tex`, `_Answers.json`, compiled PDF), the registered layout in `thptqg_2026.py`, and the real paper's form and difficulty. Write new content; never copy a passage or item. Follow the distractor rule above. Verify: layout match, key correct, independent re-solve, compile with the same LaTeX setup the existing prototypes use, and render pages to check the script (Cyrillic, kana and kanji, hangul) prints correctly. Put them under `prototypes/<subject>/` in the corpus with a NOTE of sources and doubts. Mark them "chờ giáo viên duyệt": nobody on this project reads these languages at exam level, so this is not approval.

## Report

Write `audit/REPORT.md` in Vietnamese:

1. **Kết luận** in 5 lines.
2. **Bảng dữ liệu** per subject: official and provincial papers usable before and after, missing pages, papers the owner still has to find.
3. **Ma trận mặc định:** what is wrong per subject, and the decisions awaiting the owner.
4. **Prototype:** the ranking, the worst findings. Is "phương án nhiễu theo lỗi thường gặp" met? Give the share per subject.
5. **Phân hoá:** what high-discrimination questions in real papers do per subject, usable as input for a later hard-question design step.
6. **Giới hạn:** models used, what was only judged by a model, small samples, third-party copies, anything skipped or failed.
7. **Việc chủ app cần làm.**

List absolute paths to prompts, test cases and real outputs so the owner can review all three. Tell the owner the report's full path and how to open it. Say plainly what failed, was skipped or is unverified.
