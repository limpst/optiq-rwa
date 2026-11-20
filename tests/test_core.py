import numpy as np

from optiq_rwa.data.synthetic import MarketScenario, generate
from optiq_rwa.optimize.qubo import build_qubo, solve_greedy, solve_sa
from optiq_rwa.pricing import bs_price, sigma_sqrt_t
from optiq_rwa.strategies import core


def test_sigma_sqrt_t_matches_post_example():
    # 0.589 * sqrt(12.7/8760) ~ 2.2%
    assert abs(sigma_sqrt_t(0.589, 12.7) - 0.0224) < 5e-4


def test_put_call_parity():
    c, p = bs_price(1.02, 0.6, 12.7, "call"), bs_price(1.02, 0.6, 12.7, "put")
    assert abs((c - p) - (1 - 1.02)) < 1e-12


def test_qubo_respects_budget_and_one_strike():
    edge = np.array([0.5, 0.4, 0.3, -0.2, 0.6])
    var = np.zeros(5)
    night = np.array([0, 0, 1, 1, 2]); coin = np.array(["A", "A", "A", "A", "A"])
    Q, n = build_qubo(edge, var, night, coin, k_units=2, lam=0.0)
    x, _ = solve_sa(Q, sweeps=300, seed=1, restarts=3)
    x = x[:n]
    assert x.sum() <= 2 and not (x[0] and x[1]) and x[3] == 0
    g = solve_greedy(edge, var, night, coin, 2, lam=0.0)
    assert set(np.flatnonzero(g)) == {0, 4}


def test_strategies_run():
    chain, nights, paths, coins = generate(MarketScenario(n_nights=150, seed=3))
    nav, _ = core.yield_funded_calls(chain, 100, mode="bank_event")
    assert len(nav) == 50 and nav.iloc[-1] > 0
    nav, _ = core.short_premium(chain, 100, wing_m=2.0, m=1.0)
    assert nav.notna().all()
    df = core.perp_vs_option(chain, paths, coins, 100)
    assert {"perp 100x", "daily call m=+1.0"} <= set(df.instrument)
