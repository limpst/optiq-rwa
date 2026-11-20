"""Idea 2 — event-night selection as a QUBO.

Binary x_i = "spend one budget unit on candidate i" where a candidate is a
(night, coin, strike) daily call. Energy (minimised):

    E(x) = - sum_i e_i x_i                      expected edge per unit
           + lam * sum_i v_i x_i                 own payback variance
           + lam * sum_{i<j} c_ij x_i x_j        same-night cross-coin co-movement
           + P1 * sum_{i<j in same (night,coin)} x_i x_j      at most one strike
           + P2 * (sum_i x_i + sum_b 2^b s_b - K)^2            budget <= K units

Solved with simulated annealing (SA) and compared with a greedy baseline.
"""
from __future__ import annotations

import numpy as np


def build_qubo(edge, var, night, coin, k_units, lam=0.5, rho=0.7, p1=None, p2=None):
    edge, var = np.asarray(edge, float), np.asarray(var, float)
    n = len(edge)
    scale = max(np.abs(edge).max(), 1e-6)
    p1 = p1 or 4 * scale
    p2 = p2 or 0.1 * scale   # soft budget: a larger P2 freezes SA in the empty state (see results/qubo_bench.md)
    n_slack = int(np.ceil(np.log2(k_units + 1))) if k_units > 0 else 0
    N = n + n_slack
    Q = np.zeros((N, N))
    Q[np.arange(n), np.arange(n)] += -edge + lam * var
    night, coin = np.asarray(night), np.asarray(coin)
    same_night = night[:, None] == night[None, :]
    same_coin = coin[:, None] == coin[None, :]
    sd = np.sqrt(np.maximum(var, 0))
    cross = same_night & ~same_coin
    Q[:n, :n] += np.where(cross, lam * rho * np.outer(sd, sd) / 2, 0)
    Q[:n, :n] += np.where(same_night & same_coin & ~np.eye(n, dtype=bool), p1 / 2, 0)
    # budget equality with slack: (a.x - K)^2 = x'aa'x - 2K a.x + K^2
    a = np.concatenate([np.ones(n), 2.0 ** np.arange(n_slack)])
    Q += p2 * np.outer(a, a)
    Q[np.arange(N), np.arange(N)] += -2 * p2 * k_units * a
    Q = (Q + Q.T) / 2
    return Q, n


def energy(Q, x):
    return float(x @ Q @ x)


def solve_sa(Q, sweeps=500, t0=None, t1=None, seed=0, restarts=4):
    rng = np.random.default_rng(seed)
    N = Q.shape[0]
    diag = np.diag(Q).copy()
    off = Q - np.diag(diag)
    t0 = t0 or max(np.abs(Q).max(), 1e-9)
    t1 = t1 or t0 * 1e-3
    best_x, best_e = None, np.inf
    for _ in range(restarts):
        x = np.zeros(N)
        field = off @ x
        temps = np.geomspace(t0, t1, sweeps)
        for T in temps:
            for i in rng.permutation(N):
                d = (1 - 2 * x[i]) * (diag[i] + 2 * field[i])
                if d < 0 or rng.random() < np.exp(-d / T):
                    step = 1 - 2 * x[i]
                    x[i] += step
                    field += step * off[:, i]
        e = energy(Q, x)
        if e < best_e:
            best_x, best_e = x.copy(), e
    return best_x, best_e


def solve_greedy(edge, var, night, coin, k_units, lam=0.5):
    """Pick the best risk-adjusted candidates, one per (night, coin), until K units."""
    score = np.asarray(edge) - lam * np.asarray(var)
    order = np.argsort(-score)
    used, x = set(), np.zeros(len(score))
    for i in order:
        if x.sum() >= k_units or score[i] <= 0:
            break
        key = (night[i], coin[i])
        if key in used:
            continue
        used.add(key)
        x[i] = 1
    return x


