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


def test_lower_bound_blocks_thin_edge(con):
    plan, _ = _plan(con)                                   # 105C: mid 1.0, ask 1.1
    t = _table(1.2).assign(se=0.0)
    kept, _ = gate.apply([dict(o) for o in plan], t, event=False)
    assert len(kept) == 1                                  # point estimate 1.2 x mid clears ask + fee
    kept, blocked = gate.apply([dict(o) for o in plan], t.assign(se=0.1), event=False)
    assert not kept and len(blocked) == 1                  # 1.2 - 1.645 x 0.1 = 1.04 < ask
    kept, _ = gate.apply([dict(o) for o in plan], t.assign(se=0.1), event=False, z=0.0)
    assert len(kept) == 1                                  # z = 0 -> point estimate again


def test_live_nights_pull_payback(tmp_path):
    (tmp_path / "cal").mkdir(); (tmp_path / "live").mkdir()
    pd.DataFrame([dict(coin="SOL", kind="call", m=1.0, event=False, n=100, payback_mid=0.5, p_itm_emp=0.2)]).to_csv(
        tmp_path / "cal" / "calibration_SOL.csv", index=False)
    no_live = gate.load_payback(tmp_path / "cal", live_dir=tmp_path / "live")
    hist = no_live[no_live.coin == "SOL"].iloc[0]
    assert np.isclose(hist.payback, 0.5) and hist.n_live == 0 and hist.se > 0
    n = 60                                                 # live nights: half end ITM paying 4 x mid -> payback 2.0
    live = pd.DataFrame(dict(night=range(n), date=pd.date_range("2026-11-01", periods=n).date, coin="SOL", kind="call",
                             m=1.0, k_rel=1.02, iv=0.6, iv_atm=0.6, mid=0.01, bid=0.009, ask=0.011, settle_rel=1.0,
                             payoff=[0.04 if i % 2 else 0.0 for i in range(n)], event=False, quote_source="live_book"))
    live.to_parquet(tmp_path / "live" / "sol_live_chain.parquet")
    t = gate.load_payback(tmp_path / "cal", live_dir=tmp_path / "live")
    r = t[t.coin == "SOL"].iloc[0]
    assert r.n_live == n and np.isclose(r.payback, 0.5 * 0.5 + 0.5 * 2.0)   # w_live = 60 / (60 + 60)
