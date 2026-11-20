"""Rebuild results/sweep_summary.csv and results/SUMMARY.md from the saved per-seed CSVs (no re-run).

    PYTHONPATH=src python scripts/summarise_sweep.py
"""
import pathlib, sys
import pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from optiq_rwa.backtest.report import summarise  # noqa: E402
out = pathlib.Path("results")
res = pd.read_csv(out / "sweep_results.csv"); calib = pd.read_csv(out / "calibration.csv"); perp = pd.read_csv(out / "perp_vs_option.csv")
avg = summarise(res, calib, perp, out)
print(f"highlighted {int(avg.highlight.sum())} of {len(avg)}")
print(avg[avg.highlight][["scenario", "cost_model", "idea", "params", "ann_return", "ir_vs_rwa", "max_drawdown", "dsr", "dsr_min_seed"]].round(3).to_string(index=False))
