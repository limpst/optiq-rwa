"""Maker-fill backfill: would resting limit orders at mid have filled on past nights (from stored order books)?

For each UTC date with snapshots: take the snapshot closest to 19:20 UTC, plan the yield_calls legs (m~+1 call per
tradable base) and the short_condor legs, rest each at mid, then scan later snapshots before expiry for a crossing
(ask <= mid for buys, bid >= mid for sells). Reports fill rate, time-to-fill, and for filled buys the payoff at
delivery vs premium (payback at mid, maker fee 0 for USDC daily / 3 bps inverse).

    PYTHONPATH=src python scripts/run_maker_backfill.py
"""
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from optiq_rwa.data import store                                   # noqa: E402
from optiq_rwa.data.live import live_chain, index_name_of          # noqa: E402
from optiq_rwa.paper import engine                                 # noqa: E402

con = store.connect()
snaps = store.read(con, "SELECT snap_id, ts_ms, date FROM snapshots ORDER BY ts_ms")
rows = []
for date, g in snaps.groupby("date"):
    target = pd.Timestamp(date + " 19:20", tz="UTC").timestamp() * 1000
    g = g.assign(d=(g.ts_ms - target).abs())
    s0 = g.sort_values("d").iloc[0]
    if s0.d > 45 * 60_000:
        continue
    snap_id, ts = int(s0.snap_id), int(s0.ts_ms)
    bases = engine.tradable_bases(con, date)
    chains = {}
    for b in bases:
        for rank in (0, 1):
            ch = live_chain(con, snap_id, b, rank)
            if not ch.empty and 6 <= ch.hours.iloc[0] <= 26:
                chains[b] = ch
                break
    for name in ("yield_calls", "short_condor"):
        plan = engine.plan_orders(con, name, engine.STRATEGIES[name], chains, 1_000_000.0, date)
        for base in dict.fromkeys(o["base"] for o in plan):
            legs = [o for o in plan if o["base"] == base]
            leg_rows = []
            for o in legs:
                r = o["row"]
                hist = store.read(con, """SELECT s.ts_ms, b.bid_px, b.ask_px, st.underlying_price FROM order_book b JOIN snapshots s USING (snap_id)
                                          LEFT JOIN inst_state st ON st.instrument_name=b.instrument_name AND st.snap_id=b.snap_id
                                          WHERE b.instrument_name=? AND b.level=0 AND s.ts_ms>? AND s.ts_ms<=? ORDER BY s.ts_ms""",
                                  (r.instrument_name, ts, int(r.expiration_ts)))
                inv = r.instrument_name.split("-")[0] in ("BTC", "ETH")
                conv = hist.underlying_price.fillna(r.spot).values if (inv and not hist.empty) else np.ones(len(hist))
                px = (hist.ask_px.values if o["side"] == "buy" else hist.bid_px.values) * conv if not hist.empty else np.array([])
                ok = ((px <= r.mid) if o["side"] == "buy" else (px >= r.mid)) & np.isfinite(px) if len(px) else np.array([], bool)
                t_fill = (int(hist.ts_ms.iloc[int(np.argmax(ok))]) - ts) / 3.6e6 if ok.any() else np.nan
                d = store.utc_date(int(r.expiration_ts))
                dp = con.execute("SELECT price FROM delivery_price WHERE index_name=? AND date=?", (index_name_of(base), d)).fetchone()
                payoff = (max(dp[0] - r.strike, 0) if r.kind == "call" else max(r.strike - dp[0], 0)) if dp else np.nan
                leg_rows.append(dict(date=date, strategy=name, base=base, instrument=r.instrument_name, side=o["side"], m=round(float(r.m), 2),
                                     mid=float(r.mid), ask=float(r.ask), bid=float(r.bid), n_snaps=len(hist), crossed=bool(ok.any()),
                                     hours_to_fill=t_fill, payoff=payoff, payback_mid=(payoff / r.mid) if (dp and r.mid > 0) else np.nan))
            pkg = all(l["crossed"] for l in leg_rows) if leg_rows else False
            for l in leg_rows:
                l["package_filled"] = pkg
            rows += leg_rows
df = pd.DataFrame(rows)
out = pathlib.Path("results"); out.mkdir(exist_ok=True)
df.to_csv(out / "maker_backfill.csv", index=False)
lines = ["# Maker-fill backfill (resting at mid, live order books)\n"]
if df.empty:
    lines.append("no nights with a 19:20 UTC snapshot and a 6-26h expiry yet")
else:
    summ = df.groupby(["strategy", "side"]).agg(legs=("crossed", "size"), leg_fill=("crossed", "mean"), pkg_fill=("package_filled", "mean"),
                                                 hours_to_fill=("hours_to_fill", "median"), payback_mid_filled=("payback_mid", lambda x: x[df.loc[x.index, "crossed"]].mean())).reset_index()
    lines.append(summ.round(3).to_markdown(index=False))
    byb = df[df.strategy == "yield_calls"].groupby("base").agg(nights=("crossed", "size"), fill=("crossed", "mean"), h=("hours_to_fill", "median")).reset_index()
    lines.append("\n## yield_calls (m~1 call buy at mid) by base\n")
    lines.append(byb.round(2).to_markdown(index=False))
    lines.append("\n## nights\n")
    lines.append(df[["date", "strategy", "base", "side", "m", "mid", "ask", "crossed", "hours_to_fill", "package_filled", "payback_mid"]].round(3).to_markdown(index=False))
(out / "maker_backfill.md").write_text("\n".join(lines)); print("\n".join(lines[:12]))
