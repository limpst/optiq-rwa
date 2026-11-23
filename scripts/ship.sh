#!/bin/zsh
# ship.sh "<commit message>" [--no-server]
# preflight (import · tests · report style · export · data assertions · JS · server) -> git add -A (tracked dirs) -> commit -> pull --rebase -> push.
# Stops at the first failure; never commits a page that failed preflight. The artifact publish itself is done by the
# Claude session from docs/artifact.html + docs/data.json after this script prints SHIPPED.
set -e
cd "$(dirname "$0")/.." || exit 1
MSG="${1:?usage: ship.sh \"commit message\" [--no-server] [--copy vN [label]]}"; shift || true
COPY=""; LABEL=""; ARGS=()
while [ $# -gt 0 ]; do case "$1" in --copy) COPY="$2"; shift 2; [ $# -gt 0 ] && [[ "$1" != --* ]] && { LABEL="$1"; shift; };; *) ARGS+=("$1"); shift;; esac; done
/bin/zsh scripts/preflight_publish.sh "${ARGS[@]}"
git add -A src scripts tools tests docs results data/parquet data/events.csv README.md .gitignore pyproject.toml 2>/dev/null || true
if git diff --cached --quiet; then echo "nothing to commit"; else
  git commit -q -m "$MSG

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
fi
git pull -q --rebase --autostash origin main
git push -q origin main
echo "SHIPPED $(git rev-parse --short HEAD)"
# --copy vN [label]: keep the HTML + data.json copy the global rule asks for (~/Claude_Artifacts) and append the INDEX.md line
if [ -n "$COPY" ]; then
  D=$(date +%Y-%m-%d); URL="https://claude.ai/artifact/QbAXfoRRHvuhBF4nSW5Vd7"; mkdir -p ~/Claude_Artifacts
  cp docs/artifact.html ~/Claude_Artifacts/${D}_OptiQ-RWA_Desk_${COPY}.html && cp docs/data.json ~/Claude_Artifacts/${D}_OptiQ-RWA_Desk_${COPY}_data.json
  echo "- ${D} · OptiQ-RWA Desk · ${COPY}${LABEL:+ (${LABEL})} · ${URL} · ${D}_OptiQ-RWA_Desk_${COPY}.html (+ _data.json)" >> ~/Claude_Artifacts/INDEX.md
  echo "COPIED ~/Claude_Artifacts/${D}_OptiQ-RWA_Desk_${COPY}.html"
fi
