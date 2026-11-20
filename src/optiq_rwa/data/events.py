"""Event calendar (FOMC decision days, US CPI releases, token unlocks) -> event-night flags.

data/events.csv columns: date, event, time_utc, confidence (confirmed | tentative | uncertain), source.

Night convention: the option bought on `date` (entry ~19:20 UTC) expires 08:00 UTC the next day. FOMC
decisions (18:00/19:00 UTC) and CPI prints (12:30/13:30 UTC) are already out at a 19:20 UTC entry, so an
"event night" here carries the post-event drift / press-conference move, not the print itself. For the print
itself an intraday entry on `date` (before time_utc) is needed; the live paper engine can do that later.
"""
from __future__ import annotations

import pathlib

import pandas as pd

from ..config import ROOT

PATH = ROOT / "data" / "events.csv"


def load(path: pathlib.Path | None = None, min_confidence: str = "tentative") -> pd.DataFrame:
    rank = {"confirmed": 2, "tentative": 1, "uncertain": 0}
    df = pd.read_csv(path or PATH, parse_dates=["date"])
    df["date"] = df.date.dt.date
    return df[df.confidence.map(rank) >= rank[min_confidence]].reset_index(drop=True)


def event_dates(kinds=("FOMC", "CPI"), path=None, min_confidence="tentative") -> set:
    df = load(path, min_confidence)
    return set(df[df.event.isin(kinds)].date)


def flag_nights(dates, kinds=("FOMC", "CPI"), shift_days: int = 0) -> pd.Series:
    """Boolean per entry date; shift_days=1 flags the night *before* the event (covers the print at 08:00+ UTC? no:
    Deribit expiry is 08:00 UTC, before US prints), so default 0 = entry on the event day."""
    ev = event_dates(kinds)
    d = pd.to_datetime(pd.Series(list(dates))).dt.date
    return pd.Series([(x + pd.Timedelta(days=shift_days)).date() in ev if hasattr(x, "date") else (pd.Timestamp(x) + pd.Timedelta(days=shift_days)).date() in ev for x in pd.to_datetime(d)], index=pd.Index(list(dates)))
