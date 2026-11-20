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
from optiq_rwa.backtest.metrics import nav_metrics, add_dsr, highlight, HIGHLIGHT   # noqa: E402
from optiq_rwa.backtest.costs import MODELS, with_costs, cost_summary  # noqa: E402
from optiq_rwa.backtest.periods import period_table, nights_to_dates  # noqa: E402
from optiq_rwa.risk.calibration import calibration_table    # noqa: E402
from optiq_rwa.strategies import core                        # noqa: E402
from optiq_rwa.data.events import event_dates                # noqa: E402

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
    ev = event_dates(("FOMC", "CPI"))
    raw["event"] = pd.to_datetime(raw.date).dt.date.isin(ev)
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
           "Indicative only. Event nights = entry on a FOMC decision day or US CPI day (data/events.csv; the print is already out at the 19:20 UTC entry, so the night carries the post-event move).\n"]
nav_all = []
for f in sorted(pathlib.Path(a.raw).glob("*_chain.parquet")):
    raw = pd.read_parquet(f)
    coin = raw.coin.iloc[0]
    ch = regularise(raw, a.tol)
    if ch.empty:
        continue
    nights = sorted(ch.night.unique())
    cover = ch.groupby("m").night.nunique().reindex(M_GRID).fillna(0).astype(int)
    n_ev = int(ch.groupby("night").event.first().sum())
    summary.append(f"\n## {coin}: {len(nights)} nights ({raw.date.min()} .. {raw.date.max()}), {len(raw)} traded strikes, {n_ev} event nights\n")
    summary.append("Nights with a strike within tol of each m bucket:\n\n" + cover.to_frame("nights").T.to_markdown())
    # idea 4 calibration on all nights
    cal = calibration_table(ch)
    cal.to_csv(out / f"calibration_{coin}.csv", index=False)
    evc = cal[(cal.kind == "call") & (cal.m == 1.0)]
    if len(evc):
        summary.append("\nEvent vs non-event nights, calls m=1 (payback_ask):\n\n" + evc[["event", "n", "p_itm_model", "p_itm_emp", "payback_mid", "payback_ask"]].round(3).to_markdown(index=False))
    summary.append("\n### Idea 4 - calibration (calls)\n")
    summary.append(cal[cal.kind == "call"][["m", "n", "p_itm_model", "p_itm_emp", "p_be_model", "p_be_emp", "payback_mid", "payback_ask"]].round(3).to_markdown(index=False))
    # strategies need a dense (night x coin) grid for the chosen m -> drop nights missing that bucket
    rows = []
    test_start = nights[min(a.warmup, len(nights) - 1)]
    dates = ch.groupby("night").date.first()
    for cm_name, cm in MODELS.items():
        chc = with_costs(ch, cm)
        use_c = cm_name != "none"
        cs = cost_summary(chc)
        for m in (0.5, 1.0, 1.5):
            sub = chc[(chc.kind == "call") & (chc.m == m)]
            if sub.night.nunique() < 20:
                continue
            chain_m = chc[chc.night.isin(sub.night)]
            for mode, bm in (("daily", 1.0), ("daily", 3.0), ("event_only", 3.0), ("bank_event", 1.0)):
                nav, info = core.yield_funded_calls(chain_m, test_start, m=m, mode=mode, budget_mult=bm, coins=[coin], costs=use_c)
                if nav.dropna().empty:
                    continue
                rows.append(dict(coin=coin, cost_model=cm_name, idea="1_yield_funded_calls", params=f"m={m} {mode} bm={bm}", nights=len(nav.dropna()),
                                 fee_per_premium=cs["fee_per_premium"], **nav_metrics(nav), **info))
                nav_all.append(nights_to_dates(nav.dropna(), dates).rename(f"{coin}|{cm_name}|calls m={m} {mode} bm={bm}"))
        for m, wing in ((1.5, 2.5), (1.5, None), (2.0, None)):
            need = [("call", m), ("put", -m)] + ([("call", wing), ("put", -wing)] if wing else [])
            ok = None
            for kd, mm in need:
                st = set(chc[(chc.kind == kd) & (chc.m == mm)].night)
                ok = st if ok is None else ok & st
            if len(ok) < 20:
                continue
            chain_m = chc[chc.night.isin(ok)]
            for frac, skip in ((0.25, False), (0.5, False), (0.5, True)):
                nav, info = core.short_premium(chain_m, test_start, m=m, frac=frac, skip_events=skip, wing_m=wing, costs=use_c)
                if nav.dropna().empty:
                    continue
                rows.append(dict(coin=coin, cost_model=cm_name, idea="3_short_premium", params=f"m={m} wing={wing} frac={frac} skip_ev={skip}", nights=len(nav.dropna()),
                                 fee_per_premium=cs["fee_per_premium"], **nav_metrics(nav), **info))
                nav_all.append(nights_to_dates(nav.dropna(), dates).rename(f"{coin}|{cm_name}|short m={m} wing={wing} frac={frac} skip_ev={skip}"))
    res = pd.DataFrame(rows)
    if not res.empty:
        res = add_dsr(res, group_cols=("coin", "cost_model"))
        res["highlight"] = res.apply(highlight, axis=1)
        res.to_csv(out / f"strategies_{coin}.csv", index=False)
        for cmn in ("none", "base", "stress"):
            g = res[res.cost_model == cmn]
            if g.empty:
                continue
            summary.append(f"\n### Ideas 1 / 3 on real quotes, cost model = {cmn} (fee per $ premium {g.fee_per_premium.iloc[0]:.3f}); **bold** = SR>0, IR>0.5, MDD>=-15%, DSR>=0.95\n")
            d = g[["idea", "params", "nights", "ann_return", "excess_vs_rwa", "sharpe", "ir_vs_rwa", "max_drawdown", "worst_night", "dsr", "payback_ask"]].round(4).copy()
            d["idea"] = [f"**{v}**" if h else v for v, h in zip(d.idea, g.highlight)]
            summary.append(d.to_markdown(index=False))
if nav_all:
    navs = pd.concat(nav_all, axis=1).sort_index()
    navs.to_csv(out / "nav_series.csv")
    base_cols = [c for c in navs.columns if "|base|" in c]
    best = navs[base_cols].iloc[-1].idxmax() if base_cols else navs.iloc[-1].idxmax()
    summary.append(f"\n## Period returns, best strategy by final NAV under base costs: {best}\n")
    for f, lab in (("M", "Monthly"), ("W", "Weekly (last 12)")):
        pt = period_table(navs[best], f)[["period", "n_days", "ret", "excess", "max_dd", "worst_day"]].round(4)
        summary.append(f"\n### {lab}\n")
        summary.append((pt.tail(12) if f == "W" else pt).to_markdown(index=False))
    # equity-curve comparison none vs base vs stress for that strategy
    tag = best.split("|", 2)[2]; coin0 = best.split("|")[0]
    comp = {cmn: navs.get(f"{coin0}|{cmn}|{tag}") for cmn in ("none", "base", "stress")}
    summary.append("\n### Final NAV by cost model (same strategy)\n")
    summary.append(pd.DataFrame({k: [v.dropna().iloc[-1]] for k, v in comp.items() if v is not None}).round(5).to_markdown(index=False))
(out / "SUMMARY_REAL.md").write_text("\n".join(summary))
print("\n".join(summary))
