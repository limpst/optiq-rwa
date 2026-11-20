#!/bin/zsh
# 15-min live snapshot (launchd com.optiq.snapshot). Public endpoints only.
cd "$(dirname "$0")/.." || exit 1
export PYTHONPATH=src
PY="${OPTIQ_PY:-$HOME/dev/quantum/bin/python}"
mkdir -p data/logs
"$PY" -m optiq_rwa.data.live snapshot >> data/logs/snapshot.log 2>&1
