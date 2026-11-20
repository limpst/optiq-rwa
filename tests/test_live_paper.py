"""Store / live_chain / paper engine / periods on an in-memory fixture (no network)."""
import dataclasses
import pathlib
import sys
import time

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from optiq_rwa.data import store                      # noqa: E402
from optiq_rwa.data.live import live_chain, volume_table   # noqa: E402
from optiq_rwa.paper import engine                    # noqa: E402
from optiq_rwa.backtest.periods import period_table, summary  # noqa: E402


@pytest.fixture
def con(tmp_path, monkeypatch):
    con = store.connect(tmp_path / "t.db")
    ts = int(time.time() * 1000) - 3600_000          # snapshot one hour ago
    exp = ts + 13 * 3600_000                         # 13h to expiry
    date = store.utc_date(ts)
    con.execute("INSERT INTO snapshots (snap_id, ts_ms, date) VALUES (1, ?, ?)", (ts, date))
    spot = 100.0
    inst, summ, ob, st = [], [], [], []
    for k in (90, 95, 100, 105, 110, 115):
        for kind, cp in (("call", "C"), ("put", "P")):
            name = f"SOL_USDC-TEST-{k}-{cp}"
            inst.append(dict(instrument_name=name, base="SOL_USDC", currency="USDC", settlement_currency="USDC", option_type=kind,
                             strike=k, expiration_ts=exp, contract_size=1.0, inverse=0, tick_size=0.01, min_trade_amount=1.0,
                             first_seen_ms=ts, last_seen_ms=ts))
            intrinsic = max(spot - k, 0) if kind == "call" else max(k - spot, 0)
            mid = intrinsic + 1.0
            summ.append(dict(snap_id=1, instrument_name=name, bid=mid - 0.1, ask=mid + 0.1, mid=mid, mark_price=mid, mark_iv=127.0,
                             volume=10, volume_usd=1000.0, open_interest=5, underlying_price=spot))
            for lvl, amt in enumerate((5, 10, 50)):            # 3 levels, 0.1 apart: depth 5 / 10 / 50 contracts
                ob.append(dict(snap_id=1, instrument_name=name, level=lvl, bid_px=mid - 0.1 * (lvl + 1), bid_amt=amt,
                               ask_px=mid + 0.1 * (lvl + 1), ask_amt=amt))
            st.append(dict(snap_id=1, instrument_name=name, mark_price=mid, mark_iv=127.0, bid_iv=125, ask_iv=129, delta=0.5, gamma=0,
                           vega=0, theta=0, index_price=spot, underlying_price=spot, open_interest=5, interest_rate=0))
    for t, rows in (("instruments", inst), ("book_summary", summ), ("order_book", ob), ("inst_state", st)):
        store.insert_df(con, t, pd.DataFrame(rows))
    vol = volume_table(pd.DataFrame(summ), date)
    vol["universe_pass"] = 1
    store.insert_df(con, "volume_daily", vol)
    con.commit()
    monkeypatch.setattr(engine, "SETTINGS", dataclasses.replace(engine.SETTINGS, focus_bases=("SOL_USDC",)))
    return con


def test_live_chain_schema(con):
    ch = live_chain(con, 1, "SOL_USDC")
    assert len(ch) == 12 and set(ch.kind) == {"call", "put"}
    assert (ch.quote_source == "order_book").all()
    assert np.isclose(ch.k_rel[ch.strike == 100].iloc[0], 1.0)
    assert 12.9 < ch.hours.iloc[0] < 13.1
    assert (ch.m[ch.kind == "call"].diff().dropna() > 0).all()      # m increases with strike


def test_paper_trade_settle_nav(con):
    out = engine.trade(con, nav0=100_000.0, min_hours=6, max_hours=26, log=lambda *_: None)
    assert out["yield_calls"]["orders"] == 1
    orders = store.read(con, "SELECT * FROM paper_orders WHERE status='filled'")
    assert (orders.fill_usd > 0).all()
    budget = 100_000 * engine.SETTINGS.rwa_rate / 365
    assert np.isclose(orders[orders.strategy == "yield_calls"].fill_usd.sum(), budget)
    # trading twice the same day is a no-op
    again = engine.trade(con, nav0=100_000.0, min_hours=6, max_hours=26, log=lambda *_: None)
    assert "yield_calls" not in again          # a strategy with no fills may retry
    # force expiry + delivery price, settle, mark NAV
    con.execute("UPDATE paper_positions SET expiry_ts=?", (int(time.time() * 1000) - 1000,))
    exp_date = store.utc_date(int(time.time() * 1000) - 1000)
    con.execute("INSERT INTO delivery_price VALUES ('sol_usdc', ?, 112.0)", (exp_date,))
    n = engine.settle(con, log=lambda *_: None)
    assert n == len(store.read(con, "SELECT * FROM paper_positions"))
    pos = store.read(con, "SELECT * FROM paper_positions WHERE strategy='yield_calls'").iloc[0]
    # bought the call nearest m=+1 -> strike 105 -> payoff (112-105)*qty
    assert pos.instrument_name.endswith("-105-C")
    assert np.isclose(pos.payoff_usd, 7.0 * pos.qty)
    nav = engine.mark_nav(con, nav0=100_000.0, log=lambda *_: None)
    yc = nav[nav.strategy == "yield_calls"].iloc[0]
    fees = orders[orders.strategy == "yield_calls"].fee_usd.sum()
    assert np.isclose(yc.nav, 100_000 + yc.rwa_accrual - yc.premium_paid + pos.payoff_usd - fees)
    assert np.isclose(yc.fees_usd, fees) and fees > 0
    assert pos.settle_fee_usd == 0.0                       # daily options exempt from settlement fee


