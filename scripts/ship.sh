#!/bin/zsh
# ship.sh "<commit message>" [--no-server]
# preflight (import · tests · report style · export · data assertions · JS · server) -> git add -A (tracked dirs) -> commit -> pull --rebase -> push.
# Stops at the first failure; never commits a page that failed preflight. The artifact publish itself is done by the
# Claude session from docs/artifact.html + docs/data.json after this script prints SHIPPED.
set -e
cd "$(dirname "$0")/.." || exit 1
MSG="${1:?usage: ship.sh \"commit message\" [--no-server]}"; shift || true
/bin/zsh scripts/preflight_publish.sh "$@"
git add -A src scripts tools tests docs results data/parquet data/events.csv README.md .gitignore pyproject.toml 2>/dev/null || true
if git diff --cached --quiet; then echo "nothing to commit"; else
  git commit -q -m "$MSG

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
fi
git pull -q --rebase --autostash origin main
git push -q origin main
echo "SHIPPED $(git rev-parse --short HEAD)"
