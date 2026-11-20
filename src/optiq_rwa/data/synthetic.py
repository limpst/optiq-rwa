"""Synthetic crypto daily-option market, used until real Deribit data is pulled.

The generator is deliberately *parametric* so that the strategy sweep can be
run across market scenarios (how rich is implied vol? are event nights
under-priced?). Nothing here is calibrated to claim an edge exists; the
sweep shows under which assumptions each idea works.

Output (all prices relative to spot at entry = 1):
  chain : one row per (night, coin, kind, m)   -> option quotes + settlement payoff
  nights: one row per (night, coin)            -> iv, realised path summary
  paths : ndarray [night, coin, step]           -> intranight relative price path
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ..pricing import bs_price, sigma_sqrt_t

COINS_DEFAULT = {"BTC": 0.45, "ETH": 0.60, "SOL": 0.65}


@dataclass
class MarketScenario:
    n_nights: int = 600
    hours: float = 12.7                 # 19:20 UTC -> 08:00 UTC (Deribit daily expiry)
    steps: int = 13                     # intranight path resolution (~hourly)
    coins: dict = field(default_factory=lambda: dict(COINS_DEFAULT))
    rho: float = 0.7                    # cross-coin correlation of hourly returns
    t_df: float = 4.0                   # fat tails of hourly returns
    regime_ar: float = 0.9              # persistence of vol regime
    regime_sd: float = 0.25
    vrp: float = 0.10                   # implied vol premium over expected realised vol
    iv_noise: float = 0.08
    event_prob: float = 0.12            # FOMC / CPI / unlock nights (known in advance)
    event_rv_mult: float = 1.6          # realised vol multiplier on event nights
    event_iv_markup: float = 1.4        # how much the market marks IV up on event nights
    jump_prob: float = 0.03             # per night: overnight jump (news, liquidation cascade)
    jump_sd: float = 2.5                # jump size in units of the night's sigma*sqrt(T)
    skew_slope: float = 0.05            # wing IV richness per sigma of moneyness
    spread_pct: float = 0.10            # half-spread as % of mid
    spread_abs: float = 0.0002          # + half-spread floor, fraction of spot
    m_grid: tuple = (-2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0)
    seed: int = 0


def generate(sc: MarketScenario):
    rng = np.random.default_rng(sc.seed)
    coins = list(sc.coins)
    base = np.array([sc.coins[c] for c in coins])
    n, k, s = sc.n_nights, len(coins), sc.steps
    dt_h = sc.hours / s

    # --- vol regime (common) and event calendar
    v = np.zeros(n)
    for t in range(1, n):
        v[t] = sc.regime_ar * v[t - 1] + sc.regime_sd * np.sqrt(1 - sc.regime_ar**2) * rng.standard_normal()
    regime = np.exp(v - 0.5 * sc.regime_sd**2)
    event = rng.random(n) < sc.event_prob

    rv = base[None, :] * regime[:, None] * np.where(event, sc.event_rv_mult, 1.0)[:, None]
    iv_atm = (base[None, :] * regime[:, None] * (1 + sc.vrp)
              * np.where(event, sc.event_iv_markup, 1.0)[:, None]
              * np.exp(sc.iv_noise * rng.standard_normal((n, k))))

    # --- correlated fat-tailed hourly returns
    common = rng.standard_normal((n, s, 1))
    idio = rng.standard_normal((n, s, k))
    z = np.sqrt(sc.rho) * common + np.sqrt(1 - sc.rho) * idio
    chi = rng.chisquare(sc.t_df, size=(n, s, k))
    z = z * np.sqrt((sc.t_df - 2) / chi)
    sig_h = rv[:, None, :] * np.sqrt(dt_h / 8760.0)
    logret = sig_h * z - 0.5 * sig_h**2
    # overnight jumps (shared across coins when they happen) -> fat nightly tails
    jump_on = rng.random(n) < sc.jump_prob
    jump_step = rng.integers(0, s, n)
    jsz = sc.jump_sd * rv * np.sqrt(sc.hours / 8760.0) * (0.8 * rng.standard_normal((n, 1)) + 0.6 * rng.standard_normal((n, k)))
    jsz = jsz - 0.5 * jsz.var(axis=0, keepdims=True) * 0      # martingale correction applied below
    logret[np.arange(n), jump_step, :] += np.where(jump_on[:, None], jsz, 0.0)
    comp = sc.jump_prob * 0.5 * (sc.jump_sd * rv * np.sqrt(sc.hours / 8760.0)) ** 2   # E[e^J]-1 ~ var/2
    logret -= comp[:, None, :] / s
    paths = np.exp(np.cumsum(logret, axis=1))            # [n, s, k]
    paths = np.transpose(paths, (0, 2, 1))               # [n, k, s]
    settle = paths[:, :, -1]

    # --- option chain
    rows = []
    for j, c in enumerate(coins):
        ss = sigma_sqrt_t(iv_atm[:, j], sc.hours)
        for m in sc.m_grid:
            kind = "call" if m >= 0 else "put"
            kinds = ["call", "put"] if m == 0 else [kind]
            k_rel = np.exp(m * ss)
            iv_k = iv_atm[:, j] * (1 + sc.skew_slope * abs(m))
            for kd in kinds:
                mid = bs_price(k_rel, iv_k, sc.hours, kd)
                half = sc.spread_pct * mid + sc.spread_abs
                pay = np.maximum(settle[:, j] - k_rel, 0) if kd == "call" else np.maximum(k_rel - settle[:, j], 0)
                rows.append(pd.DataFrame({
                    "night": np.arange(n), "coin": c, "kind": kd, "m": m, "k_rel": k_rel,
                    "iv": iv_k, "iv_atm": iv_atm[:, j], "mid": mid,
                    "bid": np.maximum(mid - half, 0.0), "ask": mid + half,
                    "settle_rel": settle[:, j], "payoff": pay, "event": event,
                }))
    chain = pd.concat(rows, ignore_index=True)
    nights = pd.DataFrame({
        "night": np.repeat(np.arange(n), k), "coin": np.tile(coins, n),
        "event": np.repeat(event, k), "iv_atm": iv_atm.ravel(), "rv": rv.ravel(),
        "settle_rel": settle.ravel(),
    })
    return chain, nights, paths, coins
