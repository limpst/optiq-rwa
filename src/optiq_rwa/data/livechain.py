"""Nightly chains from the live order-book store, in the same schema as data/raw/*_chain.parquet (deribit.build_chain).

Why: data/raw chains are trade-VWAP quotes with a *modelled* spread (history). The live store holds real best bid / ask
(order book level 0, else book summary) every 15 minutes, so each settled night adds one out-of-sample night with
quotes that could actually have been traded. Walk-forward scripts call `load_chain(coin)` = raw history + live nights
appended after the last raw date, renumbered by date.

Per UTC date: the snapshot closest to the entry time (19:20 UTC, ±tol_min) -> nearest expiry 6-26 h ahead
(normally the next 08:00 UTC daily) -> settle at Deribit's delivery price for the expiry date.

CLI (repo root, PYTHONPATH=src):  python -m optiq_rwa.data.livechain build
"""
from __future__ import annotations

import argparse
import pathlib

import numpy as np
import pandas as pd

from ..config import ROOT
from . import store
from .live import index_name_of, live_chain

RAW_DIR, LIVE_DIR = ROOT / "data" / "raw", ROOT / "data" / "live"
BASE_OF = {"BTC": "BTC", "ETH": "ETH", "SOL": "SOL_USDC"}   # coin label (raw chains) -> live base; ETH is live-only
COLS = ["night", "date", "coin", "kind", "m", "k_rel", "iv", "iv_atm", "mid", "bid", "ask", "settle_rel", "payoff",
        "event", "quote_source"]


def _entry_snaps(con, entry_hour: int, entry_min: int, tol_min: int) -> pd.DataFrame:
    s = store.read(con, "SELECT snap_id, ts_ms, date FROM snapshots ORDER BY ts_ms")
    if s.empty:
        return s
    ts = pd.to_datetime(s.ts_ms, unit="ms", utc=True)
    target = ts.dt.normalize() + pd.Timedelta(hours=entry_hour, minutes=entry_min)
    s["gap_min"] = ((ts - target).dt.total_seconds() / 60).abs()
    s["date"] = ts.dt.date
    s = s[s.gap_min <= tol_min]
    return s.loc[s.groupby("date").gap_min.idxmin()].sort_values("ts_ms") if not s.empty else s


def build_live_chain(con, coin: str, entry_hour=19, entry_min=20, tol_min=40, min_hours=6.0, max_hours=26.0,
                     event_dates=()) -> pd.DataFrame:
    base = BASE_OF[coin]
    idx = index_name_of(base)
    ev = set(event_dates)
    rows = []
    for snap in _entry_snaps(con, entry_hour, entry_min, tol_min).itertuples():
        ch = pd.DataFrame()
        for rank in (0, 1):
            c = live_chain(con, int(snap.snap_id), base, rank)
            if not c.empty and min_hours <= c.hours.iloc[0] <= max_hours:
                ch = c
                break
        if ch.empty:
            continue
        exp_date = pd.to_datetime(int(ch.expiration_ts.iloc[0]), unit="ms", utc=True).strftime("%Y-%m-%d")
        px = con.execute("SELECT price FROM delivery_price WHERE index_name=? AND date=?", (idx, exp_date)).fetchone()
        if not px:
            continue                                   # not settled yet
        ch = ch[np.isfinite(ch.bid_rel) & np.isfinite(ch.ask_rel) & (ch.ask_rel > 0) & np.isfinite(ch.m)].copy()
        if ch.empty:
            continue
        s_rel = px[0] / float(ch.spot.iloc[0])
        pay = np.where(ch.kind == "call", np.maximum(s_rel - ch.k_rel, 0), np.maximum(ch.k_rel - s_rel, 0))
        rows.append(pd.DataFrame(dict(night=0, date=snap.date, coin=coin, kind=ch.kind.values, m=(ch.m * 2).round().values / 2,
                                      k_rel=ch.k_rel.values, iv=ch.iv.values, iv_atm=ch.iv_atm.values, mid=ch.mid_rel.values,
                                      bid=ch.bid_rel.values, ask=ch.ask_rel.values, settle_rel=s_rel, payoff=pay,
                                      event=snap.date in ev, quote_source="live_book")))
    if not rows:
        return pd.DataFrame(columns=COLS)
    out = pd.concat(rows, ignore_index=True)
    out["night"] = out.date.rank(method="dense").astype(int) - 1
    return out[COLS]


def load_chain(coin: str, raw_dir: pathlib.Path = RAW_DIR, live_dir: pathlib.Path = LIVE_DIR) -> pd.DataFrame:
    """Raw history + live nights after the last raw date, nights renumbered 0..N-1 by date."""
    parts = []
    raw_f, live_f = pathlib.Path(raw_dir) / f"{coin.lower()}_chain.parquet", pathlib.Path(live_dir) / f"{coin.lower()}_live_chain.parquet"
    raw = pd.read_parquet(raw_f) if raw_f.exists() else pd.DataFrame()
    if not raw.empty:
        raw = raw.assign(date=pd.to_datetime(raw.date).dt.date)
        parts.append(raw)
    if live_f.exists():
        live = pd.read_parquet(live_f)
        if not live.empty:
            live = live.assign(date=pd.to_datetime(live.date).dt.date)
            if not raw.empty:
                live = live[live.date > raw.date.max()]
            parts.append(live)
    if not parts:
        return pd.DataFrame(columns=COLS)
    out = pd.concat(parts, ignore_index=True)
    out["night"] = out.date.rank(method="dense").astype(int) - 1
    return out.sort_values(["night", "kind", "k_rel"]).reset_index(drop=True)


def available_coins(raw_dir: pathlib.Path = RAW_DIR, live_dir: pathlib.Path = LIVE_DIR) -> list[str]:
    names = {f.name.split("_")[0].upper() for d in (raw_dir, live_dir) for f in pathlib.Path(d).glob("*chain.parquet")}
    return sorted(names)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build"])
    ap.add_argument("--tol-min", type=int, default=40)
    a = ap.parse_args()
    try:
        from .events import event_dates
        ev = event_dates(("FOMC", "CPI"))
    except Exception:
        ev = ()
    con = store.connect()
    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    for coin in BASE_OF:
        df = build_live_chain(con, coin, tol_min=a.tol_min, event_dates=ev)
        df.to_parquet(LIVE_DIR / f"{coin.lower()}_live_chain.parquet", index=False)
        print(f"{coin}: {df.night.nunique() if len(df) else 0} live nights, {len(df)} rows")


if __name__ == "__main__":
    main()
