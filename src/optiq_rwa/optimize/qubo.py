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
    p2 = p2 or 2 * scale
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


def solve_sa(Q, sweeps=200, t0=None, t1=None, seed=0, restarts=2):
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
