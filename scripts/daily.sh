#!/bin/zsh
# daily jobs (launchd):
#   daily.sh trade    04:20 KST (19:20 UTC) paper orders on the fresh snapshot
#   daily.sh settle   17:30 KST (08:30 UTC) settle expired paper positions, mark NAV, export parquet, commit+push DB
cd "$(dirname "$0")/.." || exit 1
export PYTHONPATH=src
PY="${OPTIQ_PY:-$HOME/dev/quantum/bin/python}"
mkdir -p data/logs
LOG=data/logs/daily.log
case "$1" in
  trade)
    # the 15-min snapshot job supplies quotes; running another snapshot here held the DB write lock (2026-11-21/22 trades failed)
    "$PY" -m optiq_rwa.paper.engine trade >> $LOG 2>&1
    ;;
  settle)
    "$PY" -m optiq_rwa.paper.engine settle >> $LOG 2>&1
    "$PY" -m optiq_rwa.paper.engine nav >> $LOG 2>&1
    "$PY" -m optiq_rwa.data.live export >> $LOG 2>&1
    "$PY" scripts/export_dashboard.py >> $LOG 2>&1 || true
    scripts/publish_data.sh >> $LOG 2>&1
    ;;
  *) echo "usage: daily.sh trade|settle"; exit 2;;
esac
