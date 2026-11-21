"""Does the regime label predict which overlay pays? Real Deribit chains, walk-forward labels.

Per (coin, night): long overlay = m~+1 call bought at ask_c (payback-1 per $ premium);
short overlay = m~+/-1.5 strangle sold at bid_c, payoff_short_c owed (P&L per $ spot notional per leg).
Labels from results/regime_history.csv (features use nights < n only). Cost model = base.
Chains = data/raw history + live order-book nights appended daily (optiq_rwa.data.livechain), so the
out-of-sample window grows by one tradable-quote night per settled day.
Outputs results/regime_validation.csv / .md: per-label statistics and four NAV paths
(rwa_only, always_long_daily, always_short, regime_follow) with SR / IR / MDD / DSR.

    PYTHONPATH=src python scripts/run_regime_validation.py
"""
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from optiq_rwa.backtest.costs import BASE, with_costs           # noqa: E402
from optiq_rwa.backtest.metrics import nav_metrics, add_dsr, highlight  # noqa: E402
from optiq_rwa.data.events import event_dates                   # noqa: E402
from optiq_rwa.data.livechain import available_coins, load_chain  # noqa: E402

RWA, TOL, FRAC, BM = 0.045, 0.35, 0.5, 3.0
out = pathlib.Path("results"); lab = pd.read_csv(out / "regime_history.csv", parse_dates=["date"])
lab["date"] = lab.date.dt.date
ev = event_dates(("FOMC", "CPI"))


def nearest(g, kind, m):
    s = g[(g.kind == kind) & g.ask.gt(0)]
    if s.empty:
        return None
    d = (s.m_cont - m).abs()
    return s.loc[d.idxmin()] if d.min() <= TOL else None


rows, navs_all, md = [], {}, ["# Regime validation (real chains, base TC)\n",
                             "Long overlay = m≈+1 call at ask (incl. fee), return per $ premium = payback − 1. Short overlay = m≈±1.5 strangle at bid (incl. fee), P&L per $ notional per leg. "
                             "Labels are walk-forward (features use earlier nights only). regime_follow: rich_iv → sell strangle (frac 0.5), else buy calls with 3× accrual on event nights only.\n"]
for coin in available_coins():           # raw history + live order-book nights (data.livechain)
    raw = load_chain(coin)
    if raw.empty:
        continue
    raw = raw[np.isfinite(raw.m) & (raw.iv > 0)].copy()
    raw["m_cont"] = np.log(raw.k_rel) / (raw.iv_atm * np.sqrt(12.7 / 8760))
    raw["m"] = (raw.m_cont * 2).round() / 2
    raw["event"] = pd.to_datetime(raw.date).dt.date.isin(ev)
    rc = with_costs(raw, BASE)
    recs = []
    for (n, d), g in rc.groupby(["night", "date"]):
        c1 = nearest(g, "call", 1.0); sc = nearest(g, "call", 1.5); sp = nearest(g, "put", -1.5)
        recs.append(dict(coin=coin, night=n, date=d, event=bool(g.event.iloc[0]),
                         long_ret=(c1.payoff_long_c / c1.ask_c - 1) if c1 is not None else np.nan,
                         short_pnl=((sc.bid_c - sc.payoff_short_c) + (sp.bid_c - sp.payoff_short_c)) if (sc is not None and sp is not None) else np.nan,
                         short_prem=(sc.bid_c + sp.bid_c) if (sc is not None and sp is not None) else np.nan))
    df = pd.DataFrame(recs).merge(lab[lab.coin == coin][["date", "label", "rule_label", "ivrv", "pb_mid60"]], on="date", how="left")
    df["label"] = df.label.fillna("unknown")
    df.to_csv(out / f"regime_validation_nights_{coin}.csv", index=False)
    # per-label statistics
    stat = df.groupby("label").agg(nights=("night", "count"), long_n=("long_ret", "count"), long_mean=("long_ret", "mean"),
                                   long_hit=("long_ret", lambda x: (x > 0).mean()), short_n=("short_pnl", "count"),
                                   short_mean=("short_pnl", "mean"), short_worst=("short_pnl", "min"),
                                   short_hit=("short_pnl", lambda x: (x > 0).mean())).reset_index()
    stat.insert(0, "coin", coin); rows.append(stat)
    md.append(f"\n## {coin}: {len(df)} nights, labels {df.label.value_counts().to_dict()}\n")
    md.append(stat.round(4).to_markdown(index=False))
    # NAV paths (walk-forward, label known at entry)
    nav = {k: [1.0] for k in ("rwa_only", "always_long_daily", "always_short", "regime_follow")}
    for _, r in df.sort_values("night").iterrows():
        for k in nav:
            v = nav[k][-1]; acc = v * RWA / 365; v += acc
            if k == "always_long_daily" and np.isfinite(r.long_ret):
                v += acc * r.long_ret
            elif k == "always_short" and np.isfinite(r.short_pnl):
                v *= 1 + FRAC / 2 * r.short_pnl
            elif k == "regime_follow":
                if r.label == "rich_iv" and np.isfinite(r.short_pnl):
                    v *= 1 + FRAC / 2 * r.short_pnl
                elif r.label != "rich_iv" and r.event and np.isfinite(r.long_ret):
                    v += acc * BM * r.long_ret
            nav[k].append(v)
    dates = pd.to_datetime(df.sort_values("night").date)
    mt = []
    for k, path in nav.items():
        s = pd.Series(path[1:], index=dates)
        navs_all[f"{coin}|{k}"] = s
        mt.append(dict(coin=coin, strategy=k, **nav_metrics(s, RWA)))
    mt = add_dsr(pd.DataFrame(mt), group_cols=("coin",)); mt["highlight"] = mt.apply(highlight, axis=1)
    mt.to_csv(out / f"regime_validation_nav_{coin}.csv", index=False)
    md.append(f"\n### {coin} NAV paths (SR · IR · MDD · DSR; bold = highlight rule)\n")
    d = mt[["strategy", "n_nights", "ann_return", "excess_vs_rwa", "sharpe", "ir_vs_rwa", "max_drawdown", "worst_night", "dsr"]].round(4).copy()
    d["strategy"] = [f"**{v}**" if h else v for v, h in zip(d.strategy, mt.highlight)]
    md.append(d.to_markdown(index=False))
    rich = df[df.label == "rich_iv"]; other = df[df.label.isin(["base", "fair_iv", "events_underpriced"])]
    md.append(f"\n- {coin}: short strangle mean P&L per $ notional was {rich.short_pnl.mean():+.4f} on rich_iv nights (n={rich.short_pnl.count()}) vs {other.short_pnl.mean():+.4f} on other labelled nights (n={other.short_pnl.count()}). "
              f"Long m=1 call return per $ was {rich.long_ret.mean():+.3f} on rich_iv vs {other.long_ret.mean():+.3f} elsewhere. "
              f"{'Label separates the sell edge.' if rich.short_pnl.mean() > other.short_pnl.mean() else 'Label does not separate the sell edge.'}")
pd.concat(rows).to_csv(out / "regime_validation.csv", index=False)
pd.DataFrame(navs_all).to_csv(out / "regime_validation_curves.csv")
(out / "regime_validation.md").write_text("\n".join(md)); print("\n".join(md))
