"""Idea 8 — execution-economics gate: trade a package only when expected edge − transaction cost > 0.

Expected settlement value of an option = calibrated payback-at-mid × live mid, where the payback ratio comes from
idea 4 (results/real/calibration_{COIN}.csv: realised payoff / mid per coin × kind × m × event bucket), shrunk toward
the pooled (kind × m × event) estimate with weight n / (n + prior_n). Costs are what the paper engine actually pays:
the spread (fill at ask / bid) plus the Deribit trading fee (CostModel.fee). Settlement fee is 0 for daily options.

    buy leg  edge = E[payoff] − ask − fee(ask)
    sell leg edge = bid − fee(bid) − E[payoff]

A strategy's orders for one base form a package (a condor's wings are protection, not a separate bet), so the gate
passes or blocks the whole package on the sum of leg edges (USD).

Recalibration on live quotes: once data/live/{coin}_live_chain.parquet holds settled nights (data.livechain), each
bucket's payback is pulled toward the live estimate with weight n_live / (n_live + prior_n), so the gate moves from
modelled-spread history to tradable-quote evidence as nights accumulate.

Lower-bound rule: the gate uses a one-sided bound, not the point estimate — buys use payback − z·se, sells use
payback + z·se (z = GATE_Z, default 1.645 = 5% quantile). se of a payback ratio is approximated from the ITM rate p and
bucket size n as payback · sqrt((1 − p) / (n · p)) (payoff concentrated in ITM nights), so thin buckets need a larger
edge to pass.
"""
from __future__ import annotations

import os
import pathlib

import numpy as np
import pandas as pd

from ..backtest.costs import BASE as COST_MODEL
from ..config import ROOT

CAL_DIR, LIVE_DIR = ROOT / "results" / "real", ROOT / "data" / "live"
PRIOR_N = 60.0
GATE_Z = float(os.environ.get("OPTIQ_GATE_Z", 1.645))
KEYS = ["coin", "kind", "m", "event"]
COIN_OF = {"BTC": "BTC", "BTC_USDC": "BTC", "SOL_USDC": "SOL", "SOL": "SOL", "ETH": "ETH"}   # others: pooled table


def _se(payback, p, n):
    p = np.clip(np.asarray(p, float), 1.0 / np.maximum(np.asarray(n, float), 1.0), 1.0)
    return np.asarray(payback, float) * np.sqrt((1 - p) / (np.maximum(np.asarray(n, float), 1.0) * p))


def _live_calibration(live_dir: pathlib.Path) -> pd.DataFrame:
    from ..risk.calibration import calibration_table
    parts = [pd.read_parquet(f) for f in sorted(pathlib.Path(live_dir).glob("*_live_chain.parquet"))]
    parts = [p for p in parts if not p.empty]
    if not parts:
        return pd.DataFrame(columns=KEYS + ["n", "payback_mid", "p_itm_emp"])
    return calibration_table(pd.concat(parts, ignore_index=True))[KEYS + ["n", "payback_mid", "p_itm_emp"]]


