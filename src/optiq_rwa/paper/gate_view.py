"""Gate thresholds for the dashboard: how far each live leg is from passing the idea-8 execution gate.

For a buy leg the gate passes when  pb_lb · mid − ask − fee(ask) > 0,  pb_lb = payback − z·se.
  required payback  pb* = (ask + fee(ask)) / mid           (what the calibrated lower bound must reach)
  required ask      ask* = pb_lb · mid / (1 + fee_rate)    (how far the ask must fall at today's calibration)
For a sell leg the gate passes when  bid − fee(bid) − pb_ub · mid > 0,  pb_ub = payback + z·se.
  pb* = (bid − fee(bid)) / mid,  bid* = pb_ub · mid / (1 − fee_rate).
fee_rate = fee(px)/px (12.5% when the cap binds, else 0.03% · spot / px).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..data import store
from ..data.live import live_chain
from . import gate as g
from .engine import _nearest, tradable_bases, _is_event_day

LEGS = [("buy", "call", 1.0), ("sell", "call", 1.5), ("sell", "put", -1.5)]


def thresholds(con=None, min_hours: float = 1.0, max_hours: float = 30.0) -> pd.DataFrame:
    con = con or store.connect()
    snap_id = store.latest_snap_id(con)
    if snap_id is None:
        return pd.DataFrame()
    ts, date = con.execute("SELECT ts_ms, date FROM snapshots WHERE snap_id=?", (snap_id,)).fetchone()
    event = _is_event_day(date)
    table = g.load_payback()
    rows = []
    for b in tradable_bases(con, date):
        ch = None
        for rank in (0, 1):
            c = live_chain(con, snap_id, b, rank)
            if not c.empty and min_hours <= c.hours.iloc[0] <= max_hours:
                ch = c
                break
        if ch is None:
            continue
        for side, kind, m in LEGS:
            r = _nearest(ch, kind, m, need="ask" if side == "buy" else "bid")
            if r is None:
                continue
            pb, se = g.expected_payback(table, b, kind, float(r.m), event, with_se=True)
            px = float(r.ask if side == "buy" else r.bid)
            mid = float(r.mid)
            if pb is None or not np.isfinite(px) or px <= 0 or not np.isfinite(mid) or mid <= 0:
                continue
            fee = float(g.COST_MODEL.fee(px / r.spot)) * float(r.spot)
            fee_rate = fee / px
            pb_b1 = max(pb - 1.0 * se, 0.0) if side == "buy" else pb + 1.0 * se      # relaxed twin (z = 1)
            edge_z1 = (pb_b1 * mid - px - fee) if side == "buy" else (px - fee - pb_b1 * mid)
            if side == "buy":
                pb_b = max(pb - g.GATE_Z * se, 0.0)
                pb_req = (px + fee) / mid
                px_req = pb_b * mid / (1 + fee_rate)
                edge = pb_b * mid - px - fee
            else:
                pb_b = pb + g.GATE_Z * se
                pb_req = (px - fee) / mid
                px_req = pb_b * mid / max(1 - fee_rate, 1e-9)
                edge = px - fee - pb_b * mid
            rows.append(dict(base=b, side=side, kind=kind, m=round(float(r.m), 2), instrument_name=r.instrument_name, hours=round(float(r.hours), 1),
                             mid=mid, px=px, fee=fee, fee_rate=fee_rate, payback=pb, se=se, z=g.GATE_Z, payback_bound=pb_b, payback_required=pb_req,
                             gap=pb_b - pb_req if side == "buy" else pb_req - pb_b, px_required=px_req,
                             px_move_pct=(px_req / px - 1.0), edge_per_unit=edge, passes=bool(edge > 0),
                             payback_bound_z1=pb_b1, passes_z1=bool(edge_z1 > 0), passes_point=bool(((pb * mid - px - fee) if side == "buy" else (px - fee - pb * mid)) > 0)))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    pd.set_option("display.width", 220, "display.max_columns", 30)
    print(thresholds().round(4).to_string(index=False))
