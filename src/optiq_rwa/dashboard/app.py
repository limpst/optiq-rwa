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


def candles(con, minutes: int = 60) -> dict:
    """OHLC per base from index_price snapshots, bucketed to `minutes` (15-min snapshots -> hourly candles)."""
    df = store.read(con, "SELECT s.ts_ms, i.index_name, i.price FROM index_price i JOIN snapshots s USING (snap_id) ORDER BY s.ts_ms")
    out = {}
    if df.empty:
        return out
    df["bucket"] = (df.ts_ms // (minutes * 60_000)) * (minutes * 60)
    for idx, g in df.groupby("index_name"):
        b = idx[:-4].upper() if idx.endswith("_usd") else idx.upper()
        o = g.groupby("bucket").price.agg(["first", "max", "min", "last"])
        out[b] = [{"time": int(t), "open": float(r["first"]), "high": float(r["max"]), "low": float(r["min"]), "close": float(r["last"])} for t, r in o.iterrows()]
    return out


def spread_grid(con, bases, max_snaps: int = 48) -> dict:
    """Strike x snapshot grid of top-of-book relative spread for the nearest expiry (depth collected bases only)."""
    snaps = store.read(con, "SELECT snap_id, ts_ms FROM snapshots ORDER BY snap_id DESC LIMIT ?", (max_snaps,)).sort_values("snap_id")
    if snaps.empty:
        return {}
    ph = ",".join("?" * len(snaps))
    q = f"""SELECT o.snap_id, i.base, i.strike, i.option_type AS kind, i.expiration_ts, o.bid_px, o.ask_px, o.bid_amt, o.ask_amt, i.inverse,
                   st.underlying_price
            FROM order_book o JOIN instruments i USING (instrument_name)
            LEFT JOIN inst_state st ON st.instrument_name=o.instrument_name AND st.snap_id=o.snap_id
            WHERE o.level=0 AND o.snap_id IN ({ph})"""
    df = store.read(con, q, snaps.snap_id.tolist())
    out = {}
    tmap = dict(zip(snaps.snap_id, snaps.ts_ms // 1000))
    for b, g in df.groupby("base"):
        if bases and b not in bases:
            continue
        last_ts = snaps.ts_ms.iloc[-1]
        g = g[g.expiration_ts > last_ts]
        if g.empty:
            continue
        exp = g.expiration_ts.min()
        g = g[(g.expiration_ts == exp) & (g.kind == "call")].copy()
        conv = np.where(g.inverse == 1, g.underlying_price.fillna(1.0), 1.0)
        g["bid"] = g.bid_px * conv; g["ask"] = g.ask_px * conv
        g["mid"] = (g.bid + g.ask) / 2
        g["spread_pct"] = np.where(g.mid > 0, (g.ask - g.bid) / g.mid, np.nan)
        times = sorted(set(tmap[s] for s in g.snap_id))
        strikes = sorted(g.strike.unique())
        ti = {t: i for i, t in enumerate(times)}; ki = {k: i for i, k in enumerate(strikes)}
        cells = [[ti[tmap[r.snap_id]], ki[r.strike], None if pd.isna(r.spread_pct) else round(float(r.spread_pct), 4),
                  None if pd.isna(r.bid) else float(r.bid), None if pd.isna(r.ask) else float(r.ask),
                  None if pd.isna(r.bid_amt) else float(r.bid_amt), None if pd.isna(r.ask_amt) else float(r.ask_amt)]
                 for r in g.itertuples()]
        out[b] = {"times": [int(t) for t in times], "strikes": [float(k) for k in strikes], "kind": "call",
                  "expiry": dt.datetime.fromtimestamp(exp / 1000, dt.timezone.utc).strftime("%d%b%y").upper(), "cells": cells}
    return out


def spread_by_hour(con, target_m: float = 1.0, tol: float = 0.5) -> dict:
    """Median relative spread of the m~+1 call at the nearest expiry, per base and UTC hour, from every snapshot
    with depth (order_book level 0). spread = (ask - bid) / mid; ask_over_mid = ask / mid - 1 (what a buyer pays)."""
    q = """SELECT s.ts_ms, i.base, i.strike, i.expiration_ts, i.inverse, st.mark_iv, st.underlying_price, o.bid_px, o.ask_px
           FROM order_book o JOIN snapshots s USING (snap_id) JOIN instruments i USING (instrument_name)
           JOIN inst_state st ON st.instrument_name = o.instrument_name AND st.snap_id = o.snap_id
           WHERE o.level = 0 AND i.option_type = 'call' AND o.bid_px IS NOT NULL AND o.ask_px IS NOT NULL AND o.ask_px > 0"""
    df = store.read(con, q)
    if df.empty:
        return {}
    df = df[df.expiration_ts > df.ts_ms]
    df["hours"] = (df.expiration_ts - df.ts_ms) / 3.6e6
    df = df[df.hours <= 30]
    df = df.loc[df.groupby(["base", "ts_ms"]).expiration_ts.transform("min") == df.expiration_ts]
    iv = (df.mark_iv.fillna(60) / 100).clip(lower=0.05)
    df["m"] = np.log(df.strike / df.underlying_price) / (iv * np.sqrt(df.hours.clip(lower=0.1) / 8760))
    df = df[(df.m - target_m).abs() <= tol]
    df = df.loc[(df.m - target_m).abs().groupby([df.base, df.ts_ms]).idxmin()]
    conv = np.where(df.inverse == 1, df.underlying_price, 1.0)
    bid, ask = df.bid_px * conv, df.ask_px * conv
    mid = (bid + ask) / 2
    df["spread"] = (ask - bid) / mid
    df["ask_over_mid"] = ask / mid - 1
    df["hour"] = ((df.ts_ms // 3_600_000) % 24).astype(int)
    out = {"by_hour": {}, "overall": {}, "n": int(len(df))}
    for b, g in df.groupby("base"):
        h = g.groupby("hour").agg(spread=("spread", "median"), ask_over_mid=("ask_over_mid", "median"), n=("spread", "size"), hours_to_expiry=("hours", "median")).reset_index()
        out["by_hour"][b] = _records(h.round(4))
        out["overall"][b] = {"spread_med": float(g.spread.median()), "spread_p10": float(g.spread.quantile(0.1)), "spread_p90": float(g.spread.quantile(0.9)),
                             "ask_over_mid_med": float(g.ask_over_mid.median()), "n": int(len(g)), "best_hour": int(h.sort_values("spread").hour.iloc[0]) if len(h) else None}
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


def curves_block() -> dict:
    """Equity curves (TC on/off) + SR/IR/MDD/DSR tables for the real backtest and the synthetic sweep."""
    out = {"real": {}, "sweep": {}, "real_table": [], "sweep_table": [], "highlight": {}}
    try:
        from ..backtest.metrics import HIGHLIGHT
        out["highlight"] = dict(HIGHLIGHT)
    except Exception:
        pass
    nv = RESULTS / "real" / "nav_series.csv"
    if nv.exists():
        ns = pd.read_csv(nv, index_col=0, parse_dates=True)
        for c in ns.columns:
            s_ = ns[c].dropna()
            out["real"][c] = [{"time": int(t.timestamp()), "value": float(v)} for t, v in s_.items()]
    # monthly / weekly period tables for every real curve under base TC (for the period-returns panel)
    out["real_periods"] = {}
    if nv.exists():
        for c in ns.columns:
            if "|base|" not in c:
                continue
            s_ = ns[c].dropna()
            if len(s_) < 5:
                continue
            out["real_periods"][c] = {f: _records(period_table(s_, f, SETTINGS.rwa_rate).round(6)) for f in ("W", "M")}
    sc = RESULTS / "sweep_curves.csv"
    if sc.exists():
        cs = pd.read_csv(sc, index_col=0)
        for c in cs.columns:
            s_ = cs[c].dropna()
            out["sweep"][c] = [{"time": int(i), "value": float(v)} for i, v in s_.items()]
    for p in sorted((RESULTS / "real").glob("strategies_*.csv")):
        out["real_table"] += _records(read_csv(p).round(4))
    sw = read_csv(RESULTS / "sweep_summary.csv")
    if not sw.empty and "cost_model" in sw.columns:
        out["sweep_table"] = _records(sw.round(4))
    return out


def regime_block(con) -> dict:
    """Latest regime per base (risk.regime.classify_live) + monthly label share from results/regime_history.csv."""
    out = {"live": [], "monthly": []}
    try:
        from ..risk.regime import classify_live
        live = classify_live(con)
        out["live"] = _records(live.round(3))
    except Exception as e:          # short live history / missing raw chains must not break the page
        out["error"] = str(e)[:200]
    out["validation"] = _records(read_csv(RESULTS / "regime_validation.csv").round(4))
    nv = {}
    for p in sorted(RESULTS.glob("regime_validation_nav_*.csv")):
        nv[p.stem.split("_")[-1]] = _records(read_csv(p).round(4))
    out["validation_nav"] = nv
    cur = RESULTS / "regime_validation_curves.csv"
    if cur.exists():
        cs = pd.read_csv(cur, index_col=0, parse_dates=True)
        out["validation_curves"] = {c: [{"time": int(t.timestamp()), "value": float(v)} for t, v in cs[c].dropna().items()] for c in cs.columns}
    hist = read_csv(RESULTS / "regime_history.csv")
    if not hist.empty and {"coin", "date", "label"} <= set(hist.columns):
        hist["month"] = pd.to_datetime(hist.date).dt.strftime("%Y-%m")
        share = hist.groupby(["coin", "month"]).label.value_counts(normalize=True).unstack(fill_value=0).reset_index()
        share["nights"] = hist.groupby(["coin", "month"]).size().values
        out["monthly"] = _records(share.round(2))
    return out


def collector_health(con, expected_per_day: int = 96, gap_min: int = 30) -> dict:
    """Last 24h: snapshots vs expected (every 15 min), gaps longer than gap_min, minutes since the last snapshot."""
    now = int(dt.datetime.now(dt.timezone.utc).timestamp() * 1000)
    ts = store.read(con, "SELECT ts_ms FROM snapshots WHERE ts_ms > ? ORDER BY ts_ms", (now - 86_400_000,)).ts_ms.values
    gaps = []
    for a, b in zip(ts[:-1], ts[1:]):
        if b - a > gap_min * 60_000:
            gaps.append({"from": dt.datetime.fromtimestamp(a / 1000, dt.timezone.utc).strftime("%m-%d %H:%M"), "minutes": int((b - a) / 60_000)})
    last_age = int((now - ts[-1]) / 60_000) if len(ts) else None
    # the 15-min job cannot start a new run while the previous (~2-3 min, up to ~470 depth calls) is still running, so the
    # realised cadence is longer than 15 min; coverage is judged against the realised median interval, not 96/day
    med = float(np.median(np.diff(ts)) / 60_000) if len(ts) > 2 else 15.0
    expected = int(round(1440 / max(med, 1.0)))
    return {"n_24h": int(len(ts)), "expected": expected, "expected_nominal": expected_per_day, "median_interval_min": round(med, 1),
            "coverage": float(len(ts) / expected) if expected else None, "gaps": gaps[-8:],
            "minutes_since_last": last_age, "stalled": bool(last_age is not None and last_age > 45)}


def build_bundle(con=None) -> dict:
    con = con or store.connect()
    counts = store.table_counts(con)
    last = store.read(con, "SELECT * FROM snapshots ORDER BY snap_id DESC LIMIT 1")
    uni = store.read(con, "SELECT * FROM volume_daily WHERE date=(SELECT MAX(date) FROM volume_daily) ORDER BY volume_usd DESC")
    uni["volume_krw_eok"] = uni.volume_usd * SETTINGS.usdkrw / 1e8
    vol_hist = store.read(con, "SELECT date, base, volume_usd FROM volume_daily ORDER BY date")
    navs = paper_nav_series(con)
    periods = {k: {f: _records(period_table(v, f, SETTINGS.rwa_rate).round(6)) for f in ("W", "M")} for k, v in navs.items() if len(v) > 1}
    try:
        from ..paper.engine import preview
        prev = _records(preview(con).round(4))
    except Exception as e:
        prev = [{"error": str(e)[:120]}]
    try:
        from ..paper.gate_view import thresholds
        gate_rows = _records(thresholds(con).round(4))
    except Exception as e:
        gate_rows = [{"error": str(e)[:120]}]
    mk = read_csv(RESULTS / "maker_backfill.csv")
    maker = {"legs": _records(mk.round(4)), "summary": []}
    if not mk.empty:
        sm = mk.groupby(["strategy", "side"]).agg(legs=("crossed", "size"), leg_fill=("crossed", "mean"), pkg_fill=("package_filled", "mean"),
                                                 hours_to_fill=("hours_to_fill", "median"), adverse_pct=("adverse_pct", "median"),
                                                 payback_mid_filled=("payback_mid", lambda x: float(np.nanmean(x[mk.loc[x.index, "crossed"]])) if mk.loc[x.index, "crossed"].any() else np.nan)).reset_index()
        maker["summary"] = _records(sm.round(3))
    intr = {"rules": [], "by_base": [], "decay": {}}
    ib = read_csv(RESULTS / "intraday_backfill.csv")
    if not ib.empty:
        sm = ib.groupby("rule").agg(legs=("pnl_per_prem", "size"), mean=("pnl_per_prem", "mean"), median=("pnl_per_prem", "median"), worst=("pnl_per_prem", "min"),
                                     hit=("pnl_per_prem", lambda x: float((x > 0).mean())), closed=("closed", "mean"), exit_h=("exit_hours", "median")).reset_index()
        intr["rules"] = _records(sm.round(4))
        intr["nights"] = int(ib.date.nunique())
    dc = read_csv(RESULTS / "intraday_decay_curve.csv")
    if not dc.empty:
        for (b, k), g in dc.groupby(["base", "kind"]):
            intr["decay"][f"{b}|{k}"] = [{"h": float(r.hours), "r": float(r.ratio)} for r in g.sort_values("hours").itertuples()]
    try:
        from ..paper.engine import STRATEGIES as _S
        roster = [{"name": k, "base": v.get("base", k), "gate": bool(v.get("gate")), "gate_z": v.get("gate_z"), "maker": bool(v.get("maker")),
                   "tp": v.get("tp"), "sl": v.get("sl"), "params": {kk: vv for kk, vv in v.items() if kk in ("m", "budget_mult", "short_m", "wing_m", "frac")}} for k, v in _S.items()]
    except Exception:
        roster = []
    pos = store.read(con, "SELECT strategy, expiry_ts, pnl_usd, settled, exit_reason, side FROM paper_positions")
    pnl_grid = {"dates": [], "strategies": [], "cells": []}
    if not pos.empty:
        pos["night"] = pos.expiry_ts.map(lambda v: store.utc_date(int(v)))
        gsum = pos.groupby(["night", "strategy"]).agg(pnl=("pnl_usd", lambda x: float(np.nansum(x))), n=("pnl_usd", "size"), settled=("settled", "sum"),
                                                    tp=("exit_reason", lambda x: int((x == "tp").sum())), sl=("exit_reason", lambda x: int((x == "sl").sum()))).reset_index()
        # net the trading fees paid on entry (fee_usd lives on the order, not the position) so the cell matches paper_nav's option_pnl
        fees = store.read(con, "SELECT o.strategy, i.expiration_ts, COALESCE(o.fee_usd,0) fee FROM paper_orders o JOIN instruments i USING (instrument_name) WHERE o.status='filled'")
        if not fees.empty:
            fees["night"] = fees.expiration_ts.map(lambda v: store.utc_date(int(v)))
            fsum = fees.groupby(["night", "strategy"]).fee.sum().reset_index()
            gsum = gsum.merge(fsum, on=["night", "strategy"], how="left").fillna({"fee": 0.0})
            gsum["pnl_gross"] = gsum.pnl
            gsum["pnl"] = gsum.pnl - gsum.fee
        # orders that produced no position: gated (idea 8 blocked), unfilled (maker never crossed), resting (maker still waiting)
        ords = store.read(con, "SELECT o.date, o.strategy, o.status, i.expiration_ts FROM paper_orders o JOIN instruments i USING (instrument_name) WHERE o.status IN ('gated','unfilled','resting','rejected')")
        if not ords.empty:
            ords["night"] = ords.expiration_ts.map(lambda v: store.utc_date(int(v)))
            oc = ords.groupby(["night", "strategy", "status"]).size().unstack(fill_value=0).reset_index()
            gsum = gsum.merge(oc, on=["night", "strategy"], how="outer").fillna({"pnl": 0.0, "n": 0, "settled": 0, "tp": 0, "sl": 0})
            for c in ("gated", "unfilled", "resting", "rejected"):
                if c not in gsum:
                    gsum[c] = 0
        roster_names = [r["name"] for r in roster]
        strats = [k for k in roster_names if k in set(gsum.strategy)] + sorted(set(gsum.strategy) - set(roster_names))
        pnl_grid = {"dates": sorted(gsum.night.unique().tolist()), "strategies": strats, "cells": _records(gsum.round(2))}
    paper = {
        "pnl_grid": pnl_grid,
        "roster": roster,
        "intraday": intr,
        "maker": maker,
        "gate": gate_rows,
        "preview": prev,
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
                   "n_snapshots": counts.get("snapshots", 0), "first_date": store.read(con, "SELECT MIN(date) d FROM snapshots").d.iloc[0],
                   "health": collector_health(con)},
        "universe": _records(uni.round(2)),
        "volume_history": _records(vol_hist.round(0)),
        "index_history": index_history(con),
        "candles": candles(con),
        "spread_grid": spread_grid(con, set(uni[uni.universe_pass == 1].base) | set(SETTINGS.focus_bases)),
        "spread_by_hour": spread_by_hour(con),
        "iv_history": atm_iv_history(con),
        "chains": latest_chains(con),
        "paper": paper, "periods": periods, "sweep": sweep_rows, "perp": _records(perp.round(4)) if not perp.empty else [],
        "real": real,
        "regime": regime_block(con),
        "curves": curves_block(),
        "events": _records(read_csv(ROOT / "data" / "events.csv")),
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
