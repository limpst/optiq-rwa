"""Dashboard bundle builds on a small fixture DB and carries the keys the page reads (no network)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from test_live_paper import con  # noqa: E402,F401  (fixture: one snapshot, SOL_USDC chain with depth)


def test_build_bundle_keys(con, monkeypatch):
    from optiq_rwa.dashboard import app
    b = app.build_bundle(con)
    for k in ("generated_at", "config", "status", "universe", "index_history", "candles", "spread_grid", "spread_by_hour",
              "chains", "paper", "periods", "sweep", "real", "regime", "curves", "events"):
        assert k in b, k
    assert b["status"]["n_snapshots"] == 1 and "health" in b["status"]
    for k in ("roster", "pnl_grid", "intraday", "maker", "gate", "preview", "nav", "orders", "positions"):
        assert k in b["paper"], k
    assert len(b["paper"]["roster"]) >= 10
    assert "SOL_USDC" in b["chains"]
    import json
    json.dumps(b, default=str)                      # must be JSON-serialisable for /api/all and data.json


def test_full_document_wraps_fragment():
    from optiq_rwa.dashboard.app import full_document, STATIC
    frag = (STATIC / "index.html").read_text()
    doc = full_document(frag)
    assert doc.startswith("<!doctype html>") and doc.endswith("</body></html>")
    assert '<script id="data" type="application/json">' in frag and 'id="btn-en"' in frag
