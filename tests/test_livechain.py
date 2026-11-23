"""Live order-book nights in the raw-chain schema (data.livechain)."""
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from optiq_rwa.data import livechain, store     # noqa: E402
from test_live_paper import con                 # noqa: E402,F401  (fixture)


def _build(con, settle=112.0):
    ts = con.execute("SELECT ts_ms FROM snapshots WHERE snap_id=1").fetchone()[0]
    t = pd.Timestamp(ts, unit="ms", tz="UTC")
    exp = con.execute("SELECT MAX(expiration_ts) FROM instruments").fetchone()[0]
    if settle is not None:
        con.execute("INSERT INTO delivery_price VALUES ('sol_usdc', ?, ?)", (store.utc_date(exp), settle))
    return livechain.build_live_chain(con, "SOL", entry_hour=t.hour, entry_min=t.minute, tol_min=5)


def test_live_chain_rows_and_payoff(con):
    df = _build(con)
    assert list(df.columns) == livechain.COLS and len(df) == 12
    assert (df.quote_source == "live_book").all() and (df.night == 0).all()
    assert np.isclose(df.settle_rel.iloc[0], 1.12)
    c105 = df[(df.kind == "call") & np.isclose(df.k_rel, 1.05)].iloc[0]
    assert np.isclose(c105.payoff, 0.07) and c105.ask > c105.mid > c105.bid       # real book quotes, relative to spot
    assert (df.m * 2 == (df.m * 2).round()).all()                                 # m on the 0.5 grid


def test_unsettled_night_skipped(con):
    assert _build(con, settle=None).empty


def test_load_chain_appends_after_raw(con, tmp_path):
    live = _build(con)
    d = live.date.iloc[0]
    raw = live.assign(date=d - pd.Timedelta(days=1), quote_source="trade_vwap")
    overlap = live.assign(date=d - pd.Timedelta(days=1))                          # same date as raw -> dropped
    (tmp_path / "raw").mkdir(); (tmp_path / "live").mkdir()
    raw.to_parquet(tmp_path / "raw" / "sol_chain.parquet")
    pd.concat([overlap, live]).to_parquet(tmp_path / "live" / "sol_live_chain.parquet")
    out = livechain.load_chain("SOL", tmp_path / "raw", tmp_path / "live")
    assert out.night.nunique() == 2 and len(out) == 24
    assert set(out[out.night == 1].quote_source) == {"live_book"}
    assert livechain.available_coins(tmp_path / "raw", tmp_path / "live") == ["SOL"]


def test_eth_is_collected_live():
    assert livechain.BASE_OF["ETH"] == "ETH"
