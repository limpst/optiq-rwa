"""Apply the regime classifier to the real raw chains and the live store.

Writes results/regime_history.csv and results/regime_summary.md; prints classify_live for BTC, ETH, SOL_USDC.
Run: PYTHONPATH=src python scripts/run_regime.py
"""
from __future__ import annotations

import pathlib

import pandas as pd

from optiq_rwa.data import store
from optiq_rwa.data.livechain import available_coins, load_chain
from optiq_rwa.risk import regime

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "data" / "raw", ROOT / "results"


def month_table(h: pd.DataFrame) -> pd.DataFrame:
    h = h.assign(month=h.date.str[:7])
    t = h.groupby(["coin", "month"]).label.value_counts(normalize=True).unstack(fill_value=0).round(2)
    n = h.groupby(["coin", "month"]).size().rename("nights")
    return t.join(n)


def main():
    clf = regime.RegimeClassifier()
    parts = []
    for coin in available_coins():                       # raw history + live order-book nights
        chain = load_chain(coin)
        if chain.empty:
            continue
        try:
            h = regime.classify_history(chain, clf)
        except Exception as e:                           # e.g. a live-only coin with too few nights yet
            print(f"{coin}: regime history skipped ({e})")
            continue
        if h.empty:
            continue
        dates = chain.groupby("night").date.first()
        h["date"] = h.night.map(dates).astype(str)
        parts.append(h)
    hist = pd.concat(parts, ignore_index=True)
    OUT.mkdir(exist_ok=True)
    hist.to_csv(OUT / "regime_history.csv", index=False)
    mt = month_table(hist)

    lines = ["# Regime classification (real Deribit chains)", "",
             "Nearest-centroid on walk-forward features (IV/RV, trailing payback, P(ITM) gap, IV percentile); "
             "reference = synthetic scenarios (results/regime_reference.csv). Label share per month:", "",
             mt.reset_index().to_markdown(index=False), "", "## Latest label", ""]
    for coin, h in hist.groupby("coin"):
        last = h.iloc[-1]
        probs = {c[2:]: round(last[c], 2) for c in h.columns if c.startswith("p_")}
        lines.append(f"- {coin} {last.date}: {last.label} ({probs}); rule-based: {last.rule_label} - {last.rule_reason}")
        lines.append("")
    lines += ["## Interpretation", ""]
    for coin, h in hist.groupby("coin"):
        d = h[h.label != "unknown"]
        share = d.label.value_counts(normalize=True).round(2).to_dict()
        last = h.iloc[-1]
        lines.append(f"- {coin}: label share over {len(d)} classified nights {share}; latest {last.label}. "
                     f"Why: IV/RV {last.ivrv:.2f}, payback_mid60 {last.pb_mid60:.2f}, P(ITM) gap {last.itm_gap60:+.3f} "
                     f"(realised minus model). So what: {last.action}. Real chains are sparse (BTC ~7, SOL ~2.6 quotes/night), "
                     "so payback features are noisy; treat label as a tilt, not a signal.")
    lines += ["", "Limitation: base, fair_iv and events_underpriced are nearly indistinguishable on these features "
              "(only rich_iv separates); distinguishing them needs event-night flags and IV mark-up on events."]
    (OUT / "regime_summary.md").write_text("\n".join(lines) + "\n")
    print(mt.to_string())

    con = store.connect()
    live = regime.classify_live(con, clf=clf)
    cols = ["base", "iv_atm_live", "rv_delivery", "n_rv", "ivrv", "pb_mid60", "itm_gap60", "iv_pct120", "label", "rule_label", "action"]
    print(live[cols].round(3).to_string())


if __name__ == "__main__":
    main()
