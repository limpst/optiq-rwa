"""Black-Scholes helpers in *relative* units (spot = 1).

All option prices in this project are expressed as a fraction of spot at
entry, so results are comparable across coins and nights.
"""
from __future__ import annotations

import numpy as np
from scipy.stats import norm

HOURS_PER_YEAR = 8760.0


def sigma_sqrt_t(iv, hours):
    """Expected 1-sigma move over `hours` (e.g. 0.589 * sqrt(12.7/8760) ~ 2.2%)."""
    return np.asarray(iv) * np.sqrt(np.asarray(hours) / HOURS_PER_YEAR)


def bs_price(k_rel, iv, hours, kind="call"):
    """Undiscounted Black-Scholes price with spot = 1 (rates ~0 over one night)."""
    k_rel = np.asarray(k_rel, dtype=float)
    s = sigma_sqrt_t(iv, hours)
    d1 = (-np.log(k_rel) + 0.5 * s**2) / s
    d2 = d1 - s
    if kind == "call":
        return norm.cdf(d1) - k_rel * norm.cdf(d2)
    return k_rel * norm.cdf(-d2) - norm.cdf(-d1)


def prob_itm(k_rel, iv, hours, kind="call"):
    """Risk-neutral probability of finishing in the money (N(d2))."""
    s = sigma_sqrt_t(iv, hours)
    d2 = (-np.log(np.asarray(k_rel, dtype=float)) - 0.5 * s**2) / s
    return norm.cdf(d2) if kind == "call" else norm.cdf(-d2)


def prob_beyond(level_rel, iv, hours, kind="call"):
    """Model probability that settlement clears `level_rel` (e.g. breakeven = K + premium)."""
    return prob_itm(level_rel, iv, hours, kind)


def payoff(settle_rel, k_rel, kind="call"):
    settle_rel = np.asarray(settle_rel, dtype=float)
    k_rel = np.asarray(k_rel, dtype=float)
    if kind == "call":
        return np.maximum(settle_rel - k_rel, 0.0)
    return np.maximum(k_rel - settle_rel, 0.0)
