#!/bin/zsh
# Commit data/optiq.db + data/parquet + data/live + results + docs (status.md) to GitHub (daily). Skips if DB > 90 MB (GitHub 100 MB limit).
cd "$(dirname "$0")/.." || exit 1
PY="${OPTIQ_PY:-$HOME/dev/quantum/bin/python}"
"$PY" - <<'PYEOF'
import sqlite3, sys; sys.path.insert(0, "src")
from optiq_rwa.config import SETTINGS
con = sqlite3.connect(SETTINGS.db_path); con.execute("PRAGMA wal_checkpoint(TRUNCATE)"); con.close()
PYEOF
SZ=$(stat -f%z data/optiq.db)
if [ "$SZ" -gt 94371840 ]; then echo "DB ${SZ}B > 90MB: not committing; switch to parquet-only publishing"; exit 3; fi
git add data/optiq.db data/parquet data/live results docs 2>/dev/null
if git diff --cached --quiet; then echo "nothing to publish"; exit 0; fi
git commit -q -m "data: snapshot $(date -u +%Y-%m-%dT%H:%MZ) (db ${SZ}B)" && git pull -q --rebase --autostash origin main && git push -q origin main && echo "pushed $(git rev-parse --short HEAD)"
