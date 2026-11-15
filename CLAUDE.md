# CLAUDE.md

Rules for this repo live in [AGENTS.md](AGENTS.md), the single source of truth. Read its Tier 0 first. Do not add rules here.

Claude Code specifics:

- Create your branch (`<type>/<member>/<topic>`) before editing, commit small, push the branch, open a PR and stop. Never merge or push to `main`.
- Run `git fetch --all` before describing repo state.
- End each session with `tools/agent-log.sh` and put the AI-assistance section in the PR.
