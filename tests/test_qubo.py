import itertools

import numpy as np

from optiq_rwa.optimize.qubo import (build_qubo, polish, solve_greedy, solve_milp, solve_sa,
                                     true_objective)
from optiq_rwa.strategies.core import repair_selection


def _instance(seed, nights=7, coins=3, strikes=4, k=7):
    rng = np.random.default_rng(seed)
    night, coin, _ = (a.ravel() for a in np.meshgrid(range(nights), range(coins), range(strikes), indexing="ij"))
    n = len(night)
    e = rng.normal(0, 0.3, n)
    e[rng.choice(n, 4, replace=False)] += 0.9
    v = rng.uniform(0, 1, n)
    v = v / v.max() * np.abs(e).max()
    return e, v, night, coin, k


def _feasible(x, night, coin, k):
    keys = list(zip(night[x > 0], coin[x > 0]))
    return x.sum() <= k and len(keys) == len(set(keys))


def test_milp_respects_budget():
    for seed in range(5):
        e, v, night, coin, k = _instance(seed)
        x = solve_milp(e, v, night, coin, k, lam=0.5, rho=0.7)
        assert _feasible(x, night, coin, k)


def test_milp_equals_brute_force_small():
    for seed in range(5):
        rng = np.random.default_rng(seed)
        n, k, lam, rho = 10, 3, 0.5, 0.7
        night = rng.integers(0, 2, n); coin = rng.integers(0, 2, n)
        e = rng.normal(0, 0.3, n); v = rng.uniform(0, 0.4, n)
        best = min(
            true_objective(np.array(b), e, v, night, coin, lam, rho)
            for b in itertools.product((0, 1), repeat=n) if _feasible(np.array(b), night, coin, k)
        )
        x = solve_milp(e, v, night, coin, k, lam, rho)
        assert abs(true_objective(x, e, v, night, coin, lam, rho) - best) < 1e-8


def test_tuned_sa_within_1pct_of_milp():
    for seed in range(5):
        e, v, night, coin, k = _instance(seed)
        lam, rho = 0.5, 0.7
        ref = true_objective(solve_milp(e, v, night, coin, k, lam, rho), e, v, night, coin, lam, rho)
        Q, n = build_qubo(e, v, night, coin, k, lam=lam, rho=rho)
        x, _ = solve_sa(Q, seed=seed)
        x = repair_selection(x[:n], e, v, lam, k, night, coin)
        x = polish(x, e, v, night, coin, k, lam, rho)
        assert _feasible(x, night, coin, k)
        assert true_objective(x, e, v, night, coin, lam, rho) <= ref + 0.01 * abs(ref)


def test_greedy_feasible():
    for seed in range(5):
        e, v, night, coin, k = _instance(seed)
        assert _feasible(solve_greedy(e, v, night, coin, k, lam=0.5), night, coin, k)
