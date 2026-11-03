#!/bin/bash
# Resumable: extraction skips finished papers. Stops at once if the CLI still refuses.
L=$HOME/Lecturing_Lab/agent-review/TOAN-PROFILE-1102; cd $L
python3 extract.py >> extract.log 2>&1
[ $(ls extract/p*.json | wc -l) -eq 9 ] || { echo "extraction incomplete"; exit 1; }
[ -f outputs/profile.compact.json ] || python3 aggregate.py >> aggregate.log 2>&1
[ -f outputs/profile.compact.json ] || { echo "aggregate failed"; exit 1; }
./run_arm.sh A1 base & ./run_arm.sh B1 profile & wait
./run_arm.sh A2 base & ./run_arm.sh B2 profile & wait
echo done
