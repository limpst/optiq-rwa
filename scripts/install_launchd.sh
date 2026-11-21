#!/bin/zsh
# Install / reinstall the launchd agents (snapshot 15 min, readme hourly, trade 04:20 KST, settle 17:30 KST).
# NOTE: launchd cannot read ~/Downloads, ~/Desktop or ~/Documents (macOS TCC). Keep the repo elsewhere (e.g. ~/dev).
cd "$(dirname "$0")/.." || exit 1
REPO=$(pwd)
case "$REPO" in *"/Downloads/"*|*"/Desktop/"*|*"/Documents/"*) echo "repo is under a TCC-protected folder ($REPO); launchd jobs will fail with 'Operation not permitted'. Move the repo (e.g. ~/dev) first."; exit 2;; esac
mkdir -p data/logs ~/Library/LaunchAgents
for p in scripts/launchd/com.optiq.*.plist; do
  L=$(basename "$p" .plist)
  sed "s#__REPO__#$REPO#g" "$p" > ~/Library/LaunchAgents/$L.plist
  launchctl bootout "gui/$(id -u)/$L" 2>/dev/null
  launchctl bootstrap "gui/$(id -u)" ~/Library/LaunchAgents/$L.plist && echo "loaded $L"
done
launchctl list | grep com.optiq
