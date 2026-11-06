# AGENTS.md - ASTRA (team Trial and Success)

Single source of truth for rules in this repo, for people and for AI agents (Claude Code, Codex, Cursor, Copilot...). `CLAUDE.md` only points here; do not add rules there.

> **Status: draft v0, proposed by Huy (2026-10-23). It becomes the team's rule once every member has read it and agreed in the group chat.** Lines marked **DECIDE** are open for the team. Change this file only through a PR that the whole team has seen.

Project: ASTRA, a multi-agent system that generates and verifies exams (CSC10014 Computational Thinking, HCMUS/APCS). Seven members work in this repo at the same time, so the Git rules come first. Background: [ASTRA_Trial_and_Success_Report.md](ASTRA_Trial_and_Success_Report.md). Plan for the first build: [docs/mvp-plan.md](docs/mvp-plan.md).

## Tier 0 - read before doing anything (fits one screen)

1. **Never commit or push to `main`.** One task = one branch = one pull request. `main` always holds something that runs, because a broken `main` blocks seven people.
2. **Branch name: `<type>/<member>/<topic>`**, lowercase ASCII, no spaces, topic at most 40 characters. `<type>` is `feat`, `fix`, `docs`, `chore`, `spike` (try and discard, no PR). `<member>` is your GitHub username. Example: `docs/huy/agents-and-mvp-plan`. Always cut from the latest `origin/main`.
3. **Fetch before you start and before you say anything about repo state:** `git fetch --all`. A local branch is not evidence of what the team has; check `git rev-list --left-right --count main...origin/main`.
4. **Open a PR and stop.** You may merge your own PR only after **one approval from a different member** and only when it is up to date with `main`. Squash merge, so each PR is one commit that `git revert` can undo. **DECIDE:** who breaks ties and who may merge when the reviewer is slow (suggestion: the Leader, Huy). GitHub's free plan cannot block a push to `main`, so this rule depends on each of us.
5. **Never rewrite shared history.** No force-push to `main` or to a branch someone else has pulled; no rebase of a pushed branch. To bring `main` into your branch use `git merge origin/main`.
6. **Destructive Git needs confirmation:** `reset --hard`, `clean`, `checkout -- <file>`, `rebase`, `stash drop`, `branch -D`, `push --force`. First run `git status` and `git log`, say what will be lost, and commit unfinished work (a commit can be undone; a discard cannot). Never use `stash` to hold work overnight.
7. **Commit small and often:** after every finished step and at least every 30 minutes. Message `<type>(<scope>): <imperative summary, at most 72 characters>`, for example `feat(gate): reject papers whose section totals differ`. Types: `feat fix docs refactor test chore ci revert wip`. Scope is the part you touched: `docs mas rag gate api web data eval repo`. Add files by name, not `git add -A`.
8. **No secrets, no real data in Git.** API keys live in `.env` (ignored); commit `.env.example` with names only. Do not commit copyrighted exam papers, student data, `.db` files, build output, virtual environments or `.DS_Store`. Reference material enters the project only through the approved list in [docs/mvp-plan.md](docs/mvp-plan.md#6-feeding-approved-references-images-and-other-data).
9. **Log every AI session.** One line in `agent-log/<member>.log` with `tools/agent-log.sh`, and the AI declaration the course asks for stays true. The AI never invents results; targets (95% accuracy, VND 2,000 per exam) are goals until a recorded run says otherwise.
10. **"Done" means observed.** It runs from its real entry point, you watched it run, and the PR says what you ran. Say "build only" or "not run" when that is all that happened.
11. **Read before you edit, and edit with targeted changes.** Never overwrite a file you have not read or that is another member's, without telling them in the PR.
12. **Decisions are written down.** When the team settles a question from `docs/mvp-plan.md` section 10, add a numbered entry to `docs/DECISIONS.md` (append only) in the same PR that acts on it.

## Tier 2A - Git and pull requests in detail

### Life of a task

```bash
git fetch --all
git switch -c feat/<member>/<topic> origin/main   # cut from latest main
# work, commit small, push your branch as backup
git push -u origin feat/<member>/<topic>
# open PR (template fills in), ask a reviewer, wait, fix review comments with new commits
# after one approval and a green check: squash merge, then delete the branch
git switch main && git pull --ff-only && git branch -d feat/<member>/<topic>
```

After a squash merge `git branch -d` refuses, because the commits are not literally in `main`. Check the PR shows MERGED, then `git branch -D` and note it. An unmerged branch is work in progress, not litter.

### Naming

| Thing | Form | Example |
| :--- | :--- | :--- |
| Branch | `<type>/<member>/<topic>` | `feat/long/blueprint-schema` |
| Commit and PR title | `<type>(<scope>): <summary>` | `docs(mas): describe guardrail gate` |
| Git username | never changes during the course | `ndmhuy` |
| AI log | `agent-log/<member>.log` | `agent-log/huy.log` |
| Decision | `D-001`, `D-002`, ... in `docs/DECISIONS.md` | |
| Snapshot for a course deadline | tag `submit/<week>` | `submit/w03` |

### Pull requests

- Size: about 300 to 400 changed lines, not counting generated files. Bigger means split it, because reviewers read carefully only up to that much.
- Title follows the commit form, because squash merge uses it as the commit. No `wip` on `main`.
- Fill in the template: what changed, why, what you ran, which AI tool helped and what you checked yourself.
- Review, in this order: does it do what the PR says; does it follow this file; can you run it; are there secrets or real data; is the AI part declared. Leave comments that name a file and line.
- One task per PR. A second problem you find becomes an issue, not an extra commit.

### Conflicts

- Resolve by merging `origin/main` into your branch and reading both sides. Never take "ours" or "theirs" for a whole file you did not write.
- Append-only files (`agent-log/*.log`, `docs/DECISIONS.md`) resolve by **union**: keep every entry from both sides, sorted by time.
- If you are unsure, stop and ask the author of the other change before pushing.

### Several agent sessions on one machine

Switching branches in one folder mixes unfinished work. Use one worktree per session, next to the repo, never in `/tmp`:

```bash
git worktree add -b feat/<member>/<topic> ../ASTRA.worktrees/<member>-<topic> origin/main
```

Put `DO_NOT_DELETE.txt` in the worktree root before editing, with five lines: `LIVE WORK - DO NOT DELETE`, the session owner, the branch, the time, and `Ask the owner before deleting this folder`. It is git-ignored. Cleanup skips any folder containing it, deletes only explicit paths you have listed, never uses a glob, and uses `git worktree remove <path>` then `git branch -d`.

## Tier 2B - AI use in this repo

- Allowed with conditions (the course's AI Usage Guidelines): look things up and cross-check, code suggestions you understand and test, structure and grammar help declared in the Appendix, small test data you validate.
- Prohibited: fake results, analysis without real results, untested AI code, text paraphrased without citation. Undeclared AI use is a violation; a second one means zero for the course.
- The group already declared ChatGPT for the report ([declaration](ASTRA_Trial_and_Success_AI_Usage_Declaration.md)). Anyone using another tool for the project adds a line to their `agent-log` and to the PR.
- The AI may read and propose; the member reads every line it wrote before pushing and can explain it.
- Commits made with AI help keep the `Co-Authored-By` trailer the tool adds; do not remove it.
- Never paste real exam papers, API keys or student information into a prompt.

### Log line format

`tools/agent-log.sh "<task>" "<prompt summary>" "<summary>" "<verified: command and result | build only | not run>"` appends:
`[time] Member / Branch / Task / Prompt / Files Modified / Summary / Verified / Uncommitted / Git Fingerprint: <sha before> -> <sha after>`. A field you cannot answer is written `n/a (reason)`, never left out. An optimistic entry is worse than none, because it stops the next person from looking again.

## Tier 2C - Engineering rules (provisional until the stack is decided)

The stack is not fixed yet (see [docs/mvp-plan.md](docs/mvp-plan.md) section 3). These hold whatever we choose:

- **The contract is data.** Every message between stages is structured, versioned (`schema_version`) and validated at the boundary. One place defines each schema; other files import it and never restate it.
- **Deterministic checks are code, not prompts.** Item counts, section totals, option labels, score sums, time budget and output schema are checked by functions with tests.
- **The Blind Solver never sees the Writer's key.** A test must fail if the key reaches the solver's input.
- **Numbers come from versioned configuration** (blueprint, scoring profile, retry limits, budgets), never literals in agent code.
- **Every question carries provenance:** the source ids it used, the model that wrote it, and its validation status.
- **Retries are bounded.** After the limit the item goes to the teacher with the reason; it does not loop.
- **A teacher approves before anything is exported.** Automation prepares; a person publishes.
- **Fix the root cause.** Do not swallow exceptions, comment out assertions or return fake values so a test passes. A failing old test: decide whether the test or the code is wrong, then rewrite the test to state the new truth; do not delete or loosen it.
- Pin the language version and list dependencies in `requirements.txt` (or the lock file of the chosen tool). One command (`scripts/verify.sh`, to be added) runs build, lint and tests; run it before every push.

## Tier 2D - Documents

- Markdown is the source for team documents under `docs/`. Link to files instead of copying their text. State in the first screen what the document is and who it is for.
- Lab reports for the course are separate: they live in each member's personal lab repo, not here.
- Do not hand-edit generated files. Superseded documents move to `docs/archive/` with the date in the name; never delete them.

## When editing this file

Structure: Tier 0 (rules, one screen) then Tier 2 (details). A new rule adds one line to Tier 0 with its reason; detail goes to Tier 2. Propose a new rule in its own PR and name the incident it would have prevented. Adapted from the DTT and Lecturing rule files of Huy's earlier projects.