def pair_penalty(var, night, coin, lam, rho):
    """Same-night cross-coin co-movement coefficients c_ij (as in build_qubo), upper-triangular."""
    night, coin = np.asarray(night), np.asarray(coin)
    sd = np.sqrt(np.maximum(np.asarray(var, float), 0))
    cross = (night[:, None] == night[None, :]) & (coin[:, None] != coin[None, :])
    return np.triu(np.where(cross, lam * rho * np.outer(sd, sd), 0.0), 1)


def true_objective(x, edge, var, night, coin, lam, rho):
    """Constraint-free objective  -(e - lam v).x + sum_{i<j} c_ij x_i x_j  (what all solvers minimise)."""
    x = np.asarray(x, float)[: len(edge)]
    c = pair_penalty(var, night, coin, lam, rho)
    return float(-(np.asarray(edge) - lam * np.asarray(var)) @ x + x @ c @ x)


def solve_milp(edge, var, night, coin, k_units, lam=0.5, rho=0.7):
    """Exact solution via scipy MILP: one strike per (night, coin), sum x <= K.

    Pair penalty c_ij x_i x_j (c_ij = lam*rho*sd_i*sd_j, same night, different coin) is linearised
    with y_ij >= x_i + x_j - 1, 0 <= y_ij <= 1 (exact because c_ij >= 0).
    """
    from scipy.optimize import Bounds, LinearConstraint, milp
    from scipy.sparse import lil_matrix

    edge, var = np.asarray(edge, float), np.asarray(var, float)
    n = len(edge)
    c = pair_penalty(var, night, coin, lam, rho)
    ii, jj = np.nonzero(c)
    m = len(ii)
    obj = np.concatenate([-(edge - lam * var), c[ii, jj]])
    groups = {}
    for i, key in enumerate(zip(np.asarray(night).tolist(), np.asarray(coin).tolist())):
        groups.setdefault(key, []).append(i)
    rows = 1 + len(groups) + m
    A = lil_matrix((rows, n + m))
    lo, hi = np.full(rows, -np.inf), np.zeros(rows)
    A[0, :n] = 1
    hi[0] = k_units
    for r, idx in enumerate(groups.values(), start=1):
        A[r, idx] = 1
        hi[r] = 1
    for r, (i, j) in enumerate(zip(ii, jj), start=1 + len(groups)):
        A[r, i], A[r, j], A[r, n + r - 1 - len(groups)] = 1, 1, -1   # x_i + x_j - y <= 1
        hi[r] = 1
    res = milp(obj, constraints=LinearConstraint(A.tocsr(), lo, hi),
               integrality=np.concatenate([np.ones(n), np.zeros(m)]), bounds=Bounds(0, 1))
    return np.round(res.x[:n])


def polish(x, edge, var, night, coin, k_units, lam=0.5, rho=0.7, max_iter=50):
    """Feasible 1-flip / swap descent on the true objective (fixes SA's last-mile misses)."""
    edge, var = np.asarray(edge, float), np.asarray(var, float)
    night, coin = np.asarray(night), np.asarray(coin)
    n = len(edge)
    c = pair_penalty(var, night, coin, lam, rho)
    c = c + c.T
    lin = -(edge - lam * var)
    same = (night[:, None] == night[None, :]) & (coin[:, None] == coin[None, :])
    x = (np.asarray(x)[:n] > 0).astype(float)

    def f(z):
        return float(lin @ z + 0.5 * z @ c @ z)

    cur = f(x)
    for _ in range(max_iter):
        best, bx = cur, None
        on, off = np.flatnonzero(x > 0), np.flatnonzero(x == 0)
        trials = [(i, None) for i in on] + [(None, j) for j in off] + [(i, j) for i in on for j in off]
        for i, j in trials:
            z = x.copy()
            if i is not None:
                z[i] = 0
            if j is not None:
                z[j] = 1
            if z.sum() > k_units or (j is not None and (same[j] & (z > 0)).sum() > 1):
                continue
            val = f(z)
            if val < best - 1e-12:
                best, bx = val, z
        if bx is None:
            break
        x, cur = bx, best
    return x