def _row(con, name="SOL_USDC-TEST-105-C"):
    ch = live_chain(con, 1, "SOL_USDC")
    return ch[ch.instrument_name == name].iloc[0]


def test_depth_walk_vwap_fee_and_nav_identity(con, monkeypatch):
    r = _row(con)                                           # mid 1.0 -> asks 1.1 / 1.2 / 1.3 with 5 / 10 / 50 contracts
    ts, date = con.execute("SELECT ts_ms, date FROM snapshots WHERE snap_id=1").fetchone()
    engine._place(con, 1, ts, date, "yield_calls", r, "buy", 30.0, "deep")
    engine._place(con, 1, ts, date, "yield_calls", r, "buy", 3.0, "shallow")
    o = store.read(con, "SELECT * FROM paper_orders ORDER BY order_id")
    deep, shallow = o.iloc[0], o.iloc[1]
    # $30: 5@1.1 = 5.5, 10@1.2 = 12, remaining 12.5 @1.3
    q = 5 + 10 + 12.5 / 1.3
    assert deep.levels_used == 3 and np.isclose(deep.qty, q) and np.isclose(deep.fill_usd, 30.0)
    assert np.isclose(deep.fill_px, 30.0 / q)
    assert np.isclose(deep.slippage_usd, (30.0 / q - 1.1) * q)
    assert np.isclose(deep.fee_usd, min(0.0003 * 100.0 * q, 0.125 * 30.0))
    assert shallow.levels_used == 1 and np.isclose(shallow.fill_px, 1.1) and np.isclose(shallow.slippage_usd, 0.0)
    # sells walk the bids downward: 0.9 / 0.8 / 0.7
    engine._place(con, 1, ts, date, "short_condor", r, "sell", 8.0, "sell")
    sell = store.read(con, "SELECT * FROM paper_orders ORDER BY order_id").iloc[2]
    qs = 5 + 3.5 / 0.8
    assert sell.levels_used == 2 and np.isclose(sell.fill_px, 8.0 / qs) and sell.slippage_usd > 0
    # fee cap binds for cheap options (12.5% of fill value)
    cheap = r.copy(); cheap["ask"] = 0.001
    w = engine._walk_book(con, 1, cheap, "buy", 1.0)
    assert np.isclose(w["fee_usd"], 0.125 * w["fill_usd"]) or w["fee_usd"] <= 0.125 * w["fill_usd"] + 1e-12
    # preview matches _place (no writes)
    n_before = len(store.read(con, "SELECT * FROM paper_orders"))
    pv = engine.preview(con, nav0=100_000.0, min_hours=6, max_hours=26)
    assert {"fee_usd", "slippage_usd", "levels_used", "fill_vwap"} <= set(pv.columns)
    assert len(store.read(con, "SELECT * FROM paper_orders")) == n_before
    # NAV identity incl. settlement fee (force non-exempt)
    import dataclasses as dc
    monkey = dc.replace(engine.COST_MODEL, settle_daily_exempt=False)
    monkeypatch.setattr(engine, "COST_MODEL", monkey)
    con.execute("UPDATE paper_positions SET expiry_ts=?", (int(time.time() * 1000) - 1000,))
    con.execute("INSERT INTO delivery_price VALUES ('sol_usdc', ?, 112.0)", (store.utc_date(int(time.time() * 1000) - 1000),))
    engine.settle(con, log=lambda *_: None)
    pos = store.read(con, "SELECT * FROM paper_positions WHERE strategy='yield_calls'")
    sf = pos.settle_fee_usd.sum()
    assert np.allclose(pos.settle_fee_usd, np.minimum(0.00015 * 112.0, 0.125 * 7.0) * pos.qty)
    nav = engine.mark_nav(con, nav0=100_000.0, log=lambda *_: None)
    yc = nav[nav.strategy == "yield_calls"].iloc[0]
    fees = store.read(con, "SELECT SUM(fee_usd) f FROM paper_orders WHERE strategy='yield_calls'").f[0] + sf
    assert np.isclose(yc.fees_usd, fees)
    payoff = (pos.payoff_usd).sum()
    assert np.isclose(yc.nav, 100_000 + yc.rwa_accrual - yc.premium_paid + yc.premium_received + payoff - fees)


def test_depth_exhausted_partial(con):
    r = _row(con)
    ts, date = con.execute("SELECT ts_ms, date FROM snapshots WHERE snap_id=1").fetchone()
    engine._place(con, 1, ts, date, "yield_calls", r, "buy", 10_000.0, "big")
    o = store.read(con, "SELECT * FROM paper_orders").iloc[0]
    assert o.levels_used == 3 and np.isclose(o.qty, 65) and "partial: depth exhausted" in o.note
    assert np.isclose(o.fill_usd, 5 * 1.1 + 10 * 1.2 + 50 * 1.3)


def test_period_table_matches_total():
    idx = pd.date_range("2026-01-01", periods=59, freq="D")          # Jan 1 .. Feb 28
    nav = pd.Series(np.cumprod(1 + np.full(59, 0.001)), index=idx)
    m = period_table(nav, "M")
    assert len(m) == 2
    assert np.isclose((1 + m.ret).prod() - 1, nav.iloc[-1] / nav.iloc[0] - 1, atol=1e-9)   # day 1 = starting NAV
    s = summary(nav)
    assert s["total"]["n_days"] == 59 and "W" in s
