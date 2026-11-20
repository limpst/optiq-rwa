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
from optiq_rwa.backtest.report import summarise  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--quick", action="store_true")
ap.add_argument("--nights", type=int, default=900)
ap.add_argument("--warmup", type=int, default=200)
a = ap.parse_args()

out = pathlib.Path("results"); out.mkdir(exist_ok=True)
seeds = (0,) if a.quick else (0, 1, 2)
res, calib, perp, curves = run(seeds=seeds, n_nights=a.nights, warmup=a.warmup, quick=a.quick)
res.to_csv(out / "sweep_results.csv", index=False)
calib.to_csv(out / "calibration.csv", index=False)
perp.to_csv(out / "perp_vs_option.csv", index=False)
avg = summarise(res, calib, perp, out)
# seed-averaged equity curves of the best config (by IR) per (scenario, cost_model, idea) -> results/sweep_curves.csv
best_rows = avg.sort_values("ir_vs_rwa", ascending=False).groupby(["scenario", "cost_model", "idea"]).head(1)
curve_cols = {}
for _, b in best_rows.iterrows():
    sers = [curves[(b.scenario, s, b.idea, b.params, b.cost_model)] for s in seeds if (b.scenario, s, b.idea, b.params, b.cost_model) in curves]
    if sers:
        m = pd.concat([x.reset_index(drop=True) for x in sers], axis=1).mean(axis=1)
        curve_cols[f"{b.scenario}|{b.cost_model}|{b.idea}|{b.params}"] = m
pd.DataFrame(curve_cols).to_csv(out / "sweep_curves.csv", index_label="night")
print((out / "SUMMARY.md").read_text())