"""Idea 8 — execution-economics gate: trade a package only when expected edge − transaction cost > 0.

Expected settlement value of an option = calibrated payback-at-mid × live mid, where the payback ratio comes from
idea 4 (results/real/calibration_{COIN}.csv: realised payoff / mid per coin × kind × m × event bucket), shrunk toward
the pooled (kind × m × event) estimate with weight n / (n + prior_n). Costs are what the paper engine actually pays:
the spread (fill at ask / bid) plus the Deribit trading fee (CostModel.fee). Settlement fee is 0 for daily options.

    buy leg  edge = E[payoff] − ask − fee(ask)
    sell leg edge = bid − fee(bid) − E[payoff]

A strategy's orders for one base form a package (a condor's wings are protection, not a separate bet), so the gate
passes or blocks the whole package on the sum of leg edges (USD).
"""
from __future__ import annotations

import pathlib

import numpy as np
import pandas as pd

from ..backtest.costs import BASE as COST_MODEL
from ..config import ROOT

CAL_DIR = ROOT / "results" / "real"
PRIOR_N = 60.0
COIN_OF = {"BTC": "BTC", "BTC_USDC": "BTC", "SOL_USDC": "SOL", "SOL": "SOL"}   # other bases use the pooled table


def load_payback(cal_dir: pathlib.Path = CAL_DIR, prior_n: float = PRIOR_N) -> pd.DataFrame:
    """Shrunk payback-at-mid per (coin, kind, m, event); coin='*' rows are the pooled estimate."""
    files = sorted(pathlib.Path(cal_dir).glob("calibration_*.csv"))
    if not files:
        return pd.DataFrame(columns=["coin", "kind", "m", "event", "n", "payback"])
    t = pd.concat(pd.read_csv(f) for f in files)
    t = t[np.isfinite(t.payback_mid) & (t.n > 0)].copy()
    t["w_pay"] = t.payback_mid * t.n
    pool = t.groupby(["kind", "m", "event"], as_index=False).agg(n=("n", "sum"), w_pay=("w_pay", "sum"))
    pool["payback_pool"] = pool.w_pay / pool.n
    t = t.merge(pool[["kind", "m", "event", "payback_pool"]], on=["kind", "m", "event"])
    w = t.n / (t.n + prior_n)
    t["payback"] = w * t.payback_mid + (1 - w) * t.payback_pool
    pooled = pool.assign(coin="*", payback=pool.payback_pool)[["coin", "kind", "m", "event", "n", "payback"]]
    return pd.concat([t[["coin", "kind", "m", "event", "n", "payback"]], pooled], ignore_index=True)


def expected_payback(table: pd.DataFrame, base: str, kind: str, m: float, event: bool) -> float | None:
    """Payback-at-mid for the nearest calibrated m (grid 0.5); coin table first, pooled table as fallback."""
    if table.empty:
        return None
    coin = COIN_OF.get(base, "*")
    for c in ((coin, "*") if coin != "*" else ("*",)):
        s = table[(table.coin == c) & (table.kind == kind) & (table.event == bool(event))]
        if s.empty:
            s = table[(table.coin == c) & (table.kind == kind)]
        if s.empty:
            continue
        r = s.iloc[(s.m - m).abs().argsort().iloc[0]]
        if abs(r.m - m) <= 0.75:
            return float(r.payback)
    return None


def leg_edge(row, side: str, payback: float) -> float:
    """Edge per contract unit in USD (prices from live_chain are USD per unit of underlying)."""
    mid = float(row.mid)
    exp_pay = payback * mid
    if side == "buy":
        px = float(row.ask)
        return exp_pay - px - float(COST_MODEL.fee(px / row.spot)) * row.spot
    px = float(row.bid)
    return px - float(COST_MODEL.fee(px / row.spot)) * row.spot - exp_pay


def apply(plan: list[dict], table: pd.DataFrame, event: bool) -> tuple[list[dict], list[dict]]:
    """Split planned orders into (kept, blocked) by package edge. Each kept/blocked order gets `edge_usd`.

    Edge is scaled to the order size: units = usd / price, edge_usd = units × leg edge. Legs without a calibrated
    payback make the package unknown -> blocked (conservative).
    """
    kept, blocked = [], []
    for base in dict.fromkeys(o["base"] for o in plan):
        legs = [o for o in plan if o["base"] == base]
        total, known = 0.0, True
        for o in legs:
            r = o["row"]
            pb = expected_payback(table, base, r.kind, float(r.m), event)
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
