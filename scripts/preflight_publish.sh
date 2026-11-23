#!/bin/zsh
# Pre-publish gate: import, tests, dashboard export, data assertions, JS syntax, server health. Exit non-zero = do not publish.
set -e
cd "$(dirname "$0")/.." || exit 1
NOSERVER=0; [ "$1" = "--no-server" ] && NOSERVER=1       # daily.sh settle uses steps 1-4 only
export PYTHONPATH=src
PY="${OPTIQ_PY:-$HOME/dev/quantum/bin/python}"
echo "[1/5] import"; "$PY" -c "import optiq_rwa.paper.engine as e, optiq_rwa.dashboard.app; assert len(e.STRATEGIES) >= 10, e.STRATEGIES; print('   strategies', len(e.STRATEGIES))"
echo "[2/5] tests";  "$PY" -m pytest -q 2>&1 | tail -1 | tee /dev/stderr | grep -q " passed" 
echo "[2b] report style"; "$PY" tools/probe_report_style.py --paths docs/REPORT_*.md 2>&1 | tail -1 | tee /dev/stderr | grep -q "위반 없음"
echo "[3/5] export"; "$PY" scripts/export_dashboard.py
echo "[4/5] data assertions + JS syntax"; "$PY" - <<'PYEOF'
import json, pathlib, re, subprocess
d = json.loads(pathlib.Path("docs/data.json").read_text())
assert d["status"]["n_snapshots"] > 0, "no snapshots"
assert len(d["paper"]["roster"]) >= 10, "roster missing"
assert d["chains"], "no chains"
assert "real_table" in d["curves"] and d["curves"]["real_table"], "real backtest table missing"
assert d["regime"].get("live"), "regime live missing"
h = pathlib.Path("docs/artifact.html").read_text()
assert 'id="data" type="application/json">null</script>' in h, "artifact must load data.json (inline null)"
assert 0.02e6 < pathlib.Path("docs/artifact.html").stat().st_size < 2e6, "artifact page size out of range"
js = "\n".join(re.findall(r"<script>(.*?)</script>", h, re.S)); pathlib.Path("/tmp/_optiq_check.js").write_text(js)
r = subprocess.run(["node", "--check", "/tmp/_optiq_check.js"], capture_output=True, text=True); assert r.returncode == 0, r.stderr[:400]
for k in ("h_glance", "h_regime", "h_live", "h_paper", "h_eq", "h_real", "h_sweep", "h_method", "h_opt", "h_biz", "h_data", "h_gloss", "h_work", "h_lim", "h_links"):
    assert f'data-t="{k}"' in h, f"section {k} missing"
print("   data ok: snapshots", d["status"]["n_snapshots"], "roster", len(d["paper"]["roster"]), "artifact", round(pathlib.Path("docs/artifact.html").stat().st_size/1e3), "KB")
PYEOF
if [ "$NOSERVER" = "1" ]; then echo "PREFLIGHT OK (no server step)"; exit 0; fi
echo "[5/5] server"; pkill -f "uvicorn optiq_rwa.dashboard" || true; sleep 1
(nohup "$PY" -m uvicorn optiq_rwa.dashboard.app:app --port 8793 --log-level warning > data/logs/dashboard.log 2>&1 &)
for i in 1 2 3 4 5 6 7 8 9 10; do code=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8793/ || true); [ "$code" = "200" ] && break; sleep 2; done
[ "$code" = "200" ] || { echo "   server not up: $code"; exit 1; }
api=$(curl -s http://127.0.0.1:8793/api/all | "$PY" -c "import json,sys; d=json.load(sys.stdin); print(d['status']['n_snapshots'])")
echo "   server 200, api snapshots $api"
echo "PREFLIGHT OK"
