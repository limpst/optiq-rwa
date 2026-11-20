"""NAV metrics: return, vol, SR, IR, MDD, CVaR, skew/kurtosis, and the Deflated Sharpe Ratio (DSR).

Definitions (nightly returns r_t, n nights, 365 periods/yr):
  SR  = mean(r) / sd(r) * sqrt(365)                       Sharpe vs zero
  IR  = (mean(r) - rwa/365) / sd(r) * sqrt(365)           information ratio vs the RWA benchmark (deterministic)
  MDD = min_t (NAV_t / max_{s<=t} NAV_s - 1)
  DSR = Phi( (SR_p - SR0) * sqrt(n - 1) / sqrt(1 - g3*SR_p + (g4 - 1)/4 * SR_p^2) )     Bailey & Lopez de Prado (2014)
        SR_p = per-period Sharpe of the *excess over RWA* (the overlay's skill; the RWA accrual itself is riskless drift),
        g3 skew, g4 kurtosis (non-excess), SR0 = expected max SR of N unrelated trials:
        SR0 = sqrt(V[SR]) * ((1 - gamma) Z(1 - 1/N) + gamma Z(1 - 1/(N e))), gamma = 0.5772
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm, skew, kurtosis

EULER = 0.5772156649


def nightly_returns(nav: pd.Series) -> np.ndarray:
    nav = pd.Series(nav).dropna()
    full = pd.concat([pd.Series([1.0]), nav.reset_index(drop=True)])
    return full.pct_change().dropna().values


def nav_metrics(nav: pd.Series, rwa_rate: float = 0.045) -> dict:
    nav = pd.Series(nav).dropna()
    full = pd.concat([pd.Series([1.0]), nav.reset_index(drop=True)])
    r = full.pct_change().dropna().values
    n = len(r)
    if n == 0:
        return {}
    ann = full.iloc[-1] ** (365 / n) - 1
    sd = r.std(ddof=1) if n > 1 else np.nan
    vol = sd * np.sqrt(365) if n > 1 else np.nan
    dd = (full / full.cummax() - 1).min()
    q = np.quantile(r, 0.05)
    ok = bool(sd and sd > 1e-12)
    sr_p = r.mean() / sd if ok else np.nan
    return {
        "ann_return": ann,
        "excess_vs_rwa": ann - rwa_rate,
        "ann_vol": vol,
        "sharpe": sr_p * np.sqrt(365) if ok else np.nan,
        "ir_vs_rwa": (r.mean() - rwa_rate / 365) / sd * np.sqrt(365) if ok else np.nan,
        "sharpe_vs_rwa": (r.mean() * 365 - rwa_rate) / vol if ok else np.nan,   # kept for older tables
        "max_drawdown": dd,
        "cvar5_night": r[r <= q].mean(),
        "worst_night": r.min(),
        "skew": float(skew(r)) if n > 2 else np.nan,
        "kurt": float(kurtosis(r, fisher=False)) if n > 3 else np.nan,
        "n_nights": n,
        "sr_period": sr_p,
        "ir_period": (r.mean() - rwa_rate / 365) / sd if ok else np.nan,
    }


def expected_max_sharpe(sr_var: float, n_trials: int) -> float:
    """SR0: expected maximum per-period Sharpe among n_trials unrelated strategies with SR variance sr_var."""
    if n_trials <= 1 or not np.isfinite(sr_var) or sr_var <= 0:
        return 0.0
    return np.sqrt(sr_var) * ((1 - EULER) * norm.ppf(1 - 1 / n_trials) + EULER * norm.ppf(1 - 1 / (n_trials * np.e)))


def deflated_sharpe(sr_period: float, n: int, skew_: float, kurt_: float, n_trials: int, sr_var: float) -> float:
    """Probability that the true Sharpe exceeds SR0 given selection among n_trials, non-normality and track length."""
    if not np.isfinite(sr_period) or n < 3:
        return np.nan
    sr0 = expected_max_sharpe(sr_var, n_trials)
    g3 = 0.0 if not np.isfinite(skew_) else skew_
    g4 = 3.0 if not np.isfinite(kurt_) else kurt_
    denom = np.sqrt(max(1 - g3 * sr_period + (g4 - 1) / 4 * sr_period ** 2, 1e-12))
    return float(norm.cdf((sr_period - sr0) * np.sqrt(n - 1) / denom))


def add_dsr(table: pd.DataFrame, group_cols=("scenario",), sr_col="ir_period") -> pd.DataFrame:
    """Add DSR per row, treating every row inside a group as one trial of the same search (N = group size)."""
    t = table.copy()
    t["dsr"] = np.nan
    for _, idx in t.groupby(list(group_cols)).groups.items():
        g = t.loc[idx]
        srs = g[sr_col].dropna()
        var = float(srs.var(ddof=1)) if len(srs) > 1 else 0.0
        for i, row in g.iterrows():
            t.at[i, "dsr"] = deflated_sharpe(row[sr_col], int(row.get("n_nights", 0) or 0), row.get("skew", np.nan), row.get("kurt", np.nan), len(g), var)
    return t


HIGHLIGHT = dict(sharpe=0.0, ir_vs_rwa=0.5, max_drawdown=-0.15, dsr=0.95, min_nights=60)


def highlight(row) -> bool:
    """User rule (2026-11-20): SR > 0, IR > 0.5, MDD >= -15%, DSR >= 0.95; plus >= 60 nights so a zero-loss
    short sample (tail never hit) cannot pass on variance alone."""
    try:
        return bool(row["sharpe"] > HIGHLIGHT["sharpe"] and row["ir_vs_rwa"] > HIGHLIGHT["ir_vs_rwa"]
                    and row["max_drawdown"] >= HIGHLIGHT["max_drawdown"] and row["dsr"] >= HIGHLIGHT["dsr"]
                    and row.get("n_nights", 0) >= HIGHLIGHT["min_nights"])
    except (KeyError, TypeError):
        return False
