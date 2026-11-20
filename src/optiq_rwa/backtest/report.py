"""Sweep summary tables (seed-averaged) + SUMMARY.md from the per-seed results CSVs.

DSR trials: configs of the *same idea* inside one (scenario, cost model, seed) search, so that the
expected-max-Sharpe benchmark SR0 reflects the parameter search actually run for that idea, not the
spread between unrelated ideas (mixing idea 1 and idea 3 inflates V[SR] and drives DSR to 0 for all).
"""
from __future__ import annotations

import pathlib

import pandas as pd

from .metrics import HIGHLIGHT, add_dsr, highlight

COLS = ["ann_return", "excess_vs_rwa", "ann_vol", "sharpe", "ir_vs_rwa", "sharpe_vs_rwa", "max_drawdown", "cvar5_night", "dsr"]
KEYS = ["scenario", "cost_model", "idea", "params"]
SHOW = ["idea", "params", "ann_return", "excess_vs_rwa", "sharpe", "ir_vs_rwa", "max_drawdown", "dsr", "seed_min_ret", "n_nights"]
DSR_GROUP = ("scenario", "cost_model", "seed", "idea")


def summarise(res: pd.DataFrame, calib: pd.DataFrame, perp: pd.DataFrame, out: pathlib.Path) -> pd.DataFrame:
    res = add_dsr(res.drop(columns=[c for c in ("dsr", "highlight") if c in res.columns]), group_cols=DSR_GROUP)
    res["highlight"] = res.apply(highlight, axis=1)
    res.to_csv(out / "sweep_results.csv", index=False)
    avg = res.groupby(KEYS)[COLS + ["payback_ask"]].mean().reset_index()
    avg["seed_min_ret"] = res.groupby(KEYS).ann_return.min().values
    avg["n_nights"] = res.groupby(KEYS).n_nights.min().values
    avg["dsr_min_seed"] = res.groupby(KEYS).dsr.min().values
    avg["highlight"] = avg.apply(highlight, axis=1)
    avg.to_csv(out / "sweep_summary.csv", index=False)

    def _fmt(df):
        d = df[SHOW].round(4).copy()
        d["idea"] = [f"**{v}**" if h else v for v, h in zip(d.idea, df.highlight)]
        return d.to_markdown(index=False)

    lines = ["# Sweep summary (seed-averaged, out-of-sample nights)\n",
             "Cost models: none / base (Deribit fee 0.03% notional, cap 12.5% of price; daily settlement exempt) / stress (2x spread, +50% slippage, settlement fee on). "
             "SR = Sharpe vs 0, IR = vs RWA 4.5%, DSR = deflated Sharpe on the excess over RWA; trials N = parameter configs of the same idea in one scenario x cost model x seed search. "
             f"**bold** = highlight rule SR > {HIGHLIGHT['sharpe']}, IR > {HIGHLIGHT['ir_vs_rwa']}, MDD >= {HIGHLIGHT['max_drawdown']:.0%}, DSR >= {HIGHLIGHT['dsr']}, nights >= {HIGHLIGHT['min_nights']} (seed-averaged metrics).\n"]
    n_hl = int(avg.highlight.sum())
    lines.append(f"Highlighted configs: {n_hl} of {len(avg[avg.idea != '0_rwa_only'])} (scenario x cost model x config).\n")
    if n_hl:
        lines.append(avg[avg.highlight][["scenario", "cost_model"] + SHOW].round(4).to_markdown(index=False))
    for cmn in ("none", "base", "stress"):
        for sc, g in avg[avg.cost_model == cmn].groupby("scenario", sort=False):
            lines.append(f"\n## Scenario: {sc} - cost model: {cmn}\n")
            best = (g.sort_values("ir_vs_rwa", ascending=False).groupby("idea").head(1).sort_values("idea"))
            lines.append(_fmt(best))
            lines.append("")
    q = avg[(avg.idea == "2_qubo_event_selector") & (avg.cost_model == "base")]
    lines.append("\n## Idea 2 - QUBO solver comparison (base costs)\n")
    lines.append(q[["scenario", "params", "ann_return", "excess_vs_rwa", "sharpe", "ir_vs_rwa", "dsr", "payback_ask"]].round(4).to_markdown(index=False))
    if perp is not None and not perp.empty:
        pv = perp.groupby(["scenario", "nights", "instrument"], sort=False)[["mean_ret", "p_profit", "p_lose_all", "liquidation_rate", "cvar5"]].mean().reset_index()
        lines.append("\n## Idea 5 - perp vs daily call ($1 at risk per trade, base scenario)\n")
        lines.append(pv[pv.scenario == "base"].round(3).to_markdown(index=False))
    if calib is not None and not calib.empty:
        cal = calib.groupby(["scenario", "kind", "m", "event"])[["p_itm_model", "p_itm_emp", "p_be_model", "p_be_emp", "payback_mid", "payback_ask"]].mean().reset_index()
        lines.append("\n## Idea 4 - calibration, calls (base scenario)\n")
        lines.append(cal[(cal.scenario == "base") & (cal.kind == "call")].round(3).to_markdown(index=False))
    (out / "SUMMARY.md").write_text("\n".join(lines))
    return avg
