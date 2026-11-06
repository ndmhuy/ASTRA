#!/bin/bash
# One real-money baseline paper. Refuses a second run. Key comes from the ANTHROPIC_API_KEY you exported.
L=$HOME/Lecturing_Lab/agent-review/TOAN-PROFILE-1102; tag=${LAB_COST_TAG:-COST1}
if [ "$LAB_COST_DRY" != "1" ]; then
  [ -n "$ANTHROPIC_API_KEY" ] || { echo "Chưa có ANTHROPIC_API_KEY"; exit 1; }
  [ ! -e "$L/outputs/run-$tag" ] || { echo "Đã chạy rồi: $L/outputs/run-$tag"; exit 1; }
fi
export LAB_ANTHROPIC_KEY="$ANTHROPIC_API_KEY"
mkdir -p "$L/sb/$tag/base" "$L/sb/$tag/state"
cd "$HOME/Lecturing_Lab/wt-agent-runner/Grading_Tools" || exit 1
export GEMINI_API_KEY="" GEMINI_API_KEYS="" ANTHROPIC_API_KEY="" OPENAI_API_KEY="" PROMPT_PROXY_URL="" LICENSE_VERIFY_URL=""
export PYTHONDONTWRITEBYTECODE=1 LECTURING_DEV_AI=claude-cli LECTURING_ALLOWED_HOSTS=testserver LECTURING_BASE_DIR="$L/sb/$tag/base" LECTURING_STATE_DIR="$L/sb/$tag/state" LECTURING_INSTALL_ROOT="$L/sb/$tag/state"
echo "Đang chạy. Nhật ký: $L/run-$tag.log. Giới hạn chi: ${LAB_COST_CAP_USD:-5} USD."
"$HOME/Lecturing_Source/.venv/bin/python3" "$L/lab_cost.py" "$tag" > "$L/run-$tag.log" 2>&1
code=$?; echo "Xong, mã thoát $code"; tail -2 "$L/run-$tag.log" | cut -c1-200; exit $code
