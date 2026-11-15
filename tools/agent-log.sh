#!/usr/bin/env bash
# Append one line to agent-log/<member>.log with branch, files and a Git Fingerprint (AGENTS.md rule 9).
# Usage: tools/agent-log.sh "<task>" "<prompt summary>" "<summary>" "<verified: command and result | build only | not run>"
# Member: second part of the branch name (<type>/<member>/<topic>), or env ASTRA_MEMBER.
# Env: AGENT_START_SHA = commit at session start (default: where the branch left origin/main).
# Adapted from the DTT and CT-Labs tools/agent-log.sh.
set -euo pipefail
[ $# -eq 4 ] || { echo "usage: $0 <task> <prompt> <summary> <verified>" >&2; exit 2; }
task="$1"; prompt="$2"; summary="$3"; verified="$4"
root="$(git rev-parse --show-toplevel)"
branch="$(git rev-parse --abbrev-ref HEAD)"
member="${ASTRA_MEMBER:-$(printf '%s' "$branch" | awk -F/ 'NF>=3 {print $2}')}"
[ -n "$member" ] || { echo "cannot tell the member from branch '$branch'; set ASTRA_MEMBER" >&2; exit 2; }
head="$(git rev-parse --short=12 HEAD)"
start="${AGENT_START_SHA:-$(git merge-base HEAD origin/main 2>/dev/null || git rev-list --max-parents=0 HEAD | tail -1)}"
start_short="$(git rev-parse --short=12 "$start")"
files="$( { git diff --name-only "$start"..HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | grep -v '^agent-log/' | paste -sd, - || true)"
dirty="$(git status --porcelain | { grep -v 'agent-log/' || true; } | wc -l | tr -d ' ')"
if [ "$dirty" -gt 0 ]; then uncommitted="$dirty files not committed"; else uncommitted="none"; fi
mkdir -p "$root/agent-log"
printf '[%s] Member: %s / Branch: %s / Task: %s / Prompt: %s / Files Modified: %s / Summary: %s / Verified: %s / Uncommitted: %s / Git Fingerprint: %s -> %s\n' \
  "$(date '+%Y-%m-%d %H:%M:%S %z')" "$member" "$branch" "$task" "$prompt" "${files:-n/a}" "$summary" "$verified" "$uncommitted" "$start_short" "$head" \
  >> "$root/agent-log/$member.log"
echo "logged to agent-log/$member.log"
