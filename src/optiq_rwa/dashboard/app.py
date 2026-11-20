"""OptiQ-RWA dashboard: FastAPI + TradingView lightweight-charts.

    PYTHONPATH=src uvicorn optiq_rwa.dashboard.app:app --port 8793 --reload
    open http://127.0.0.1:8793

The page (static/index.html) fetches /api/all. scripts/export_dashboard.py inlines the same
bundle into the page as a static snapshot (docs/index.html) for publishing as an artifact.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib

import numpy as np
import pandas as pd
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

from ..config import ROOT, SETTINGS
from ..data import store
from ..data.live import live_chain
from ..backtest.periods import period_table, paper_nav_series

STATIC = pathlib.Path(__file__).parent / "static"
RESULTS = ROOT / "results"


def _records(df: pd.DataFrame) -> list[dict]:
    if df is None or df.empty:
        return []
    df = df.replace({np.nan: None, np.inf: None, -np.inf: None})
    out = []
    for r in df.to_dict("records"):
        out.append({k: (v.isoformat() if hasattr(v, "isoformat") else (float(v) if isinstance(v, (np.floating,)) else (int(v) if isinstance(v, np.integer) else v)))
                    for k, v in r.items()})
    return out


def _series(df: pd.DataFrame, tcol: str, vcol: str, ms: bool = True) -> list[dict]:
    if df.empty:
        return []
    t = (df[tcol] // 1000).astype(int) if ms else pd.to_datetime(df[tcol]).astype("int64") // 10**9
    return [{"time": int(a), "value": float(b)} for a, b in zip(t, df[vcol]) if b is not None and np.isfinite(b)]


def index_history(con) -> dict:
    df = store.read(con, "SELECT s.ts_ms, i.index_name, i.price FROM index_price i JOIN snapshots s USING (snap_id) ORDER BY s.ts_ms")
    def base(idx: str) -> str:           # btc_usd -> BTC, sol_usdc -> SOL_USDC
        return idx[:-4].upper() if idx.endswith("_usd") else idx.upper()
    return {base(k): _series(g, "ts_ms", "price") for k, g in df.groupby("index_name")}


def atm_iv_history(con) -> dict:
    """ATM mark IV per snapshot per base: strike closest to the underlying at the nearest expiry (needs inst_state)."""
    q = """SELECT s.ts_ms, i.base, i.strike, i.expiration_ts, st.mark_iv, st.underlying_price
           FROM inst_state st JOIN snapshots s USING (snap_id) JOIN instruments i USING (instrument_name)
           WHERE st.mark_iv IS NOT NULL AND st.underlying_price IS NOT NULL"""
    df = store.read(con, q)
    out = {}
    if df.empty:
        return out
    df["dist"] = (df.strike / df.underlying_price - 1).abs()
    for (b, ts), g in df.groupby(["base", "ts_ms"]):
        g = g[g.expiration_ts == g.expiration_ts.min()]
        row = g.loc[g.dist.idxmin()]
        out.setdefault(b, []).append({"time": int(ts // 1000), "value": float(row.mark_iv)})
    return out


def latest_chains(con) -> dict:
    snap = store.latest_snap_id(con)
    if snap is None:
        return {}
    bases = store.read(con, "SELECT DISTINCT base FROM instruments").base.tolist()
    out = {}
    for b in bases:
        for rank in (0, 1):
            ch = live_chain(con, snap, b, rank)
            if not ch.empty and ch.hours.iloc[0] >= 1.0:
                ch = ch[(ch.m.abs() <= 3.0)]
                out[b] = {"rank": rank, "hours": float(ch.hours.iloc[0]), "spot": float(ch.spot.iloc[0]),
                          "iv_atm": float(ch.iv_atm.iloc[0]), "rows": _records(ch.round(5))}
                break
    return out


def read_csv(p: pathlib.Path) -> pd.DataFrame:
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


def build_bundle(con=None) -> dict:
    con = con or store.connect()
    counts = store.table_counts(con)
    last = store.read(con, "SELECT * FROM snapshots ORDER BY snap_id DESC LIMIT 1")
    uni = store.read(con, "SELECT * FROM volume_daily WHERE date=(SELECT MAX(date) FROM volume_daily) ORDER BY volume_usd DESC")
    uni["volume_krw_eok"] = uni.volume_usd * SETTINGS.usdkrw / 1e8
    vol_hist = store.read(con, "SELECT date, base, volume_usd FROM volume_daily ORDER BY date")
    navs = paper_nav_series(con)
    periods = {k: {f: _records(period_table(v, f, SETTINGS.rwa_rate).round(6)) for f in ("W", "M")} for k, v in navs.items() if len(v) > 1}
    paper = {
        "nav": _records(store.read(con, "SELECT * FROM paper_nav ORDER BY date")),
        "nav_series": {k: _series(v.reset_index(), "date", "nav", ms=False) for k, v in navs.items()},
        "orders": _records(store.read(con, "SELECT * FROM paper_orders ORDER BY order_id DESC LIMIT 100").round(4)),
        "positions": _records(store.read(con, "SELECT * FROM paper_positions ORDER BY pos_id DESC LIMIT 100").round(4)),
    }
    sweep = read_csv(RESULTS / "sweep_summary.csv")
    if not sweep.empty:
        cols = ["ann_return", "excess_vs_rwa", "sharpe_vs_rwa", "max_drawdown", "cvar5_night", "seed_min_ret"]
        best = sweep.sort_values("sharpe_vs_rwa", ascending=False).groupby(["scenario", "idea"]).head(1).sort_values(["scenario", "idea"])
        sweep_rows = _records(best[["scenario", "idea", "params"] + cols].round(4))
    else:
        sweep_rows = []
    real = {"strategies": [], "calibration": [], "nav_series": {}}
    for p in sorted((RESULTS / "real").glob("strategies_*.csv")):
        real["strategies"] += _records(read_csv(p).round(4))
    for p in sorted((RESULTS / "real").glob("calibration_*.csv")):
        real["calibration"] += _records(read_csv(p).round(4))
    nv = RESULTS / "real" / "nav_series.csv"
    if nv.exists():
        ns = pd.read_csv(nv, index_col=0, parse_dates=True)
        for c in ns.columns:
            s = ns[c].dropna()
            real["nav_series"][c] = [{"time": int(t.timestamp()), "value": float(v)} for t, v in s.items()]
    perp = read_csv(RESULTS / "perp_vs_option.csv")
    if not perp.empty:
        perp = perp[(perp.scenario == "base") & (perp.nights == "all")].groupby("instrument", sort=False)[["mean_ret", "p_profit", "p_lose_all", "liquidation_rate", "cvar5"]].mean().reset_index()
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "config": {"min_daily_volume_krw": SETTINGS.min_daily_volume_krw, "usdkrw": SETTINGS.usdkrw, "rwa_rate": SETTINGS.rwa_rate,
                   "focus_bases": list(SETTINGS.focus_bases), "db": str(SETTINGS.db_path.relative_to(ROOT))},
        "status": {"counts": counts, "last_snapshot": _records(last)[0] if not last.empty else None,
                   "n_snapshots": counts.get("snapshots", 0), "first_date": store.read(con, "SELECT MIN(date) d FROM snapshots").d.iloc[0]},
        "universe": _records(uni.round(2)),
        "volume_history": _records(vol_hist.round(0)),
        "index_history": index_history(con),
        "iv_history": atm_iv_history(con),
        "chains": latest_chains(con),
        "paper": paper, "periods": periods, "sweep": sweep_rows, "perp": _records(perp.round(4)) if not perp.empty else [],
        "real": real,
    }


app = FastAPI(title="OptiQ-RWA dashboard")


@app.get("/api/all")
def api_all():
    return JSONResponse(json.loads(json.dumps(build_bundle(), default=str)))


WRAP_HEAD = '<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"></head><body>'
WRAP_TAIL = "</body></html>"


def full_document(fragment: str) -> str:
    """static/index.html is written in the artifact shape (no doctype/head/body); wrap it for a browser."""
    return WRAP_HEAD + fragment + WRAP_TAIL


@app.get("/", response_class=HTMLResponse)
def index():
    return full_document((STATIC / "index.html").read_text())
