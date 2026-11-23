#!/bin/zsh
# Daily GitHub publish: Parquet (zstd) + results + docs. The SQLite DB stays local (storage policy 2026-11-23).
cd "$(dirname "$0")/.." || exit 1
git add data/parquet data/events.csv results docs 2>/dev/null
if git diff --cached --quiet; then echo "nothing to publish"; exit 0; fi
SZ=$(du -sk data/parquet | cut -f1)
git commit -q -m "data: parquet $(date -u +%Y-%m-%dT%H:%MZ) (parquet ${SZ}KB)" && git push -q origin main && echo "pushed $(git rev-parse --short HEAD)"
