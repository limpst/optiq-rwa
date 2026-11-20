"""Ideas 1, 2, 3 and 5 as backtestable strategies.

Every NAV strategy starts at 1.0 fully invested in a tokenised T-bill style
RWA earning `rwa_rate` per year (accrued nightly), and returns a nightly NAV
series over the test window. Option P&L is per $ of premium (buyer) or per $
of spot notional (seller), all in relative units.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..optimize.qubo import build_qubo, solve_greedy, solve_sa
from ..risk.calibration import edge_model


def _lookup(chain, kind, m):
    """[night, coin] tables of ask, bid, payoff, event for one strike bucket."""
    sub = chain[(chain.kind == kind) & (chain.m == m)]
    piv = {f: sub.pivot(index="night", columns="coin", values=f) for f in ("ask", "bid", "mid", "payoff")}
    ev = sub.groupby("night").event.first()
    return piv, ev


# ---------------------------------------------------------------- idea 1
def yield_funded_calls(chain, test_start, rwa_rate=0.045, m=1.0, mode="daily",
                       budget_mult=1.0, coins=None):
    """Spend (a multiple of) the RWA yield on daily calls.

    mode: 'daily'      spend each night's accrual
          'event_only' spend accrual only on event nights (else keep it)
          'bank_event' bank accruals and spend the whole bank on event nights
    """
    piv, ev = _lookup(chain, "call", m)
    coins = coins or list(piv["ask"].columns)
    nights = [n for n in piv["ask"].index if n >= test_start]
    nav, bank, out, spent, paid = 1.0, 0.0, [], 0.0, 0.0
    for n in nights:
        accrual = nav * rwa_rate / 365
        nav += accrual
        budget = accrual * budget_mult
        spend = 0.0
        if mode == "daily":
            spend = budget
        elif mode == "event_only" and ev[n]:
            spend = budget
        elif mode == "bank_event":
            bank += budget
            if ev[n]:
                spend, bank = bank, 0.0
        if spend > 0:
            pb = np.mean([piv["payoff"].at[n, c] / piv["ask"].at[n, c] for c in coins])
            nav += spend * (pb - 1)
            spent += spend
            paid += spend * pb
        out.append(nav)
    return pd.Series(out, index=nights), {"premium_spent": spent, "payback_ask": paid / spent if spent else np.nan}


# ---------------------------------------------------------------- idea 2
def qubo_event_selector(chain, test_start, rwa_rate=0.045, budget_mult=1.0, lam=0.5,
                        solver="sa", m_set=(0.0, 0.5, 1.0, 1.5), week=7, refit_every=28,
                        units_per_week=7, prior_n=60, seed=0, rho=0.7):
    calls = chain[(chain.kind == "call") & (chain.m.isin(m_set))].copy()
    calls["pb"] = calls.payoff / calls.ask
    nights_all = sorted(calls.night.unique())
    test_nights = [n for n in nights_all if n >= test_start]
    nav, out, spent, paid, edges, var_tab, last_fit = 1.0, {}, 0.0, 0.0, None, None, -10**9
    for w0 in range(test_start, max(nights_all) + 1, week):
        if w0 - last_fit >= refit_every:
            train = calls[calls.night < w0]
            edges = edge_model(train, prior_n).set_index(["coin", "kind", "m", "event"])
            var_tab = train.groupby(["kind", "m", "event"]).pb.var()
            last_fit = w0
        cand = calls[(calls.night >= w0) & (calls.night < w0 + week)].reset_index(drop=True)
        if cand.empty:
            continue
        key = list(zip(cand.coin, cand.kind, cand.m, cand.event))
        e = np.array([edges.buy_edge.get(k, 0.0) for k in key])
        v = np.array([var_tab.get((k[1], k[2], k[3]), 1.0) for k in key])
        v = v / max(v.max(), 1e-9) * max(np.abs(e).max(), 1e-6)   # put variance on edge scale
        budget = nav * rwa_rate / 365 * week * budget_mult
        unit = budget / units_per_week
        if solver == "sa":
            Q, n = build_qubo(e, v, cand.night.values, cand.coin.values, units_per_week, lam=lam, rho=rho)
            x, _ = solve_sa(Q, sweeps=120, seed=seed + w0, restarts=1)
            x = x[:n]
        else:
            x = solve_greedy(e, v, cand.night.values, cand.coin.values, units_per_week, lam=lam)
        x = x[: len(cand)]
        if x.sum() > units_per_week:                              # repair (penalty is soft)
            keep = np.argsort(-(e - lam * v) * x)[:units_per_week]
            x = np.isin(np.arange(len(x)), keep) & (x > 0)
        sel = cand[x > 0]
        for n in sorted(cand.night.unique()):
            nav += nav * rwa_rate / 365
            s = sel[sel.night == n]
            if len(s):
                pnl = unit * (s.pb - 1).sum()
                nav += pnl
                spent += unit * len(s)
                paid += unit * s.pb.sum()
            out[n] = nav
    ser = pd.Series(out).reindex(test_nights).ffill()
    return ser, {"premium_spent": spent, "payback_ask": paid / spent if spent else np.nan,
                 "trades": int(round(spent / max(unit, 1e-12))) if spent else 0}


# ---------------------------------------------------------------- idea 3
def short_premium(chain, test_start, rwa_rate=0.045, m=1.5, frac=1.0, skip_events=True,
                  structure="strangle", wing_m=None):
    """Sell daily options at the bid against RWA collateral.

    frac   : spot notional sold per $ NAV per leg (1.0 = fully covered for calls).
    wing_m : if set, buy protective wings at |m| = wing_m at the ask (iron condor),
             so the tail is capped *and paid for*.
    """
    short_legs = [("call", m)] + ([("put", -m)] if structure == "strangle" else [])
    long_legs = []
    if wing_m is not None:
        long_legs = [("call", wing_m)] + ([("put", -wing_m)] if structure == "strangle" else [])
    shorts = [_lookup(chain, k, mm)[0] for k, mm in short_legs]
    longs = [_lookup(chain, k, mm)[0] for k, mm in long_legs]
    ev = _lookup(chain, *short_legs[0])[1]
    coins = list(shorts[0]["bid"].columns)
    nights = [n for n in shorts[0]["bid"].index if n >= test_start]
    w = frac / len(coins)
    nav, out, prem = 1.0, [], 0.0
    for n in nights:
        nav += nav * rwa_rate / 365
        if not (skip_events and ev[n]):
            pnl = 0.0
            for c in coins:
                for piv in shorts:
                    pnl += w * (piv["bid"].at[n, c] - piv["payoff"].at[n, c])
                    prem += w * piv["bid"].at[n, c] * nav
                for piv in longs:
                    pnl += w * (piv["payoff"].at[n, c] - piv["ask"].at[n, c])
            nav *= 1 + pnl
        out.append(nav)
    return pd.Series(out, index=nights), {"premium_collected": prem}


# ---------------------------------------------------------------- idea 5
def perp_vs_option(chain, paths, coins, test_start, leverages=(10, 25, 50, 100), m_set=(0.0, 1.0),
                   maint=0.005, fee=0.0005, event_only=False):
    """Same long view each night: leveraged perp (with liquidation on the path) vs daily call.

    Returns per-trade statistics with $1 at risk per trade.
    """
    n_n = paths.shape[0]
    nights = np.arange(test_start, n_n)
    ev = chain.groupby("night").event.first().reindex(nights).values
    if event_only:
        nights = nights[ev]
    rows = []
    rel = paths[nights] - 1.0                                   # [n, coin, step]
    worst = rel.min(axis=2)
    final = rel[:, :, -1]
    for L in leverages:
        liq = L * worst <= -(1 - L * maint)
        r = np.where(liq, -1.0, L * final - 2 * L * fee)
        rows.append(_stats(f"perp {L}x", r.ravel(), liq.mean()))
    for m in m_set:
        piv, _ = _lookup(chain, "call", m)
        pb = (piv["payoff"] / piv["ask"]).loc[nights, coins].values
        rows.append(_stats(f"daily call m={m:+.1f}", (pb - 1).ravel(), np.nan))
    return pd.DataFrame(rows)


def _stats(name, r, liq_rate):
    r = np.asarray(r)
    q = np.quantile(r, 0.05)
    return {"instrument": name, "trades": len(r), "mean_ret": r.mean(), "median_ret": np.median(r),
            "p_profit": (r > 0).mean(), "p_lose_all": (r <= -0.999).mean(),
            "liquidation_rate": liq_rate, "cvar5": r[r <= q].mean(), "best": r.max()}
