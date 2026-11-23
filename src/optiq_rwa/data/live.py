"""Live Deribit snapshot collector -> SQLite (data.store) + Parquet export.

Public endpoints only (no key). One `snapshot()`:
  1. instruments (USDC / BTC / ETH options)            -> instruments
  2. book summary per currency (3 calls, all options)  -> book_summary, volume_daily (+ universe flag)
  3. index prices                                      -> index_price
  4. order-book depth + greeks for the nearest expiries of universe-pass and focus bases -> order_book, inst_state
  5. delivery (settlement) prices                      -> delivery_price

CLI:
  python -m optiq_rwa.data.live snapshot [--depth 5] [--expiries 2] [--max-m 2.5]
  python -m optiq_rwa.data.live export [--date YYYY-MM-DD]
  python -m optiq_rwa.data.live status
  python -m optiq_rwa.data.live chain --base SOL_USDC
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import time
import urllib.error
import urllib.parse
import urllib.request

import numpy as np
import pandas as pd

from ..config import SETTINGS
from ..pricing import sigma_sqrt_t
from . import store

API = "https://www.deribit.com/api/v2/public/"
CURRENCIES = ("USDC", "BTC", "ETH")


def get(method: str, retries: int = 3, **params):
    url = API + method + "?" + urllib.parse.urlencode(params)
    for i in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                d = json.loads(r.read())
            if "result" in d:
                return d["result"]
            raise RuntimeError(d.get("error"))
        except (urllib.error.URLError, TimeoutError, RuntimeError) as e:
            if i == retries - 1:
                raise
            time.sleep(1.0 + i)


def base_of(instrument_name: str) -> str:
    return instrument_name.split("-")[0]


def index_name_of(base: str) -> str:
    return (base if "_" in base else base + "_USD").lower()


def now_ms() -> int:
    return int(time.time() * 1000)


# ------------------------------------------------------------------ steps
def fetch_instruments(ts_ms: int) -> pd.DataFrame:
    rows = []
    for cur in CURRENCIES:
        for x in get("get_instruments", currency=cur, kind="option", expired="false"):
            rows.append(dict(instrument_name=x["instrument_name"], base=base_of(x["instrument_name"]),
                             currency=x.get("quote_currency", cur), settlement_currency=x.get("settlement_currency"),
                             option_type=x["option_type"], strike=x["strike"], expiration_ts=x["expiration_timestamp"],
                             contract_size=x.get("contract_size"), inverse=int(x.get("settlement_currency") not in ("USDC", "USDT")),
                             tick_size=x.get("tick_size"), min_trade_amount=x.get("min_trade_amount"), first_seen_ms=ts_ms, last_seen_ms=ts_ms))
    return pd.DataFrame(rows)


def fetch_summaries(snap_id: int) -> pd.DataFrame:
    rows = []
    for cur in CURRENCIES:
        for x in get("get_book_summary_by_currency", currency=cur, kind="option"):
            bid, ask = x.get("bid_price"), x.get("ask_price")
            rows.append(dict(snap_id=snap_id, instrument_name=x["instrument_name"], bid=bid, ask=ask,
                             mid=(bid + ask) / 2 if bid is not None and ask is not None else None,
                             mark_price=x.get("mark_price"), mark_iv=x.get("mark_iv"), volume=x.get("volume"),
                             volume_usd=x.get("volume_usd"), open_interest=x.get("open_interest"),
                             underlying_price=x.get("underlying_price")))
    return pd.DataFrame(rows)


def volume_table(summ: pd.DataFrame, date: str) -> pd.DataFrame:
    s = summ.assign(base=summ.instrument_name.map(base_of))
    g = s.groupby("base").agg(volume_usd=("volume_usd", "sum"), n_traded=("volume", lambda v: int((v.fillna(0) > 0).sum())),
                              n_listed=("instrument_name", "count")).reset_index()
    g["date"] = date
    g["universe_pass"] = (g.volume_usd >= SETTINGS.min_daily_volume_usd).astype(int)
    return g[["date", "base", "volume_usd", "n_traded", "n_listed", "universe_pass"]]


def fetch_index_prices(snap_id: int, bases) -> pd.DataFrame:
    rows = []
    for b in sorted(set(bases)):
        try:
            rows.append(dict(snap_id=snap_id, index_name=index_name_of(b), price=get("get_index_price", index_name=index_name_of(b))["index_price"]))
        except Exception:
            continue
        time.sleep(0.05)
    return pd.DataFrame(rows)


def pick_depth_instruments(inst: pd.DataFrame, summ: pd.DataFrame, bases, ts_ms: int, max_expiries=2, max_abs_m=2.5, max_abs_m_later=1.5) -> pd.DataFrame:
    """Nearest `max_expiries` expiries per base, strikes within |m| <= max_abs_m (m in sigma*sqrt(T) units from mark_iv).
    Expiries after the nearest one keep only |m| <= max_abs_m_later: the paper engine trades the nearest expiry at 19:20 UTC
    and needs its full wing range for fills / tp-sl, while later expiries only feed the IV history (cuts ~30% of calls)."""
    df = inst[inst.base.isin(bases) & (inst.expiration_ts > ts_ms)].merge(
        summ[["instrument_name", "mark_iv", "underlying_price"]], on="instrument_name", how="left")
    keep = []
    for b, g in df.groupby("base"):
        exps = sorted(g.expiration_ts.unique())[:max_expiries]
        g = g[g.expiration_ts.isin(exps)].copy()
        hours = (g.expiration_ts - ts_ms) / 3.6e6
        iv = g.mark_iv.fillna(g.mark_iv.median()).fillna(60.0) / 100
        ss = sigma_sqrt_t(iv.values, hours.values)
        g["m"] = np.log(g.strike / g.underlying_price) / ss
        lim = np.where(g.expiration_ts == exps[0], max_abs_m, max_abs_m_later)
        keep.append(g[g.m.abs() <= lim])
    return pd.concat(keep) if keep else df.iloc[0:0]


def fetch_depth(snap_id: int, names, depth=5, pause=0.06, workers: int = 1):
    """Order-book depth + greeks for `names`. Sequential by default: a 4-thread pool was measured 2026-11-23 at
    0.71 s/request vs 0.92 s sequential but lost 11 of 40 instruments to Deribit throttling (429 -> None after retries),
    so parallelism is opt-in (workers > 1) and data completeness wins. Realised cadence is ~23 min for ~470 instruments."""
    from concurrent.futures import ThreadPoolExecutor

    def one(name):
        try:
            r = get("get_order_book", instrument_name=name, depth=depth)
        except Exception:
            return name, None
        time.sleep(pause)
        return name, r

    ob_rows, st_rows = [], []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(one, list(names)))
    for name, r in results:
        if r is None:
            continue
        bids, asks = r.get("bids", []), r.get("asks", [])
        for lvl in range(max(len(bids), len(asks))):
            b = bids[lvl] if lvl < len(bids) else (None, None)
            a = asks[lvl] if lvl < len(asks) else (None, None)
            ob_rows.append(dict(snap_id=snap_id, instrument_name=name, level=lvl, bid_px=b[0], bid_amt=b[1], ask_px=a[0], ask_amt=a[1]))
        gk = r.get("greeks", {}) or {}
        st_rows.append(dict(snap_id=snap_id, instrument_name=name, mark_price=r.get("mark_price"), mark_iv=r.get("mark_iv"),
                            bid_iv=r.get("bid_iv"), ask_iv=r.get("ask_iv"), delta=gk.get("delta"), gamma=gk.get("gamma"),
                            vega=gk.get("vega"), theta=gk.get("theta"), index_price=r.get("index_price"),
                            underlying_price=r.get("underlying_price"), open_interest=r.get("open_interest"),
                            interest_rate=r.get("interest_rate")))
    return pd.DataFrame(ob_rows), pd.DataFrame(st_rows)


def fetch_delivery(bases, count=10) -> pd.DataFrame:
    rows = []
    for b in sorted(set(bases)):
        idx = index_name_of(b)
        try:
            for x in get("get_delivery_prices", index_name=idx, count=count)["data"]:
                rows.append(dict(index_name=idx, date=x["date"], price=x["delivery_price"]))
        except Exception:
            continue
        time.sleep(0.05)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ main entry
def snapshot(con=None, depth=5, max_expiries=2, max_abs_m=2.5, log=print, summary_max_days: float = 8.0) -> dict:
    """One collection run. Writes are committed per stage so the 15-min job never holds a write lock for
    the whole ~100 s run (the paper engine and the dashboard share this file).

    summary_max_days: keep book_summary rows only for expiries within this many days (volume filter still
    uses every listed option before the cut). 8 days ~ halves storage. None = keep all."""
    con = con or store.connect()
    con.execute("PRAGMA busy_timeout=60000")
    t0, ts = time.time(), now_ms()
    date = store.utc_date(ts)
    cur = con.execute("INSERT INTO snapshots (ts_ms, date) VALUES (?, ?)", (ts, date))
    snap_id = cur.lastrowid
    con.commit()
    inst = fetch_instruments(ts)
    # keep first_seen from the existing row
    seen = store.read(con, "SELECT instrument_name, first_seen_ms FROM instruments")
    if not seen.empty:
        inst = inst.merge(seen, on="instrument_name", how="left", suffixes=("", "_old"))
        inst["first_seen_ms"] = inst.first_seen_ms_old.fillna(inst.first_seen_ms).astype("int64")
        inst = inst.drop(columns="first_seen_ms_old")
    store.insert_df(con, "instruments", inst)
    con.commit()
    summ = fetch_summaries(snap_id)
    vol = volume_table(summ, date)                      # volume filter on every listed option
    if summary_max_days is not None:
        near = set(inst[inst.expiration_ts <= ts + summary_max_days * 86_400_000].instrument_name)
        summ = summ[summ.instrument_name.isin(near)]
    store.insert_df(con, "book_summary", summ)
    con.commit()
    # volume_usd from Deribit is a rolling 24h figure -> keep the daily max
    old = store.read(con, "SELECT base, volume_usd FROM volume_daily WHERE date=?", (date,))
    if not old.empty:
        vol = vol.merge(old, on="base", how="left", suffixes=("", "_old"))
        vol["volume_usd"] = vol[["volume_usd", "volume_usd_old"]].max(axis=1)
        vol["universe_pass"] = (vol.volume_usd >= SETTINGS.min_daily_volume_usd).astype(int)
        vol = vol.drop(columns="volume_usd_old")
    store.insert_df(con, "volume_daily", vol)
    bases = sorted(set(vol.base))
    store.insert_df(con, "index_price", fetch_index_prices(snap_id, bases))
    con.commit()
    depth_bases = set(vol[vol.universe_pass == 1].base) | set(SETTINGS.focus_bases)
    picked = pick_depth_instruments(inst, summ, depth_bases, ts, max_expiries, max_abs_m)
    ob, st = fetch_depth(snap_id, picked.instrument_name.tolist(), depth=depth)
    store.insert_df(con, "order_book", ob)
    store.insert_df(con, "inst_state", st)
    con.commit()
    store.insert_df(con, "delivery_price", fetch_delivery(bases))
    secs = time.time() - t0
    con.execute("UPDATE snapshots SET n_summary=?, n_depth=?, seconds=? WHERE snap_id=?", (len(summ), len(st), secs, snap_id))
    con.commit()
    info = dict(snap_id=snap_id, date=date, ts_ms=ts, n_instruments=len(inst), n_summary=len(summ), n_depth=len(st),
                depth_bases=sorted(depth_bases), universe_pass=sorted(vol[vol.universe_pass == 1].base), seconds=round(secs, 1))
    log(json.dumps(info))
    return info


def live_chain(con, snap_id: int | None = None, base: str = "SOL_USDC", expiry_rank: int = 0) -> pd.DataFrame:
    """Chain in the synthetic schema (prices relative to spot) for one base and one expiry at a snapshot.

    Uses order-book top (inst_state/order_book) when present, else book_summary. Columns:
    instrument_name, kind, strike, k_rel, m, iv, iv_atm, mid, bid, ask, hours, spot, expiration_ts, quote_source.
    """
    snap_id = snap_id or store.latest_snap_id(con)
    ts = con.execute("SELECT ts_ms FROM snapshots WHERE snap_id=?", (snap_id,)).fetchone()[0]
    q = """SELECT i.instrument_name, i.option_type AS kind, i.strike, i.expiration_ts, i.inverse,
                  COALESCE(s.mark_iv, b.mark_iv) AS mark_iv, s.bid_iv, s.ask_iv,
                  COALESCE(s.underlying_price, b.underlying_price) AS spot, s.index_price,
                  o.bid_px, o.ask_px, b.bid AS sb, b.ask AS sa, b.mark_price, s.delta
           FROM instruments i
           JOIN book_summary b ON b.instrument_name=i.instrument_name AND b.snap_id=?
           LEFT JOIN inst_state s ON s.instrument_name=i.instrument_name AND s.snap_id=?
           LEFT JOIN order_book o ON o.instrument_name=i.instrument_name AND o.snap_id=? AND o.level=0
           WHERE i.base=? AND i.expiration_ts>?"""
    df = store.read(con, q, (snap_id, snap_id, snap_id, base, ts))
    if df.empty:
        return df
    exps = sorted(df.expiration_ts.unique())
    if expiry_rank >= len(exps):
        return df.iloc[0:0]
    df = df[df.expiration_ts == exps[expiry_rank]].copy()
    df["bid"] = df.bid_px.fillna(df.sb)
    df["ask"] = df.ask_px.fillna(df.sa)
    df["quote_source"] = np.where(df.bid_px.notna() | df.ask_px.notna(), "order_book", "book_summary")
    # inverse (BTC/ETH) quotes are in coin -> convert to USD
    conv = np.where(df.inverse == 1, df.spot, 1.0)
    for c in ("bid", "ask", "mark_price"):
        df[c] = df[c] * conv
    df["mid"] = np.where(df.bid.notna() & df.ask.notna(), (df.bid + df.ask) / 2, df.mark_price)
    df["hours"] = (df.expiration_ts - ts) / 3.6e6
    df["iv"] = df.mark_iv / 100
    df["k_rel"] = df.strike / df.spot
    atm = df.iloc[(df.k_rel - 1).abs().argsort()[:2]]
    df["iv_atm"] = atm.iv.mean()
    ss = sigma_sqrt_t(df.iv_atm.values, df.hours.values)
    df["m"] = np.log(df.k_rel) / ss
    for c in ("bid", "ask", "mid"):
        df[c + "_rel"] = df[c] / df.spot
    cols = ["instrument_name", "kind", "strike", "k_rel", "m", "iv", "bid_iv", "ask_iv", "iv_atm", "delta", "bid", "ask", "mid",
            "bid_rel", "ask_rel", "mid_rel", "hours", "spot", "expiration_ts", "quote_source"]
    return df[cols].sort_values(["kind", "strike"]).reset_index(drop=True)


def status(con) -> dict:
    out = store.table_counts(con)
    last = store.read(con, "SELECT * FROM snapshots ORDER BY snap_id DESC LIMIT 1")
    out["last_snapshot"] = last.iloc[0].to_dict() if not last.empty else None
    out["universe_today"] = store.read(con, "SELECT base, volume_usd, universe_pass FROM volume_daily WHERE date=(SELECT MAX(date) FROM volume_daily) ORDER BY volume_usd DESC").to_dict("records")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["snapshot", "export", "status", "chain"])
    ap.add_argument("--depth", type=int, default=5)
    ap.add_argument("--expiries", type=int, default=2)
    ap.add_argument("--max-m", type=float, default=2.5)
    ap.add_argument("--date")
    ap.add_argument("--base", default="SOL_USDC")
    ap.add_argument("--summary-days", type=float, default=8.0, help="keep book_summary rows for expiries within N days (0 = all)")
    a = ap.parse_args()
    con = store.connect()
    if a.cmd == "snapshot":
        snapshot(con, depth=a.depth, max_expiries=a.expiries, max_abs_m=a.max_m, summary_max_days=(a.summary_days or None))
    elif a.cmd == "export":
        for f in store.export_parquet(con, a.date):
            print("wrote", f)
    elif a.cmd == "status":
        print(json.dumps(status(con), indent=1, default=str))
    elif a.cmd == "chain":
        pd.set_option("display.width", 200, "display.max_columns", 30)
        print(live_chain(con, base=a.base).round(4).to_string())
