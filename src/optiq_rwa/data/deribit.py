"""Deribit public-history fetcher -> same `chain` schema as data.synthetic.

Uses only public endpoints (no API key):
  history.deribit.com/api/v2/public/get_last_trades_by_currency_and_time
  www.deribit.com/api/v2/public/get_delivery_prices

Trade prints do not carry the order book, so `mid` is the VWAP of trades in a
window around the entry time and bid/ask are rebuilt with the same spread
model as the synthetic market (flagged in column `quote_source`). For true
bid/ask, snapshot the live book daily with `public/get_order_book` going
forward (see scripts/snapshot_books.py idea in README).

Status: written against the public API docs, not yet run end-to-end here
(Deribit is not reachable from the build sandbox). Run locally:
    python -m optiq_rwa.data.deribit --coin SOL --start 2026-02-01 --end 2026-11-01
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import time
import urllib.parse
import urllib.request

import numpy as np
import pandas as pd

from ..pricing import sigma_sqrt_t

HIST = "https://history.deribit.com/api/v2/public/"
LIVE = "https://www.deribit.com/api/v2/public/"
# linear USDC-settled for alts, inverse (coin-settled) for BTC/ETH
SETTINGS = {
    "SOL": {"currency": "USDC", "prefix": "SOL_USDC-", "index": "sol_usdc", "inverse": False},
    "BTC": {"currency": "BTC", "prefix": "BTC-", "index": "btc_usd", "inverse": True},
    "ETH": {"currency": "ETH", "prefix": "ETH-", "index": "eth_usd", "inverse": True},
}
MONTHS = "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()


def _get(base, method, **params):
    url = base + method + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read())["result"]


def _expiry_code(d: dt.date) -> str:
    return f"{d.day}{MONTHS[d.month - 1]}{d.strftime('%y')}"


def delivery_prices(coin: str) -> pd.Series:
    out, offset = [], 0
    while True:
        res = _get(LIVE, "get_delivery_prices", index_name=SETTINGS[coin]["index"], offset=offset, count=1000)
        out += res["data"]
        offset += len(res["data"])
        if offset >= res["records_total"] or not res["data"]:
            break
    s = pd.Series({pd.Timestamp(x["date"]).date(): x["delivery_price"] for x in out})
    return s.sort_index()


def trades_window(coin: str, start: dt.datetime, end: dt.datetime) -> list[dict]:
    cfg, trades, t0 = SETTINGS[coin], [], int(start.timestamp() * 1000)
    t1 = int(end.timestamp() * 1000)
    while t0 < t1:
        res = _get(HIST, "get_last_trades_by_currency_and_time", currency=cfg["currency"], kind="option",
                   start_timestamp=t0, end_timestamp=t1, count=1000, sorting="asc")
        batch = [t for t in res["trades"] if t["instrument_name"].startswith(cfg["prefix"])]
        trades += batch
        if not res.get("has_more") or not res["trades"]:
            break
        t0 = res["trades"][-1]["timestamp"] + 1
        time.sleep(0.1)
    return trades


def build_chain(coin: str, start: str, end: str, entry_hour=19, entry_min=20, window_min=40,
                hours=12.7, spread_pct=0.10, spread_abs=0.0002, event_dates=()) -> pd.DataFrame:
    cfg = SETTINGS[coin]
    settle = delivery_prices(coin)
    rows, night = [], 0
    for d in pd.date_range(start, end, freq="D"):
        expiry = (d + pd.Timedelta(days=1)).date()
        if expiry not in settle.index:
            continue
        entry = dt.datetime(d.year, d.month, d.day, entry_hour, entry_min, tzinfo=dt.timezone.utc)
        tr = trades_window(coin, entry - dt.timedelta(minutes=window_min // 2),
                           entry + dt.timedelta(minutes=window_min // 2))
        code = cfg["prefix"] + _expiry_code(expiry) + "-"
        tr = [t for t in tr if t["instrument_name"].startswith(code)]
        if not tr:
            continue
        df = pd.DataFrame(tr)
        spot = df["index_price"].median()
        df["px_usd"] = df["price"] * (df["index_price"] if cfg["inverse"] else 1.0)
        g = df.groupby("instrument_name").apply(
            lambda x: pd.Series({"vwap": np.average(x.px_usd, weights=x.amount), "iv": x.iv.mean() / 100}))
        atm_iv = g["iv"].median()
        ss = sigma_sqrt_t(atm_iv, hours)
        s_rel = settle[expiry] / spot
        for inst, r in g.iterrows():
            _, _, strike, cp = inst.split("-")
            k_rel = float(strike.replace("d", ".")) / spot
            kind = "call" if cp == "C" else "put"
            mid = r.vwap / spot
            half = spread_pct * mid + spread_abs
            pay = max(s_rel - k_rel, 0) if kind == "call" else max(k_rel - s_rel, 0)
            rows.append(dict(night=night, date=d.date(), coin=coin, kind=kind, m=np.log(k_rel) / ss,
                             k_rel=k_rel, iv=r.iv, iv_atm=atm_iv, mid=mid, bid=max(mid - half, 0),
                             ask=mid + half, settle_rel=s_rel, payoff=pay,
                             event=d.date() in set(event_dates), quote_source="trade_vwap"))
        night += 1
    out = pd.DataFrame(rows)
    # snap continuous moneyness to the grid used by the strategies
    out["m"] = (out["m"] * 2).round() / 2
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--coin", default="SOL")
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--out", default="data/deribit_chain.parquet")
    a = ap.parse_args()
    build_chain(a.coin, a.start, a.end).to_parquet(a.out)
    print("saved", a.out)
