"""Dry-run (paper) order engine on live Deribit quotes. NO ORDERS ARE SENT.

This module imports nothing from any private/authenticated endpoint. Fills are
simulated against the latest snapshot in SQLite: buys fill at the best ask,
sells at the best bid, walking order_book levels until the USD target is filled (VWAP; level 0 of book_summary
quote if no depth). Deribit trading fee is charged on every fill, settlement fee on ITM settlement (CostModel). Positions
settle at Deribit's delivery price for the expiry date (08:00 UTC).

Strategies (same ideas as strategies.core, applied to one live chain):
  yield_calls    idea 1: spend NAV*rwa_rate/365*budget_mult on calls at m ~ +1.0 (per base, equal split)
  short_condor   idea 3: sell strangle at |m| ~ 1.5, buy wings at |m| ~ 2.5, `frac` of NAV notional
  *_gated        idea 8: same plan as the base strategy, but each base's package is sent only when
                 expected edge − (spread + fee) > 0 (paper.gate). Blocked packages are logged as status='gated'
                 rows, so ungated vs gated NAV can be compared night by night.

CLI (run from repo root; PYTHONPATH=src):
  python -m optiq_rwa.paper.engine trade  [--nav 1000000] [--min-hours 6] [--max-hours 26]
  python -m optiq_rwa.paper.engine settle
  python -m optiq_rwa.paper.engine nav
  python -m optiq_rwa.paper.engine book
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import time

import numpy as np
import pandas as pd

from ..backtest.costs import BASE as COST_MODEL
from ..config import SETTINGS
from ..data import store
from ..data.live import index_name_of, live_chain
from . import gate as gate_mod

STRATEGIES = {
    "yield_calls": dict(m=1.0, budget_mult=1.0),
    "short_condor": dict(m=1.5, wing_m=2.5, frac=0.25),
    # regime_switch: rich_iv -> short_condor legs, otherwise yield_calls only on event nights (risk.regime.classify_live)
    "regime_switch": dict(m=1.0, budget_mult=3.0, short_m=1.5, wing_m=2.5, frac=0.25),
}
# idea 8: gated twins (same parameters, execution-economics gate on). z = one-sided bound on the calibrated payback:
#   *_gated     z = GATE_Z (1.645, 5% quantile)   conservative
#   *_gated_z1  z = 1.0 (16% quantile)            relaxed twin, to measure how much the bound costs
STRATEGIES.update({f"{k}_gated": dict(v, base=k, gate=True) for k, v in list(STRATEGIES.items())})
STRATEGIES.update({f"{k}_gated_z1": dict(v, base=k, gate=True, gate_z=1.0) for k, v in list(STRATEGIES.items()) if not v.get("gate")})
TOL_M = 0.35          # accept strikes within this distance of the target m


def _nearest(chain: pd.DataFrame, kind: str, m_target: float, need: str = "both", tol: float = TOL_M, outward: float = 0.0):
    """Strike closest to m_target with a usable quote. need: 'bid' (we sell), 'ask' (we buy), 'both'.
    outward > 0 also accepts strikes further OTM than the target by up to `outward` (for thin wings)."""
    ok = (chain.kind == kind)
    if need in ("ask", "both"):
        ok &= chain.ask.notna() & (chain.ask > 0)
    if need in ("bid", "both"):
        ok &= chain.bid.notna() & (chain.bid > 0)
    sub = chain[ok]
    if sub.empty:
        return None
    d = sub.m - m_target
    sign = 1.0 if m_target >= 0 else -1.0
    far = (d * sign).clip(lower=0)                          # distance further OTM
    near = (-d * sign).clip(lower=0)                        # distance closer to ATM
    good = sub[(near <= tol) & (far <= max(tol, outward))]
    if good.empty:
        return None
    return good.loc[(good.m - m_target).abs().idxmin()]


def _contract_size(con, name) -> float:
    r = con.execute("SELECT contract_size, inverse, min_trade_amount FROM instruments WHERE instrument_name=?", (name,)).fetchone()
    return (r[0] or 1.0), bool(r[1]), (r[2] or 0.0)


def plan_orders(con, name, p, chains, nav, date=None) -> list[dict]:
    """Pure planning: the orders a strategy would send on these chains at this NAV. No DB writes."""
    plan = []
    name = p.get("base", name)
    if name == "yield_calls" or (name == "regime_switch" and _regime_mode(con, date) == "buy_events"):
        if name == "regime_switch" and not _is_event_day(date):
            return plan
        budget = nav * SETTINGS.rwa_rate / 365 * p["budget_mult"]
        per = budget / max(len(chains), 1)
        for b, ch in chains.items():
            row = _nearest(ch, "call", p["m"], need="ask")
            if row is not None:
                plan.append(dict(base=b, row=row, side="buy", usd=per, note=f"m={row.m:.2f} target={p['m']}"))
    elif name == "short_condor" or (name == "regime_switch" and _regime_mode(con, date) == "sell"):
        m, wing, frac = (p.get("short_m", p.get("m")), p["wing_m"], p["frac"])
        per_leg = nav * frac / max(len(chains), 1)
        for b, ch in chains.items():
            legs = [("call", m, "sell"), ("put", -m, "sell"), ("call", wing, "buy"), ("put", -wing, "buy")]
            rows = [(_nearest(ch, k, mm, need="bid" if side == "sell" else "ask", outward=0.0 if side == "sell" else 2.0), side) for k, mm, side in legs]
            if any(r is None for r, _ in rows):
                continue
            units = per_leg / float(ch.spot.iloc[0])
            for r, side in rows:
                cs, _, _ = _contract_size(con, r.instrument_name)
                px = float(r.ask if side == "buy" else r.bid)
                plan.append(dict(base=b, row=r, side=side, usd=units * px * cs, note=f"m={r.m:.2f}"))
    return plan


_REGIME_CACHE: dict = {}
_PAYBACK: dict = {}


def _payback_table() -> pd.DataFrame:
    if "t" not in _PAYBACK:
        _PAYBACK["t"] = gate_mod.load_payback()
    return _PAYBACK["t"]


def gated_plan(con, name, p, chains, nav, date) -> tuple[list[dict], list[dict]]:
    """(orders to send, packages blocked by the gate). Ungated strategies block nothing."""
    plan = plan_orders(con, name, p, chains, nav, date)
    if not p.get("gate"):
        return plan, []
    return gate_mod.apply(plan, _payback_table(), _is_event_day(date), z=p.get("gate_z"))


def _regime_mode(con, date) -> str:
    """'sell' when the live regime is rich_iv for the majority of classified bases, else 'buy_events'. Cached per date."""
    if date in _REGIME_CACHE:
        return _REGIME_CACHE[date]
    mode = "buy_events"
    try:
        from ..risk.regime import classify_live
        live = classify_live(con)
        if not live.empty and (live.label == "rich_iv").mean() >= 0.5:
            mode = "sell"
    except Exception:
        pass
    _REGIME_CACHE[date] = mode
    return mode


def _is_event_day(date) -> bool:
    try:
        from ..data.events import event_dates
        return pd.Timestamp(date).date() in event_dates(("FOMC", "CPI"))
    except Exception:
        return False


def _walk_book(con, snap_id, row, side, usd_target, cs=None, min_amt=None) -> dict:
    """Depth walk (no writes). Buys consume ask levels, sells bid levels, ascending level, until usd_target is filled.

    Returns dict(px0, vwap, qty, fill_usd, levels_used, slippage_usd, fee_usd, partial). Inverse quotes are converted to
    USD with spot (as live_chain does). Without order_book rows the level-0 quote from `row` is used with unlimited depth."""
    if cs is None:
        cs, _, min_amt = _contract_size(con, row.instrument_name)
    _, inverse, _ = _contract_size(con, row.instrument_name)
    spot = float(row.spot)
    px0 = float(row.ask if side == "buy" else row.bid)
    out = dict(px0=px0, vwap=np.nan, qty=0.0, fill_usd=0.0, levels_used=0, slippage_usd=0.0, fee_usd=0.0, partial=False)
    if not np.isfinite(px0) or px0 <= 0 or usd_target <= 0:
        return out
    pc, ac = ("ask_px", "ask_amt") if side == "buy" else ("bid_px", "bid_amt")
    lv = con.execute(f"SELECT {pc},{ac} FROM order_book WHERE snap_id=? AND instrument_name=? AND {pc} IS NOT NULL AND {ac}>0 ORDER BY level",
                     (snap_id, row.instrument_name)).fetchall()
    levels = [(p * spot if inverse else p, a) for p, a in lv if p and p > 0]
    if not levels:
        levels = [(px0, np.inf)]
    remaining, qty, usd, used = float(usd_target), 0.0, 0.0, 0
    for px, amt in levels:
        take = min(remaining, amt * px * cs)
        if take <= 1e-12:
            break
        qty += take / (px * cs)
        usd += take
        remaining -= take
        used += 1
        if remaining <= 1e-9 * max(usd_target, 1.0):
            remaining = 0.0
            break
    if qty <= 0:
        return out
    vwap = usd / (qty * cs)
    out.update(vwap=vwap, qty=qty, fill_usd=usd, levels_used=used, partial=remaining > 0,
               slippage_usd=((vwap - px0) if side == "buy" else (px0 - vwap)) * qty * cs,
               fee_usd=min(COST_MODEL.fee_rel * spot * qty * cs, COST_MODEL.fee_cap * usd))
    return out


def _place(con, snap_id, ts, date, strategy, row, side, usd_target, note=""):
    """Simulate one order: qty from USD target, walking book depth (VWAP fill). Returns signed cash (fill USD, fee excluded; fee is in paper_orders)."""
    cs, inverse, min_amt = _contract_size(con, row.instrument_name)
    w = _walk_book(con, snap_id, row, side, usd_target, cs, min_amt)
    if w["qty"] <= 0:
        con.execute("INSERT INTO paper_orders (ts_ms,date,strategy,instrument_name,side,qty,status,spot,snap_id,note) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (ts, date, strategy, row.instrument_name, side, 0.0, "rejected", float(row.spot), snap_id, "no quote"))
        return 0.0
    qty, fill_usd, vwap = w["qty"], w["fill_usd"], w["vwap"]
    flags = []
    if w["partial"]:
        flags.append("partial: depth exhausted")
    if qty < min_amt:
        flags.append(f"below_min_trade_amount({min_amt})")
    con.execute("INSERT INTO paper_orders (ts_ms,date,strategy,instrument_name,side,qty,limit_px,status,fill_px,fill_usd,fill_ts_ms,spot,snap_id,note,fee_usd,slippage_usd,levels_used) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (ts, date, strategy, row.instrument_name, side, qty, w["px0"], "filled", vwap, fill_usd, ts, float(row.spot), snap_id,
                 " ".join([note] + flags).strip(), w["fee_usd"], w["slippage_usd"], w["levels_used"]))
    con.execute("INSERT INTO paper_positions (strategy,instrument_name,side,qty,entry_px,entry_usd,entry_ts_ms,expiry_ts,spot_entry) VALUES (?,?,?,?,?,?,?,?,?)",
                (strategy, row.instrument_name, side, qty, vwap, fill_usd, ts, int(row.expiration_ts), float(row.spot)))
    return -fill_usd if side == "buy" else fill_usd


def current_nav(con, strategy, initial) -> float:
    r = con.execute("SELECT nav FROM paper_nav WHERE strategy=? ORDER BY date DESC LIMIT 1", (strategy,)).fetchone()
    return r[0] if r else initial


def tradable_bases(con, date) -> list[str]:
    df = store.read(con, "SELECT base FROM volume_daily WHERE date=? AND universe_pass=1", (date,))
    return sorted(set(df.base) | set(SETTINGS.focus_bases))


def trade(con=None, nav0=1_000_000.0, min_hours=6.0, max_hours=26.0, strategies=None, log=print) -> dict:
    con = con or store.connect()
    snap_id = store.latest_snap_id(con)
    if snap_id is None:
        raise SystemExit("no snapshot yet: run python -m optiq_rwa.data.live snapshot")
    ts, date = con.execute("SELECT ts_ms, date FROM snapshots WHERE snap_id=?", (snap_id,)).fetchone()
    if time.time() * 1000 - ts > 30 * 60 * 1000:
        log(f"warning: latest snapshot is {(time.time()*1000-ts)/6e4:.0f} min old")
    done = store.read(con, "SELECT DISTINCT strategy FROM paper_orders WHERE date=?", (date,)).strategy.tolist()
    out = {}
    for name, p in (strategies or STRATEGIES).items():
        if name in done:
            log(f"{name}: already traded on {date}, skip")
            continue
        nav = current_nav(con, name, nav0)
        bases = tradable_bases(con, date)
        chains = {}
        for b in bases:
            for rank in (0, 1):
                ch = live_chain(con, snap_id, b, rank)
                if not ch.empty and min_hours <= ch.hours.iloc[0] <= max_hours:
                    chains[b] = ch
                    break
        if not chains:
            log(f"{name}: no expiry within [{min_hours},{max_hours}]h for {bases}; nothing to do")
            continue
        cash, n = 0.0, 0
        kept, blocked = gated_plan(con, name, p, chains, nav, date)
        for o in kept:
            note = o["note"] + (f" edge_pkg={o['package_edge_usd']:.2f}" if "package_edge_usd" in o else "")
            cash += _place(con, snap_id, ts, date, name, o["row"], o["side"], o["usd"], note)
            n += 1
        for o in blocked:
            r = o["row"]
            con.execute("INSERT INTO paper_orders (ts_ms,date,strategy,instrument_name,side,qty,limit_px,status,spot,snap_id,note) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (ts, date, name, r.instrument_name, o["side"], 0.0, float(r.ask if o["side"] == "buy" else r.bid), "gated", float(r.spot), snap_id,
                         f"{o['note']} edge_pkg={o['package_edge_usd']:.2f} edge_leg={o['edge_usd']:.2f}"))
        con.commit()
        out[name] = dict(date=date, snap_id=snap_id, nav_before=nav, orders=n, gated=len(blocked), cash_flow_usd=round(cash, 2), bases=list(chains))
        log(json.dumps(out[name]))
    return out


def preview(con=None, nav0=1_000_000.0, min_hours=1.0, max_hours=30.0) -> pd.DataFrame:
    """What each strategy would order on the latest snapshot right now (no writes). For the dashboard."""
    con = con or store.connect()
    snap_id = store.latest_snap_id(con)
    if snap_id is None:
        return pd.DataFrame()
    ts, date = con.execute("SELECT ts_ms, date FROM snapshots WHERE snap_id=?", (snap_id,)).fetchone()
    bases = tradable_bases(con, date)
    chains = {}
    for b in bases:
        for rank in (0, 1):
            ch = live_chain(con, snap_id, b, rank)
            if not ch.empty and min_hours <= ch.hours.iloc[0] <= max_hours:
                chains[b] = ch
                break
    rows = []
    for name, p in STRATEGIES.items():
        nav = current_nav(con, name, nav0)
        kept, blocked = gated_plan(con, name, p, chains, nav, date)
        for o in kept + blocked:
            r = o["row"]
            cs, _, min_amt = _contract_size(con, r.instrument_name)
            px = float(r.ask if o["side"] == "buy" else r.bid)
            w = _walk_book(con, snap_id, r, o["side"], o["usd"], cs, min_amt)
            rows.append(dict(strategy=name, base=o["base"], instrument_name=r.instrument_name, side=o["side"], m=round(float(r.m), 2),
                             px_usd=px, qty=o["usd"] / (px * cs) if px > 0 else np.nan, usd=o["usd"], hours=round(float(r.hours), 1),
                             spot=float(r.spot), quote_source=r.quote_source, min_trade_amount=min_amt,
                             fee_usd=w["fee_usd"], slippage_usd=w["slippage_usd"], levels_used=w["levels_used"], fill_vwap=w["vwap"],
                             regime_mode=_regime_mode(con, date) if p.get("base", name) == "regime_switch" else "",
                             gate="" if not p.get("gate") else ("pass" if o in kept else "blocked"),
                             edge_pkg_usd=o.get("package_edge_usd", np.nan)))
    return pd.DataFrame(rows)


def settle(con=None, log=print) -> int:
    con = con or store.connect()
    now = int(time.time() * 1000)
    pos = store.read(con, "SELECT p.*, i.option_type, i.strike, i.base, i.contract_size FROM paper_positions p JOIN instruments i USING (instrument_name) "
                          "WHERE p.settled=0 AND p.expiry_ts<=?", (now,))
    n = 0
    for _, r in pos.iterrows():
        d = store.utc_date(int(r.expiry_ts))
        px = con.execute("SELECT price FROM delivery_price WHERE index_name=? AND date=?", (index_name_of(r.base), d)).fetchone()
        if not px:
            continue
        s = px[0]
        intrinsic = max(s - r.strike, 0.0) if r.option_type == "call" else max(r.strike - s, 0.0)
        payoff = intrinsic * r.qty * (r.contract_size or 1.0)
        sfee = float(COST_MODEL.settle_fee(payoff / (s * r.qty * (r.contract_size or 1.0)) if payoff > 0 and s > 0 else 0.0)) * s * r.qty * (r.contract_size or 1.0)
        pnl = (payoff - r.entry_usd if r.side == "buy" else r.entry_usd - payoff) - sfee
        con.execute("UPDATE paper_positions SET settled=1, settle_px=?, payoff_usd=?, pnl_usd=?, settle_fee_usd=? WHERE pos_id=?", (s, payoff, pnl, sfee, int(r.pos_id)))
        n += 1
    con.commit()
    log(f"settled {n} positions")
    return n


def mark_nav(con=None, nav0=1_000_000.0, date=None, log=print) -> pd.DataFrame:
    """Daily NAV per strategy = nav0 + RWA accrual - premium paid + premium received + settled payoffs - fees
    (fees = trading fees on every fill + settlement fees; slippage is already inside the VWAP fill price).

    Open positions are carried at zero (premium already spent / received), so NAV is conservative for
    long options until settlement and optimistic for short options until settlement."""
    con = con or store.connect()
    date = date or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    rows = []
    for name in STRATEGIES:
        first = con.execute("SELECT MIN(date) FROM paper_orders WHERE strategy=?", (name,)).fetchone()[0]
        if not first:
            continue
        days = (pd.Timestamp(date) - pd.Timestamp(first)).days + 1
        payoff = con.execute("SELECT COALESCE(SUM(CASE WHEN side='buy' THEN payoff_usd ELSE -payoff_usd END),0) FROM paper_positions "
                             "WHERE strategy=? AND settled=1 AND expiry_ts<=?",
                             (name, int(pd.Timestamp(date, tz="UTC").timestamp() * 1000) + 86_400_000)).fetchone()[0]
        paid = con.execute("SELECT COALESCE(SUM(fill_usd),0) FROM paper_orders WHERE strategy=? AND side='buy' AND status='filled' AND date<=?", (name, date)).fetchone()[0]
        recv = con.execute("SELECT COALESCE(SUM(fill_usd),0) FROM paper_orders WHERE strategy=? AND side='sell' AND status='filled' AND date<=?", (name, date)).fetchone()[0]
        trade_fees = con.execute("SELECT COALESCE(SUM(fee_usd),0) FROM paper_orders WHERE strategy=? AND status='filled' AND date<=?", (name, date)).fetchone()[0]
        settle_fees = con.execute("SELECT COALESCE(SUM(settle_fee_usd),0) FROM paper_positions WHERE strategy=? AND settled=1 AND expiry_ts<=?",
                                  (name, int(pd.Timestamp(date, tz="UTC").timestamp() * 1000) + 86_400_000)).fetchone()[0]
        fees = trade_fees + settle_fees
        n_open = con.execute("SELECT COUNT(*) FROM paper_positions WHERE strategy=? AND settled=0", (name,)).fetchone()[0]
        accrual = nav0 * ((1 + SETTINGS.rwa_rate / 365) ** days - 1)
        pnl = payoff - paid + recv - fees
        nav = nav0 + accrual + pnl
        rows.append(dict(date=date, strategy=name, nav=nav, cash=nav, rwa_accrual=accrual, option_pnl=pnl,
                         premium_paid=paid, premium_received=recv, n_open=n_open, fees_usd=fees))
    df = pd.DataFrame(rows)
    store.insert_df(con, "paper_nav", df)
    con.commit()
    log(df.round(2).to_string(index=False) if not df.empty else "no paper trades yet")
    return df


def book(con=None) -> dict:
    con = con or store.connect()
    return {t: store.read(con, f"SELECT * FROM {t} ORDER BY 1 DESC LIMIT 50") for t in ("paper_orders", "paper_positions", "paper_nav")}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["trade", "settle", "nav", "book", "preview"])
    ap.add_argument("--nav", type=float, default=1_000_000.0)
    ap.add_argument("--min-hours", type=float, default=6.0)
    ap.add_argument("--max-hours", type=float, default=26.0)
    a = ap.parse_args()
    con = store.connect()
    pd.set_option("display.width", 220, "display.max_columns", 30)
    if a.cmd == "trade":
        trade(con, a.nav, a.min_hours, a.max_hours)
    elif a.cmd == "preview":
        print(preview(con, a.nav).round(4).to_string(index=False))
    elif a.cmd == "settle":
        settle(con)
    elif a.cmd == "nav":
        mark_nav(con, a.nav)
    else:
        for k, v in book(con).items():
            print(f"\n== {k}\n", v.round(4).to_string(index=False) if not v.empty else "(empty)")