def load_payback(cal_dir: pathlib.Path = CAL_DIR, prior_n: float = PRIOR_N, live_dir: pathlib.Path = LIVE_DIR) -> pd.DataFrame:
    """Shrunk payback-at-mid and its se per (coin, kind, m, event); coin='*' rows are the pooled estimate.

    History (cal_dir) is shrunk toward the pooled bucket, then pulled toward live-quote nights (live_dir) if any."""
    cols = KEYS + ["n", "payback", "se", "n_live"]
    files = sorted(pathlib.Path(cal_dir).glob("calibration_*.csv"))
    t = pd.concat(pd.read_csv(f) for f in files) if files else pd.DataFrame(columns=KEYS + ["n", "payback_mid", "p_itm_emp"])
    live = _live_calibration(live_dir) if pathlib.Path(live_dir).exists() else pd.DataFrame()
    if not live.empty:   # live buckets with no history still enter (history n = 0)
        t = t.merge(live, on=KEYS, how="outer", suffixes=("", "_live"))
    else:
        t = t.assign(n_live=0.0, payback_mid_live=np.nan, p_itm_emp_live=np.nan)
    t["n"] = t.n.fillna(0.0); t["n_live"] = t.n_live.fillna(0.0)
    t = t[(t.n > 0) | (t.n_live > 0)].copy()
    if t.empty:
        return pd.DataFrame(columns=cols)
    hist_ok = np.isfinite(t.payback_mid) & (t.n > 0)
    t["w_pay"] = np.where(hist_ok, t.payback_mid * t.n, 0.0)
    t["w_itm"] = np.where(hist_ok, t.p_itm_emp.fillna(0) * t.n, 0.0)
    t["n_h"] = np.where(hist_ok, t.n, 0.0)
    pool = t.groupby(["kind", "m", "event"], as_index=False).agg(n_pool=("n_h", "sum"), w_pay=("w_pay", "sum"), w_itm=("w_itm", "sum"))
    pool = pool[pool.n_pool > 0]
    pool["payback_pool"] = pool.w_pay / pool.n_pool
    pool["p_pool"] = pool.w_itm / pool.n_pool
    pool["se_pool"] = _se(pool.payback_pool, pool.p_pool, pool.n_pool)
    t = t.drop(columns=["w_pay", "w_itm"]).merge(pool[["kind", "m", "event", "payback_pool", "se_pool"]], on=["kind", "m", "event"], how="left")
    # 1) history: bucket shrunk toward pooled bucket
    w = t.n_h / (t.n_h + prior_n)
    se_b = _se(t.payback_mid.fillna(0), t.p_itm_emp.fillna(0), t.n_h)
    hist = np.where(hist_ok, w * t.payback_mid + (1 - w) * t.payback_pool, t.payback_pool)
    hist_se = np.where(hist_ok, np.sqrt((w * se_b) ** 2 + ((1 - w) * t.se_pool) ** 2), t.se_pool)
    # 2) live quotes: pull toward the live estimate with weight n_live / (n_live + prior_n)
    live_ok = np.isfinite(t.payback_mid_live) & (t.n_live > 0)
    wl = np.where(live_ok, t.n_live / (t.n_live + prior_n), 0.0)
    se_l = _se(t.payback_mid_live.fillna(0), t.p_itm_emp_live.fillna(0), t.n_live)
    base = np.where(np.isfinite(hist), hist, t.payback_mid_live)
    base_se = np.where(np.isfinite(hist_se), hist_se, se_l)
    wl = np.where(np.isfinite(hist), wl, 1.0)
    t["payback"] = np.where(live_ok, wl * t.payback_mid_live.fillna(0) + (1 - wl) * np.nan_to_num(base), base)
    t["se"] = np.where(live_ok, np.sqrt((wl * se_l) ** 2 + ((1 - wl) * np.nan_to_num(base_se)) ** 2), base_se)
    out = t[np.isfinite(t.payback)][cols]
    pooled = pool.assign(coin="*", n=pool.n_pool, payback=pool.payback_pool, se=pool.se_pool, n_live=0.0)[cols]
    return pd.concat([out, pooled], ignore_index=True)


def expected_payback(table: pd.DataFrame, base: str, kind: str, m: float, event: bool, with_se: bool = False):
    """Payback-at-mid for the nearest calibrated m (grid 0.5); coin table first, pooled table as fallback.
    with_se=True returns (payback, se); se is 0 when the table has no se column."""
    if table.empty:
        return (None, None) if with_se else None
    coin = COIN_OF.get(base, "*")
    for c in ((coin, "*") if coin != "*" else ("*",)):
        s = table[(table.coin == c) & (table.kind == kind) & (table.event == bool(event))]
        if s.empty:
            s = table[(table.coin == c) & (table.kind == kind)]
        if s.empty:
            continue
        r = s.iloc[(s.m - m).abs().argsort().iloc[0]]
        if abs(r.m - m) <= 0.75:
            se = float(r.se) if "se" in r.index and np.isfinite(r.se) else 0.0
            return (float(r.payback), se) if with_se else float(r.payback)
    return (None, None) if with_se else None


def leg_edge(row, side: str, payback: float) -> float:
    """Edge per contract unit in USD (prices from live_chain are USD per unit of underlying)."""
    mid = float(row.mid)
    exp_pay = payback * mid
    if side == "buy":
        px = float(row.ask)
        return exp_pay - px - float(COST_MODEL.fee(px / row.spot)) * row.spot
    px = float(row.bid)
    return px - float(COST_MODEL.fee(px / row.spot)) * row.spot - exp_pay


def apply(plan: list[dict], table: pd.DataFrame, event: bool, z: float | None = None) -> tuple[list[dict], list[dict]]:
    """Split planned orders into (kept, blocked) by package edge. Each kept/blocked order gets `edge_usd`.

    Edge is scaled to the order size: units = usd / price, edge_usd = units × leg edge. Legs without a calibrated
    payback make the package unknown -> blocked (conservative). Buys are judged at payback − z·se, sells at payback + z·se.
    """
    z = GATE_Z if z is None else z
    kept, blocked = [], []
    for base in dict.fromkeys(o["base"] for o in plan):
        legs = [o for o in plan if o["base"] == base]
        total, known = 0.0, True
        for o in legs:
            r = o["row"]
            pb, se = expected_payback(table, base, r.kind, float(r.m), event, with_se=True)
            if pb is not None:
                pb = max(pb - z * se, 0.0) if o["side"] == "buy" else pb + z * se
            px = float(r.ask if o["side"] == "buy" else r.bid)
            if pb is None or not np.isfinite(px) or px <= 0:
                known = False
                o["edge_usd"] = np.nan
                continue
            o["edge_usd"] = o["usd"] / px * leg_edge(r, o["side"], pb)
            total += o["edge_usd"]
        for o in legs:
            o["package_edge_usd"] = total if known else np.nan
        (kept if known and total > 0 else blocked).extend(legs)
    return kept, blocked
