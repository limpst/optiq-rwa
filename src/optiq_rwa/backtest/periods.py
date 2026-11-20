"""Period returns (daily / weekly / monthly / scenario) from a NAV series.

    period_table(nav, freq="W")  -> one row per period: start, end, return, ann_vol, max_dd, n_days
    summary(nav)                 -> dict of D/W/M tables + total
    paper_nav_series(con)        -> {strategy: nav Series} from the paper book
"""
from __future__ import annotations

import numpy as np
import pandas as pd

FREQS = {"D": "D", "W": "W-SUN", "M": "ME", "Q": "QE", "Y": "YE"}


def _to_series(nav) -> pd.Series:
    s = pd.Series(nav).dropna().astype(float)
    if not isinstance(s.index, pd.DatetimeIndex):
        s.index = pd.to_datetime(s.index)
    return s.sort_index()


def period_table(nav, freq: str = "W", rwa_rate: float = 0.045) -> pd.DataFrame:
    s = _to_series(nav)
    if s.empty:
        return pd.DataFrame()
    rows = []
    for key, g in s.groupby(pd.Grouper(freq=FREQS.get(freq, freq))):
        if g.empty:
            continue
        prev = s[s.index < g.index[0]]
        start_nav = prev.iloc[-1] if len(prev) else g.iloc[0]
        full = pd.concat([pd.Series([start_nav]), g.reset_index(drop=True)])
        r = full.pct_change().dropna()
        n = len(g)
        ret = g.iloc[-1] / start_nav - 1
        rows.append(dict(period=key.strftime("%Y-%m-%d"), start=g.index[0].date(), end=g.index[-1].date(), n_days=n,
                         ret=ret, ann_ret=(1 + ret) ** (365 / max(n, 1)) - 1,
                         rwa_ret=(1 + rwa_rate / 365) ** n - 1, excess=ret - ((1 + rwa_rate / 365) ** n - 1),
                         ann_vol=r.std(ddof=1) * np.sqrt(365) if n > 1 else np.nan,
                         max_dd=(full / full.cummax() - 1).min(), worst_day=r.min(), best_day=r.max()))
    return pd.DataFrame(rows)


def summary(nav, rwa_rate: float = 0.045) -> dict:
    s = _to_series(nav)
    out = {f: period_table(s, f, rwa_rate) for f in ("D", "W", "M")}
    if not s.empty:
        n = len(s)
        out["total"] = dict(start=str(s.index[0].date()), end=str(s.index[-1].date()), n_days=n, ret=s.iloc[-1] / s.iloc[0] - 1,
                            ann_ret=(s.iloc[-1] / s.iloc[0]) ** (365 / max(n, 1)) - 1, max_dd=(s / s.cummax() - 1).min())
    return out


def paper_nav_series(con) -> dict:
    df = pd.read_sql_query("SELECT date, strategy, nav FROM paper_nav ORDER BY date", con)
    return {k: g.set_index("date").nav for k, g in df.groupby("strategy")}


def nights_to_dates(nav: pd.Series, dates: pd.Series | None = None, end=None) -> pd.Series:
    """Map a night-indexed NAV (sweep output) to calendar dates (real chain gives `date`; synthetic ends at `end`)."""
    if dates is not None:
        idx = pd.to_datetime(pd.Series(dates).reindex(nav.index).values)
    else:
        end = pd.Timestamp(end or pd.Timestamp.utcnow().date())
        idx = end - pd.to_timedelta((nav.index.max() - nav.index).astype(int), unit="D")
    return pd.Series(nav.values, index=idx)
