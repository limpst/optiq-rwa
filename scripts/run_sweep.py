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

ap = argparse.ArgumentParser()
ap.add_argument("--quick", action="store_true")
ap.add_argument("--nights", type=int, default=900)
ap.add_argument("--warmup", type=int, default=200)
a = ap.parse_args()

out = pathlib.Path("results"); out.mkdir(exist_ok=True)
seeds = (0,) if a.quick else (0, 1, 2)
res, calib, perp = run(seeds=seeds, n_nights=a.nights, warmup=a.warmup, quick=a.quick)
res.to_csv(out / "sweep_results.csv", index=False)
calib.to_csv(out / "calibration.csv", index=False)
perp.to_csv(out / "perp_vs_option.csv", index=False)

# --- seed-averaged summary
cols = ["ann_return", "excess_vs_rwa", "ann_vol", "sharpe_vs_rwa", "max_drawdown", "cvar5_night"]
avg = res.groupby(["scenario", "idea", "params"])[cols + ["payback_ask"]].mean().reset_index()
avg["seed_min_ret"] = res.groupby(["scenario", "idea", "params"]).ann_return.min().values
avg.to_csv(out / "sweep_summary.csv", index=False)

lines = ["# Sweep summary (seed-averaged, out-of-sample nights)\n"]
for sc, g in avg.groupby("scenario", sort=False):
    lines.append(f"\n## Scenario: {sc}\n")
    best = (g.sort_values("sharpe_vs_rwa", ascending=False).groupby("idea").head(1).sort_values("idea"))
    lines.append(best[["idea", "params"] + cols + ["seed_min_ret"]].round(4).to_markdown(index=False))
    lines.append("")
q = avg[avg.idea == "2_qubo_event_selector"]
lines.append("\n## Idea 2 - QUBO solver comparison (SA vs greedy)\n")
lines.append(q[["scenario", "params", "ann_return", "excess_vs_rwa", "sharpe_vs_rwa", "payback_ask"]].round(4).to_markdown(index=False))
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
