from __future__ import annotations

import numpy as np
import pandas as pd


def nav_metrics(nav: pd.Series, rwa_rate: float = 0.045) -> dict:
    nav = nav.dropna()
    full = pd.concat([pd.Series([1.0]), nav.reset_index(drop=True)])
    r = full.pct_change().dropna().values
    n = len(r)
    ann = full.iloc[-1] ** (365 / n) - 1
    vol = r.std(ddof=1) * np.sqrt(365) if n > 1 else np.nan
    dd = (full / full.cummax() - 1).min()
    q = np.quantile(r, 0.05)
    return {
        "ann_return": ann,
        "excess_vs_rwa": ann - rwa_rate,
        "ann_vol": vol,
        "sharpe_vs_rwa": (r.mean() * 365 - rwa_rate) / vol if vol and vol > 1e-6 else np.nan,
        "max_drawdown": dd,
        "cvar5_night": r[r <= q].mean(),
        "worst_night": r.min(),
    }
