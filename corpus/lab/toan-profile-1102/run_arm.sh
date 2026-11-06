#!/bin/bash
L=$HOME/Lecturing_Lab/agent-review/TOAN-PROFILE-1102; tag=$1; arm=$2
mkdir -p $L/sb/$tag/base $L/sb/$tag/state
cd $HOME/Lecturing_Lab/wt-agent-runner/Grading_Tools
export GEMINI_API_KEY="" GEMINI_API_KEYS="" ANTHROPIC_API_KEY="" OPENAI_API_KEY="" PROMPT_PROXY_URL="" LICENSE_VERIFY_URL=""
export PYTHONDONTWRITEBYTECODE=1 LECTURING_DEV_AI=codex-cli LECTURING_ALLOWED_HOSTS=testserver LECTURING_BASE_DIR=$L/sb/$tag/base LECTURING_STATE_DIR=$L/sb/$tag/state LECTURING_INSTALL_ROOT=$L/sb/$tag/state
exec $HOME/Lecturing_Source/.venv/bin/python3 $L/lab_arm.py $tag $arm > $L/run-$tag.log 2>&1
