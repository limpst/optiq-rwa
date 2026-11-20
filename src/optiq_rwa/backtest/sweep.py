"""Strategy sweep: market scenarios x strategy parameters x seeds.

Walk-forward: the first `warmup` nights are training only (calibration /
QUBO edge model, refit every 4 weeks on all past nights); every strategy is
scored on the same out-of-sample nights.
"""
from __future__ import annotations

import itertools
import time

import pandas as pd

from ..data.synthetic import MarketScenario, generate
from ..risk.calibration import calibration_table
from ..strategies import core
from .metrics import nav_metrics

SCENARIOS = {
    # name: (vrp, event_iv_markup)   event realised-vol multiplier is 1.6 throughout
    "rich_iv":            (0.20, 1.8),
    "base":               (0.05, 1.4),
    "events_underpriced": (0.10, 1.1),
    "fair_iv":            (0.00, 1.6),
}


def strategy_grid(quick=False):
    g = []
    for m, mode, bm in itertools.product((0.0, 0.5, 1.0, 1.5), ("daily", "event_only", "bank_event"), (1.0, 3.0)):
        g.append(("1_yield_funded_calls", dict(m=m, mode=mode, budget_mult=bm)))
    solvers = (("greedy", 0.0), ("greedy", 0.5), ("sa", 0.5)) if not quick else (("greedy", 0.5),)
    for solver, lam in solvers:
        g.append(("2_qubo_event_selector", dict(solver=solver, lam=lam, budget_mult=1.0)))
    for m, frac, skip, wing in itertools.product((1.0, 1.5, 2.0), (0.5, 1.0), (True, False), (None, 2.0)):
        if wing is not None and wing <= m:
            continue
        g.append(("3_short_premium", dict(m=m, frac=frac, skip_events=skip, wing_m=wing)))
    return g


FUNCS = {
    "1_yield_funded_calls": core.yield_funded_calls,
    "2_qubo_event_selector": core.qubo_event_selector,
    "3_short_premium": core.short_premium,
}


def run(seeds=(0, 1, 2), n_nights=600, warmup=200, quick=False, log=print):
    rows, calib, perp = [], [], []
    for (sname, (vrp, evm)), seed in itertools.product(SCENARIOS.items(), seeds):
        t = time.time()
        sc = MarketScenario(n_nights=n_nights, vrp=vrp, event_iv_markup=evm, seed=seed)
        chain, nights, paths, coins = generate(sc)
        # idea 4: calibration on the out-of-sample window
        ct = calibration_table(chain[chain.night >= warmup])
        ct.insert(0, "scenario", sname); ct.insert(1, "seed", seed)
        calib.append(ct)
        # idea 5
        for ev_only in (False, True):
            pv = core.perp_vs_option(chain, paths, coins, warmup, event_only=ev_only)
            pv.insert(0, "scenario", sname); pv.insert(1, "seed", seed); pv.insert(2, "nights", "event" if ev_only else "all")
            perp.append(pv)
        # benchmark: RWA only
        bench = pd.Series([(1 + 0.045 / 365) ** (i + 1) for i in range(n_nights - warmup)])
        rows.append({"scenario": sname, "seed": seed, "idea": "0_rwa_only", "params": "{}", **nav_metrics(bench)})
        for idea, params in strategy_grid(quick):
            kw = dict(params)
            if idea == "2_qubo_event_selector":
                kw["seed"] = seed
            nav, info = FUNCS[idea](chain, warmup, **kw)
            rows.append({"scenario": sname, "seed": seed, "idea": idea,
                         "params": str(params), **nav_metrics(nav), **info})
        log(f"{sname:20s} seed={seed}  {time.time() - t:5.1f}s")
    return pd.DataFrame(rows), pd.concat(calib), pd.concat(perp)
