#!/bin/zsh
# launchd jobs:
#   daily.sh trade    04:20 KST (19:20 UTC) paper orders on the fresh snapshot (base + gated twins, idea 8)
#   daily.sh settle   17:30 KST (08:30 UTC) settle, mark NAV, export parquet, live chain nights (data/live),
#                     OOS walk-forward refresh (regime labels + validation), docs/status.md, commit+push parquet/results/docs to main
#                     (storage policy 2026-11-23: data/optiq.db is local only; book_summary keeps expiries <= 8 days)
#   daily.sh status   hourly (com.optiq.readme) docs/status.md -> force-push as the single commit of branch `status`;
#                     alerts once when the newest snapshot is > 45 min old (collector stalled)
#                     (main history untouched). `readme` is accepted as an alias for agents installed earlier.
# Any failed step -> scripts/notify.sh (macOS notification, optional Teams / Slack webhook, data/logs/alerts.log).
cd "$(dirname "$0")/.." || exit 1
export PYTHONPATH=src
PY="${OPTIQ_PY:-$HOME/dev/quantum/bin/python}"
mkdir -p data/logs
LOG=data/logs/daily.log
FAILED=()
ERRS=()
step() {   # run one step; on failure remember its name and the last meaningful error line (Error/Traceback-free) for the alert
  local n=$1; shift; local tmp; tmp=$(mktemp)
  if "$@" > "$tmp" 2>&1; then cat "$tmp" >> $LOG; else
    cat "$tmp" >> $LOG; FAILED+=("$n")
    local line; line=$(grep -E "Error|error:|Assert|FAILED|failed|locked|No such|not found" "$tmp" | grep -v "^  File\|Traceback" | tail -1 | cut -c1-200)
    [ -z "$line" ] && line=$(grep -v "^\s*$" "$tmp" | tail -1 | cut -c1-200)
    ERRS+=("[$n] $line")
  fi
  rm -f "$tmp"
}
case "$1" in
  trade)
    # quotes come from the 15-min snapshot job; an extra snapshot here held the DB write lock (11-21/22 trades failed)
    step trade    "$PY" -m optiq_rwa.paper.engine trade
    ;;
  settle)
    step settle     "$PY" -m optiq_rwa.paper.engine settle
    step nav        "$PY" -m optiq_rwa.paper.engine nav
    step export     "$PY" -m optiq_rwa.data.live export
    step dashboard  /bin/zsh scripts/preflight_publish.sh --no-server   # export + assertions (import, tests, data, JS); fails loudly instead of committing a broken page
    step livechain  "$PY" -m optiq_rwa.data.livechain build          # live order-book nights -> data/live/
    step regime     "$PY" scripts/run_regime.py                      # walk-forward labels (past nights only)
    step validation "$PY" scripts/run_regime_validation.py           # OOS walk-forward NAV / SR / IR / MDD / DSR
    step status     "$PY" scripts/update_status.py
    step publish    scripts/publish_data.sh                           # parquet + data/live + results + docs (DB stays local)
    ;;
  status|readme)
    LOG=data/logs/status.log
    "$PY" scripts/update_status.py --max-age-min 45 >> $LOG 2>&1; rc=$?
    STALE=data/logs/.snapshot_stale                       # one alert per stall episode, cleared when data flows again
    if [ $rc -eq 3 ]; then
      [ -f $STALE ] || { touch $STALE; FAILED+=("snapshot-stale(>45min)"); }
    else
      rm -f $STALE
      [ $rc -ne 0 ] && FAILED+=("status")
    fi
    if [ -f docs/status.md ]; then
      blob=$(git hash-object -w docs/status.md) \
        && tree=$(printf '100644 blob %s\tREADME.md\n' "$blob" | git mktree) \
        && c=$(git commit-tree "$tree" -m "status $(date -u +%Y-%m-%dT%H:%MZ)") \
        && git push -q -f origin "${c}:refs/heads/status" >> $LOG 2>&1 || FAILED+=("push-status")
    fi
    ;;
  *) echo "usage: daily.sh trade|settle|status"; exit 2;;
esac
if [ ${#FAILED[@]} -gt 0 ]; then
  /bin/zsh scripts/notify.sh "OptiQ $1 실패: ${FAILED[*]}" "$(printf '%s\n' "${ERRS[@]}")"
  exit 1
fi
