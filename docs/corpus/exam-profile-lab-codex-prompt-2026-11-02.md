# Prompt cho Codex: chạy tiếp lab hồ sơ đề Toán

Dán toàn bộ phần dưới đường kẻ vào Codex.

---

You are continuing a paused research lab for the Lecturing app, an exam generator for Vietnamese teachers. Reply to the owner in Vietnamese. Prefer plain, short reports. Read this whole brief first.

## Goal

Teachers say the app's high-discrimination questions are not hard enough, and some questions look machine-written. Test this hypothesis: a profile derived from real papers (topics, constructions, distractor design, sources of difficulty), fed to planning and composing, measurably improves a generated Toán paper.

The owner's rules for the solution:
- No code gate that blocks questions. Metrics grade this experiment only.
- It must be generic across subjects: a new subject needs papers, not new rules or prompts.
- Report honestly, including a null or negative result.

Background: `/Users/huynguyen/Lecturing_Source/docs/release/next/exam-profile-lab-plan-2026-11-02.md`

## Where things are

- Lab folder (all your work and evidence): `~/Lecturing_Lab/agent-review/TOAN-PROFILE-1102/`
- `papers/`: `p01`..`p09` are 2026 provincial papers, used to build the profile. `HELDOUT_2026` is the official 2026 paper. It must never enter the profile.
- `extract/`: finished per-paper rows. Currently `p01`, `p02`, `p03`, `HELDOUT_2026`, made with `claude -p --model sonnet`.
- `prompts/`: `EXTRACT.txt`, `AGGREGATE.txt`, `PLAN_ADDENDUM.txt`, `COMPOSER_ADDENDUM.txt`
- `lib.py` (model call), `extract.py` (resumable), `aggregate.py`, `lab_arm.py` (one paper; arm `profile` monkeypatches the product), `run_arm.sh`, `run_all.sh`
- Product code, read only: `~/Lecturing_Lab/wt-agent-runner/Grading_Tools`, branch `claude/agent-runner`
- Python: `~/Lecturing_Source/.venv/bin/python3`

Only `hook_check.py` has exercised the monkeypatch. `lab_arm.py` and `aggregate.py` have never completed a run, so expect to debug them. Fix bugs in lab scripts only.

## Hard limits

- Do not edit, commit, merge or push anything in a product checkout or the corpus repo. All edits stay inside the lab folder.
- Do not use a paid API key or anything billed. Use only the owner's `claude -p` subscription or your own Codex CLI subscription.
- Do not delete anything outside `sb/`, and there only paths you listed first. Skip any folder holding `DO_NOT_DELETE.txt`. No wildcard deletes.
- Do not run the full test suite, and do not open the app's old UI.
- Papers are private internal evidence. Do not publish or upload them, and do not put their text in a report beyond one very short quote.
- If a required step fails twice for the same cause, stop and report it. Do not change the experiment's design to get a result.

## Step 1: choose the backend once

`claude -p` hit its weekly limit on 2026-11-02 and reopens at 22:00 ICT. Probe it with one short call.

- If it answers, keep `lib.py` as is and use `LECTURING_DEV_AI=claude-cli`, as `run_arm.sh` does.
- If it refuses, use Codex for everything: add a `codex exec` branch to `lib.py` (flags in the product's `exam_generator/agents/providers/cli.py`, profile `codex-cli`), and set `LECTURING_DEV_AI=codex-cli` in `run_arm.sh`.

**All four papers in Step 3 must use the same backend and model.** Record the backend and model of every step in `RUNLOG.md`. If Codex builds the profile and writes the papers, the result says whether the profile helps on that model, and says nothing about Haiku; state this in the report.

If you use Codex, re-extract nothing already done unless the rows are unusable, and record that 4 extractions came from Sonnet.

## Step 2: build the profile

```bash
cd ~/Lecturing_Lab/agent-review/TOAN-PROFILE-1102 && python3 extract.py
python3 aggregate.py
```

Check before continuing:
- 9 `extract/p*.json` files, each with one row per scored slot (expect 34).
- `aggregate.py` reads only `extract/p*.json`, so `HELDOUT_2026` stays out.
- `outputs/profile.compact.json` exists and `bad_refs_dropped` is small relative to total refs. Report the number.
- Profile fidelity: no pattern contains a concrete question, number or named situation from a paper. Check this by reading and with a similarity scan against `papers/p*.md`.

## Step 3: generate four papers

```bash
./run_arm.sh A1 base & ./run_arm.sh B1 profile & wait
./run_arm.sh A2 base & ./run_arm.sh B2 profile & wait
```

Each run writes `run-<tag>.log`, `outputs/run-<tag>/plan.json`, `outputs/run-<tag>/calls/*.json`; the paper is under `sb/<tag>/base/`.

Before trusting a B run, open its `calls/` files and confirm:
- The `PLAN_SYNTHESIS` call contains `exam_profile` and the addendum.
- The composer call contains the `exam_profile` block and the addendum.

Confirm A runs contain neither. If a B run lacks them, the comparison is invalid: fix and rerun.

A run counts only if it reaches `DONE`. Note fallback notices, for example `synthesis_unavailable`, in `RUNLOG.md`.

## Step 4: does the profile predict the held-out paper?

Without showing the grader which paper produced what, for each row of `extract/HELDOUT_2026.json` ask whether a pattern in `profile.compact.json` covers it: same topic, same construction, topic only, or none. Report coverage per part, and the fraction of high-discrimination rows covered.

## Step 5: blind grading

Write `grade.py`.

1. Convert A1, A2, B1, B2 and `HELDOUT_2026` to plain per-question text. Drop part markers, comments, `LECTURING-*` tags and anything naming the arm. Assign random codes, and keep the mapping in a file the grader never sees.
2. Run `extract.py`'s prompt on each generated paper, to get rows comparable with the held-out paper.
3. Blind-grade each paper, using a stronger model than the writer when one is available, and always the same model. For each question report: number of reasoning steps; can a student without the knowledge eliminate options from wording or length; is the question and answer mathematically correct (solve it independently); is it routine or non-routine; would it separate strong from average students; a score of 1 to 5.
4. Rank the papers by closeness to a real exam and explain why.

Code-computed metrics, per paper, by part:
- share of MCQ where the key is the longest option; ratio of longest to mean option length
- key letter distribution; true/false pattern
- mean reasoning steps; count of high-discrimination slots
- grade spread (10, 11, 12)
- pattern and topic repetition within the paper
- maximum similarity of each question to any `papers/p*.md` question, to catch copying
- wrong keys or wrong mathematics found in Step 5.3

## Step 6: report

Write `REPORT.md` in Vietnamese with this structure:

1. **Kết luận** in 3 lines: did B beat A in both runs, by how much, and is the difference larger than A1 vs A2?
2. **Bảng số liệu** for A1, A2, B1, B2 and the 2026 paper.
3. **Điểm nghẽn:** apply the table "Cách đọc kết quả" from the plan file, and say which layer is the bottleneck (data, composer path, model).
4. **Ví dụ:** 2 to 3 pairs of comparable questions from A and B, with the source of the difference. Generated questions only.
5. **Giới hạn:** sample size of two per arm, backend used, images not read during extraction, grader is a model and not a teacher, provincial papers may be harder than the official paper, and whatever else you observed.
6. **Đề xuất bước tiếp theo**, at most 3, and only what the evidence supports.

Also list in the report, with absolute paths: the prompts used, the test cases, and the real outputs, so the owner can review all three. Commit nothing. Tell the owner the report's full path and how to open it, and flag anything that failed, was skipped or is unverified.
