#!/bin/zsh
# Failure alert: notify.sh "<title>" "<body>"
#   always  macOS notification + data/logs/alerts.log
#   if set  OPTIQ_ALERT_WEBHOOK in .env -> POST {"text": ...} (Teams "Post to a channel when a webhook request is received"
#           workflow, or a Slack incoming webhook; a Teams/Power Automate workflow can also forward it as e-mail)
cd "$(dirname "$0")/.." || exit 1
mkdir -p data/logs
[ -f .env ] && WEBHOOK=$(grep -E '^OPTIQ_ALERT_WEBHOOK=' .env | tail -1 | cut -d= -f2- | tr -d '"'"'")
WEBHOOK="${OPTIQ_ALERT_WEBHOOK:-$WEBHOOK}"
PY="${OPTIQ_PY:-$HOME/dev/quantum/bin/python}"
echo "$(date -u +%FT%TZ) ALERT $1 :: $2" >> data/logs/alerts.log
"$PY" - "$1" "$2" "$WEBHOOK" <<'PYEOF'
import json, subprocess, sys, urllib.request
title, body, hook = sys.argv[1], sys.argv[2], sys.argv[3]
esc = lambda s: s.replace("\\", "\\\\").replace('"', "'")[:240]
try:
    subprocess.run(["osascript", "-e", f'display notification "{esc(body)}" with title "{esc(title)}"'], check=False)
except OSError:
    pass
if hook:
    req = urllib.request.Request(hook, json.dumps({"text": f"**{title}**\n\n{body}"}).encode(), {"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=20).read()
    except Exception as e:
        print("webhook failed:", e)
PYEOF
