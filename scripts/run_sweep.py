"""Run the full strategy sweep and write results/ (CSV + markdown summary).

    PYTHONPATH=src python scripts/run_sweep.py            # full (~2-3 min)
    PYTHONPATH=src python scripts/run_sweep.py --quick    # 1 seed, greedy only
"""
import argparse
import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from optiq_rwa.backtest.sweep import run  # noqa: E402
from optiq_rwa.backtest.metrics import add_dsr, highlight, HIGHLIGHT  # noqa: E402
import numpy as np  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--quick", action="store_true")
ap.add_argument("--nights", type=int, default=900)
ap.add_argument("--warmup", type=int, default=200)
a = ap.parse_args()

out = pathlib.Path("results"); out.mkdir(exist_ok=True)
seeds = (0,) if a.quick else (0, 1, 2)
res, calib, perp, curves = run(seeds=seeds, n_nights=a.nights, warmup=a.warmup, quick=a.quick)
# DSR: every (scenario, cost_model) search is one family of trials; per seed first, then averaged
res = add_dsr(res, group_cols=("scenario", "cost_model", "seed"))
res["highlight"] = res.apply(highlight, axis=1)
res.to_csv(out / "sweep_results.csv", index=False)
calib.to_csv(out / "calibration.csv", index=False)
perp.to_csv(out / "perp_vs_option.csv", index=False)

# --- seed-averaged summary
cols = ["ann_return", "excess_vs_rwa", "ann_vol", "sharpe", "ir_vs_rwa", "sharpe_vs_rwa", "max_drawdown", "cvar5_night", "dsr"]
keys = ["scenario", "cost_model", "idea", "params"]
avg = res.groupby(keys)[cols + ["payback_ask"]].mean().reset_index()
avg["seed_min_ret"] = res.groupby(keys).ann_return.min().values
avg["n_nights"] = res.groupby(keys).n_nights.min().values
avg["highlight"] = avg.apply(highlight, axis=1)
avg.to_csv(out / "sweep_summary.csv", index=False)
# seed-averaged equity curves of the best config (by IR) per (scenario, cost_model, idea) -> results/sweep_curves.csv
best_rows = avg.sort_values("ir_vs_rwa", ascending=False).groupby(["scenario", "cost_model", "idea"]).head(1)
curve_cols = {}
for _, b in best_rows.iterrows():
    sers = [curves[(b.scenario, s, b.idea, b.params, b.cost_model)] for s in seeds if (b.scenario, s, b.idea, b.params, b.cost_model) in curves]
    if sers:
        m = pd.concat([x.reset_index(drop=True) for x in sers], axis=1).mean(axis=1)
        curve_cols[f"{b.scenario}|{b.cost_model}|{b.idea}|{b.params}"] = m
pd.DataFrame(curve_cols).to_csv(out / "sweep_curves.csv", index_label="night")

lines = ["# Sweep summary (seed-averaged, out-of-sample nights)\n",
         f"Cost models: none / base (Deribit fee 0.03% notional, cap 12.5% of price; daily settlement exempt) / stress (2x spread, +50% slippage, settlement fee on). "
         f"SR = Sharpe vs 0, IR = vs RWA 4.5%, DSR = deflated Sharpe (N = configs per scenario x cost model). "
         f"**bold** = highlight rule SR > {HIGHLIGHT['sharpe']}, IR > {HIGHLIGHT['ir_vs_rwa']}, MDD >= {HIGHLIGHT['max_drawdown']:.0%}, DSR >= {HIGHLIGHT['dsr']}, nights >= {HIGHLIGHT['min_nights']}. DSR is computed on the excess over RWA.\n"]
show = ["idea", "params", "ann_return", "excess_vs_rwa", "sharpe", "ir_vs_rwa", "max_drawdown", "dsr", "seed_min_ret"]
def _fmt(df):
    d = df[show].round(4).copy()
    hl = df.highlight.values
    d["idea"] = [f"**{v}**" if h else v for v, h in zip(d.idea, hl)]
    return d.to_markdown(index=False)
n_hl = int(avg.highlight.sum())
lines.append(f"Highlighted configs: {n_hl} of {len(avg)} (scenario x cost model x config).\n")
if n_hl:
    lines.append(avg[avg.highlight][["scenario", "cost_model"] + show].round(4).to_markdown(index=False))
for cmn in ("none", "base", "stress"):
    for sc, g in avg[avg.cost_model == cmn].groupby("scenario", sort=False):
        lines.append(f"\n## Scenario: {sc} · cost model: {cmn}\n")
        best = (g.sort_values("ir_vs_rwa", ascending=False).groupby("idea").head(1).sort_values("idea"))
        lines.append(_fmt(best))
        lines.append("")
q = avg[(avg.idea == "2_qubo_event_selector") & (avg.cost_model == "base")]
lines.append("\n## Idea 2 - QUBO solver comparison (base costs)\n")
lines.append(q[["scenario", "params", "ann_return", "excess_vs_rwa", "sharpe", "ir_vs_rwa", "dsr", "payback_ask"]].round(4).to_markdown(index=False))
pv = perp.groupby(["scenario", "nights", "instrument"], sort=False)[
    ["mean_ret", "p_profit", "p_lose_all", "liquidation_rate", "cvar5"]].mean().reset_index()
lines.append("\n## Idea 5 - perp vs daily call ($1 at risk per trade, base scenario)\n")
lines.append(pv[pv.scenario == "base"].round(3).to_markdown(index=False))
cal = calib.groupby(["scenario", "kind", "m", "event"])[
    ["p_itm_model", "p_itm_emp", "p_be_model", "p_be_emp", "payback_mid", "payback_ask"]].mean().reset_index()
lines.append("\n## Idea 4 - calibration, calls (base scenario)\n")
lines.append(cal[(cal.scenario == "base") & (cal.kind == "call")].round(3).to_markdown(index=False))
(out / "SUMMARY.md").write_text("\n".join(lines))
print("\n".join(lines))
