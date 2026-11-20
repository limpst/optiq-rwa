"""Backtest ideas 1 / 3 / 4 on the REAL Deribit trade-history chains in data/raw/*_chain.parquet.

Quotes are trade VWAPs around 19:20 UTC with a modelled spread (quote_source=trade_vwap),
so results are indicative, not executable. Output: results/real/*.csv, results/real/SUMMARY_REAL.md

    PYTHONPATH=src python scripts/run_real_backtest.py [--raw data/raw] [--warmup 40]
"""
import argparse
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from optiq_rwa.backtest.metrics import nav_metrics          # noqa: E402
from optiq_rwa.backtest.periods import period_table, nights_to_dates  # noqa: E402
from optiq_rwa.risk.calibration import calibration_table    # noqa: E402
from optiq_rwa.strategies import core                        # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--raw", default="data/raw")
ap.add_argument("--warmup", type=int, default=40)
ap.add_argument("--tol", type=float, default=0.35)
a = ap.parse_args()
out = pathlib.Path("results/real"); out.mkdir(parents=True, exist_ok=True)

M_GRID = (-2.5, -2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5)


def regularise(raw: pd.DataFrame, tol: float) -> pd.DataFrame:
    """One row per (night, coin, kind, m in M_GRID): nearest traded strike within tol, else NaN row."""
    raw = raw[np.isfinite(raw.m) & (raw.iv > 0)].copy()
    raw["m_cont"] = np.log(raw.k_rel) / (raw.iv_atm * np.sqrt(12.7 / 8760))
    rows = []
    for (n, c, kd), g in raw.groupby(["night", "coin", "kind"]):
        for m in M_GRID:
            if (kd == "call" and m < 0) or (kd == "put" and m > 0):
                continue
            d = (g.m_cont - m).abs()
            if d.min() <= tol:
                r = g.loc[d.idxmin()].copy(); r["m"] = m; r["m_dist"] = d.min(); rows.append(r)
    return pd.DataFrame(rows).reset_index(drop=True)


summary = ["# Real-data backtest (Deribit trade VWAP chains)\n",
           "Quotes = VWAP of trades within +/-20 min of 19:20 UTC, bid/ask rebuilt with the synthetic spread model (10% + 2bp). "
           "Indicative only. Event flag is all-False (no event calendar yet), so event-conditional modes are not run.\n"]
nav_all = []
for f in sorted(pathlib.Path(a.raw).glob("*_chain.parquet")):
    raw = pd.read_parquet(f)
    coin = raw.coin.iloc[0]
    ch = regularise(raw, a.tol)
    if ch.empty:
        continue
    nights = sorted(ch.night.unique())
    cover = ch.groupby("m").night.nunique().reindex(M_GRID).fillna(0).astype(int)
    summary.append(f"\n## {coin}: {len(nights)} nights ({raw.date.min()} .. {raw.date.max()}), {len(raw)} traded strikes\n")
    summary.append("Nights with a strike within tol of each m bucket:\n\n" + cover.to_frame("nights").T.to_markdown())
    # idea 4 calibration on all nights
    cal = calibration_table(ch)
    cal.to_csv(out / f"calibration_{coin}.csv", index=False)
    summary.append("\n### Idea 4 - calibration (calls)\n")
    summary.append(cal[cal.kind == "call"][["m", "n", "p_itm_model", "p_itm_emp", "p_be_model", "p_be_emp", "payback_mid", "payback_ask"]].round(3).to_markdown(index=False))
    # strategies need a dense (night x coin) grid for the chosen m -> drop nights missing that bucket
    rows = []
    test_start = nights[min(a.warmup, len(nights) - 1)]
    dates = ch.groupby("night").date.first()
    for m in (0.5, 1.0, 1.5):
        sub = ch[(ch.kind == "call") & (ch.m == m)]
        if sub.night.nunique() < 20:
            continue
        chain_m = ch[ch.night.isin(sub.night)]
        for bm in (1.0, 3.0):
            nav, info = core.yield_funded_calls(chain_m, test_start, m=m, mode="daily", budget_mult=bm, coins=[coin])
            if nav.dropna().empty:
                continue
            rows.append(dict(coin=coin, idea="1_yield_funded_calls", params=f"m={m} daily bm={bm}", nights=len(nav.dropna()), **nav_metrics(nav), **info))
            nav_all.append(nights_to_dates(nav.dropna(), dates).rename(f"{coin} calls m={m} bm={bm}"))
    for m, wing in ((1.5, 2.5), (1.5, None), (2.0, None)):
        need = [("call", m), ("put", -m)] + ([("call", wing), ("put", -wing)] if wing else [])
        ok = None
        for kd, mm in need:
            s = set(ch[(ch.kind == kd) & (ch.m == mm)].night)
            ok = s if ok is None else ok & s
        if len(ok) < 20:
            continue
        chain_m = ch[ch.night.isin(ok)]
        for frac in (0.25, 0.5):
            nav, info = core.short_premium(chain_m, test_start, m=m, frac=frac, skip_events=False, wing_m=wing)
            if nav.dropna().empty:
                continue
            rows.append(dict(coin=coin, idea="3_short_premium", params=f"m={m} wing={wing} frac={frac}", nights=len(nav.dropna()), **nav_metrics(nav), **info))
            nav_all.append(nights_to_dates(nav.dropna(), dates).rename(f"{coin} short m={m} wing={wing} frac={frac}"))
    res = pd.DataFrame(rows)
    if not res.empty:
        res.to_csv(out / f"strategies_{coin}.csv", index=False)
        summary.append("\n### Ideas 1 / 3 on real quotes (out-of-sample after warmup)\n")
        summary.append(res[["idea", "params", "nights", "ann_return", "excess_vs_rwa", "sharpe_vs_rwa", "max_drawdown", "worst_night", "payback_ask"]].round(4).to_markdown(index=False))
if nav_all:
    navs = pd.concat(nav_all, axis=1).sort_index()
    navs.to_csv(out / "nav_series.csv")
    best = navs.iloc[-1].idxmax()
    summary.append(f"\n## Monthly returns, best strategy by final NAV: {best}\n")
    summary.append(period_table(navs[best], "M")[["period", "n_days", "ret", "excess", "max_dd", "worst_day"]].round(4).to_markdown(index=False))
(out / "SUMMARY_REAL.md").write_text("\n".join(summary))
print("\n".join(summary))
