"""Idea 8: execution-economics gate (paper.gate) and gated twin strategies in the paper engine."""
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from optiq_rwa.data import store                  # noqa: E402
from optiq_rwa.data.live import live_chain        # noqa: E402
from optiq_rwa.paper import engine, gate          # noqa: E402
from test_live_paper import con                   # noqa: E402,F401  (fixture)


def _table(payback):
    rows = [dict(coin="*", kind=k, m=m, event=e, n=100, payback=payback)
            for k in ("call", "put") for m in np.arange(-3, 3.5, 0.5) for e in (False, True)]
    return pd.DataFrame(rows)


def _plan(con):
    ch = live_chain(con, 1, "SOL_USDC")
    r = ch[ch.instrument_name == "SOL_USDC-TEST-105-C"].iloc[0]
    return [dict(base="SOL_USDC", row=r, side="buy", usd=10.0, note="t")], r


def test_buy_edge_sign(con):
    plan, r = _plan(con)
    kept, blocked = gate.apply([dict(o) for o in plan], _table(2.0), event=False)   # E[payoff] = 2 x mid > ask + fee
    assert len(kept) == 1 and not blocked and kept[0]["edge_usd"] > 0
    kept, blocked = gate.apply([dict(o) for o in plan], _table(0.5), event=False)   # E[payoff] = mid / 2 < ask
    assert not kept and len(blocked) == 1
    fee = float(gate.COST_MODEL.fee(r.ask / r.spot)) * r.spot
    assert np.isclose(blocked[0]["edge_usd"], 10.0 / r.ask * (0.5 * r.mid - r.ask - fee))


def test_unknown_bucket_blocks(con):
    plan, _ = _plan(con)
    kept, blocked = gate.apply(plan, _table(2.0).iloc[0:0], event=False)
    assert not kept and len(blocked) == 1 and np.isnan(blocked[0]["package_edge_usd"])


def test_sell_package_is_all_or_nothing(con):
    ch = live_chain(con, 1, "SOL_USDC")
    legs = [("SOL_USDC-TEST-115-C", "sell"), ("SOL_USDC-TEST-90-P", "sell")]
    plan = [dict(base="SOL_USDC", row=ch[ch.instrument_name == n].iloc[0], side=s, usd=5.0, note="") for n, s in legs]
    kept, blocked = gate.apply(plan, _table(0.1), event=False)      # sellers keep 90% of mid minus fee -> pass
    assert len(kept) == 2 and not blocked
    kept, blocked = gate.apply(plan, _table(3.0), event=False)      # expected payoff 3x premium -> block both legs
    assert not kept and len(blocked) == 2


def test_gated_twin_logs_blocked_and_marks_nav(con, monkeypatch):
    monkeypatch.setattr(engine, "_payback_table", lambda: _table(0.5))            # gate blocks every buy
    strategies = {k: engine.STRATEGIES[k] for k in ("yield_calls", "yield_calls_gated")}
    out = engine.trade(con, nav0=100_000.0, strategies=strategies, log=lambda *_: None)
    assert out["yield_calls"]["orders"] == 1 and out["yield_calls_gated"]["orders"] == 0
    assert out["yield_calls_gated"]["gated"] == 1
    o = store.read(con, "SELECT strategy, status, fill_usd FROM paper_orders")
    assert (o[o.strategy == "yield_calls_gated"].status == "gated").all()
    monkeypatch.setattr(engine, "STRATEGIES", strategies)
    nav = engine.mark_nav(con, nav0=100_000.0, log=lambda *_: None).set_index("strategy")
    assert nav.loc["yield_calls_gated", "premium_paid"] == 0                     # gated twin still accrues RWA yield
    assert np.isclose(nav.loc["yield_calls_gated", "nav"], 100_000 + nav.loc["yield_calls_gated", "rwa_accrual"])


def test_load_payback_from_repo_results():
    t = gate.load_payback()
    if t.empty:
        return
    assert {"*", "BTC"} <= set(t.coin) and t.payback.between(0, 50).all()
    assert gate.expected_payback(t, "BTC", "call", 1.1, False) is not None
    assert gate.expected_payback(t, "ETH", "call", 1.0, False) is not None             # ETH falls back to the pooled table
