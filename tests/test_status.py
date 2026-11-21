"""docs/status.md builder: paper section with the gate before/after table (scripts/update_status.py)."""
import importlib.util
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from optiq_rwa.data import store                  # noqa: E402
from optiq_rwa.paper import engine                # noqa: E402
from test_gate import _table                      # noqa: E402
from test_live_paper import con                   # noqa: E402,F401  (fixture)

_spec = importlib.util.spec_from_file_location("update_status", pathlib.Path(__file__).resolve().parents[1] / "scripts" / "update_status.py")
status = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(status)


def test_gate_before_after_table(con, monkeypatch):
    monkeypatch.setattr(engine, "_payback_table", lambda: _table(0.5))
    strategies = {k: engine.STRATEGIES[k] for k in ("yield_calls", "yield_calls_gated")}
    monkeypatch.setattr(engine, "STRATEGIES", strategies)
    engine.trade(con, nav0=100_000.0, strategies=strategies, log=lambda *_: None)
    con.execute("UPDATE paper_positions SET expiry_ts=?", (int(time.time() * 1000) - 1000,))
    con.execute("INSERT INTO delivery_price VALUES ('sol_usdc', ?, 100.0)", (store.utc_date(int(time.time() * 1000) - 1000),))
    engine.settle(con, log=lambda *_: None)
    engine.mark_nav(con, nav0=100_000.0, log=lambda *_: None)
    text = "\n".join(status.paper_section(con))
    assert "적용 전 / 후" in text
    row = [l for l in text.splitlines() if l.startswith("| yield_calls |")][-1]
    cells = [c.strip() for c in row.strip("|").split("|")]
    assert cells[-1] == "0 / 1"                       # gated twin: 0 nights traded, 1 night blocked
    assert cells[2] == "0.00%"                        # gated twin only accrued RWA yield on day 1 (NAV base = day-1 NAV)
    assert not cells[1].startswith("+")               # ungated call expired worthless at spot 100 -> loss
