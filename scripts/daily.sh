#!/bin/zsh
# daily jobs (launchd):
#   daily.sh trade    04:20 KST (19:20 UTC) paper orders on the fresh snapshot
#   daily.sh settle   17:30 KST (08:30 UTC) settle expired paper positions, mark NAV, export parquet,
#                     refresh OOS walk-forward (regime labels + validation), rewrite README status, commit+push DB
#   daily.sh readme   hourly (com.optiq.readme) rewrite README status block from the live DB, commit+push README only
cd "$(dirname "$0")/.." || exit 1
export PYTHONPATH=src
PY="${OPTIQ_PY:-$HOME/dev/quantum/bin/python}"
mkdir -p data/logs
LOG=data/logs/daily.log
case "$1" in
  trade)
    "$PY" -m optiq_rwa.data.live snapshot >> $LOG 2>&1
    "$PY" -m optiq_rwa.paper.engine trade >> $LOG 2>&1
    ;;
  settle)
    "$PY" -m optiq_rwa.data.live snapshot >> $LOG 2>&1
    "$PY" -m optiq_rwa.paper.engine settle >> $LOG 2>&1
    "$PY" -m optiq_rwa.paper.engine nav >> $LOG 2>&1
    "$PY" -m optiq_rwa.data.live export >> $LOG 2>&1
    "$PY" scripts/export_dashboard.py >> $LOG 2>&1 || true
    "$PY" scripts/run_regime.py >> $LOG 2>&1 || true              # walk-forward labels (past nights only)
    "$PY" scripts/run_regime_validation.py >> $LOG 2>&1 || true   # OOS walk-forward NAV / SR / IR / MDD / DSR
    "$PY" scripts/update_readme.py >> $LOG 2>&1 || true
    scripts/publish_db.sh >> $LOG 2>&1
    ;;
  readme)
    "$PY" scripts/update_readme.py >> data/logs/readme.log 2>&1 || exit 0
    git add README.md
    git diff --cached --quiet && exit 0
    git commit -q -m "readme: status $(date -u +%Y-%m-%dT%H:%MZ)" >> data/logs/readme.log 2>&1
    git pull -q --rebase --autostash origin main >> data/logs/readme.log 2>&1 && git push -q origin main >> data/logs/readme.log 2>&1
    ;;
  *) echo "usage: daily.sh trade|settle|readme"; exit 2;;
esac
