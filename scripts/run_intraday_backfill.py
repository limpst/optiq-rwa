"""Intraday short backfill: sell at the 19:20 UTC bid, buy back later at the ask (profit target) or hold to expiry.

Legs: m~+1.5 call and m~-1.5 put (the strangle of idea 3), per tradable base, from stored order books.
Rules compared (per leg, per $ of premium received): hold to settlement; buy back when ask <= (1 - target) x sold bid
(target 25% / 50% / 75%); costs = taker fee on both fills (12.5% cap), settlement fee 0. Also writes the median
mid-decay curve (mid_t / mid_entry by hours since entry) used by the dashboard.

    PYTHONPATH=src python scripts/run_intraday_backfill.py
"""
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from optiq_rwa.backtest.costs import BASE as CM                   # noqa: E402
from optiq_rwa.data import store                                   # noqa: E402
from optiq_rwa.data.live import live_chain, index_name_of          # noqa: E402
from optiq_rwa.paper import engine                                 # noqa: E402

TARGETS = (0.25, 0.5, 0.75)
con = store.connect()
snaps = store.read(con, "SELECT snap_id, ts_ms, date FROM snapshots ORDER BY ts_ms")
rows, curve = [], []
for date, g in snaps.groupby("date"):
    target = pd.Timestamp(date + " 19:20", tz="UTC").timestamp() * 1000
    s0 = g.assign(d=(g.ts_ms - target).abs()).sort_values("d").iloc[0]
    if s0.d > 45 * 60_000:
        continue
    snap_id, ts = int(s0.snap_id), int(s0.ts_ms)
    for b in engine.tradable_bases(con, date):
        ch = None
        for rank in (0, 1):
            c = live_chain(con, snap_id, b, rank)
            if not c.empty and 6 <= c.hours.iloc[0] <= 26:
                ch = c
                break
        if ch is None:
            continue
        inv = b in ("BTC", "ETH")
        for kind, m in (("call", 1.5), ("put", -1.5)):
            r = engine._nearest(ch, kind, m, need="bid")
            if r is None or not np.isfinite(r.bid) or r.bid <= 0:
                continue
            hist = store.read(con, """SELECT s.ts_ms, b.bid_px, b.ask_px, st.underlying_price FROM order_book b JOIN snapshots s USING (snap_id)
                                      LEFT JOIN inst_state st ON st.instrument_name=b.instrument_name AND st.snap_id=b.snap_id
                                      WHERE b.instrument_name=? AND b.level=0 AND s.ts_ms>? AND s.ts_ms<=? ORDER BY s.ts_ms""",
                              (r.instrument_name, ts, int(r.expiration_ts)))
            conv = hist.underlying_price.fillna(r.spot).values if (inv and not hist.empty) else np.ones(len(hist))
            ask = pd.to_numeric(hist.ask_px, errors="coerce").values * conv if len(hist) else np.array([])
            bid = pd.to_numeric(hist.bid_px, errors="coerce").values * conv if len(hist) else np.array([])
            mid = np.where(np.isfinite(ask) & np.isfinite(bid), (ask + bid) / 2, np.nan) if len(hist) else np.array([])
            hrs = (hist.ts_ms.values - ts) / 3.6e6 if len(hist) else np.array([])
            for hh, mm in zip(hrs, mid):
                if np.isfinite(mm) and r.mid > 0:
                    curve.append(dict(base=b, kind=kind, hours=round(float(hh) * 2) / 2, ratio=float(mm / r.mid)))
            d = store.utc_date(int(r.expiration_ts))
            dp = con.execute("SELECT price FROM delivery_price WHERE index_name=? AND date=?", (index_name_of(b), d)).fetchone()
            payoff = (max(dp[0] - r.strike, 0) if kind == "call" else max(r.strike - dp[0], 0)) if dp else np.nan
            sold = float(r.bid)
            fee_in = float(CM.fee(sold / r.spot)) * r.spot
            base_row = dict(date=date, base=b, kind=kind, m=round(float(r.m), 2), instrument=r.instrument_name, sold_bid=sold, mid_entry=float(r.mid), spot=float(r.spot), n_snaps=len(hist))
            # hold to settlement
            rows.append(dict(base_row, rule="hold", pnl_per_prem=(sold - fee_in - payoff) / sold if dp else np.nan, exit_hours=float(r.hours), closed=False))
            for tg in TARGETS:
                lim = sold * (1 - tg)
                ok = np.isfinite(ask) & (ask <= lim)
                if ok.any():
                    i = int(np.argmax(ok)); px = float(ask[i]); fee_out = float(CM.fee(px / r.spot)) * r.spot
                    rows.append(dict(base_row, rule=f"target {int(tg*100)}%", pnl_per_prem=(sold - fee_in - px - fee_out) / sold, exit_hours=float(hrs[i]), closed=True))
                else:
                    rows.append(dict(base_row, rule=f"target {int(tg*100)}%", pnl_per_prem=(sold - fee_in - payoff) / sold if dp else np.nan, exit_hours=float(r.hours), closed=False))
df = pd.DataFrame(rows); cv = pd.DataFrame(curve)
out = pathlib.Path("results"); out.mkdir(exist_ok=True)
df.to_csv(out / "intraday_backfill.csv", index=False)
if not cv.empty:
    cvm = cv.groupby(["base", "kind", "hours"]).ratio.median().reset_index()
    cvm.to_csv(out / "intraday_decay_curve.csv", index=False)
lines = ["# Intraday short backfill (sell at 19:20 UTC bid; buy back at target or hold to settlement)\n",
         "pnl_per_prem = net P&L per $1 premium received (taker fees both ways, 12.5% cap). closed = share of legs bought back before expiry.\n"]
if not df.empty:
    sm = df.groupby("rule").agg(legs=("pnl_per_prem", "size"), mean=("pnl_per_prem", "mean"), median=("pnl_per_prem", "median"), worst=("pnl_per_prem", "min"),
                                 hit=("pnl_per_prem", lambda x: (x > 0).mean()), closed=("closed", "mean"), exit_h=("exit_hours", "median")).reset_index()
    lines.append(sm.round(3).to_markdown(index=False))
    lines.append("\n## by base (hold)\n")
    lines.append(df[df.rule == "hold"].groupby("base").agg(legs=("pnl_per_prem", "size"), mean=("pnl_per_prem", "mean"), worst=("pnl_per_prem", "min")).round(3).reset_index().to_markdown(index=False))
    if not cv.empty:
        lines.append("\n## mid decay (median mid_t / mid_entry) at +2h / +6h / +10h\n")
        piv = cvm[cvm.hours.isin([2.0, 6.0, 10.0])].pivot_table(index=["base", "kind"], columns="hours", values="ratio").round(2)
        lines.append(piv.to_markdown())
(out / "intraday_backfill.md").write_text("\n".join(lines)); print("\n".join(lines))
