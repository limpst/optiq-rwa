"""Idea 4 — probability calibration and payback per dollar.

Answers, per bucket (coin x kind x moneyness x event):
  * model P(ITM) and P(clear breakeven) vs. what actually happened
  * payback per $1 premium at mid and at the ask (buyer) and at the bid (seller)
and turns that into a shrunk out-of-sample edge estimate for the optimiser.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..pricing import prob_itm

KEYS = ["coin", "kind", "m", "event"]


def add_model_probs(chain: pd.DataFrame, hours: float = 12.7) -> pd.DataFrame:
    c = chain.copy()
    c["p_itm_model"] = np.where(c.kind == "call", prob_itm(c.k_rel, c.iv, hours, "call"),
                                prob_itm(c.k_rel, c.iv, hours, "put"))
    be = np.where(c.kind == "call", c.k_rel + c.ask, c.k_rel - c.ask)
    c["p_be_model"] = np.where(c.kind == "call", prob_itm(be, c.iv, hours, "call"),
                               prob_itm(np.maximum(be, 1e-9), c.iv, hours, "put"))
    c["itm"] = c.payoff > 0
    c["beat_be"] = c.payoff > c.ask
    return c


def calibration_table(chain: pd.DataFrame, keys=KEYS, hours: float = 12.7) -> pd.DataFrame:
    c = add_model_probs(chain, hours)
    g = c.groupby(keys, observed=True)
    t = pd.DataFrame({
        "n": g.size(),
        "p_itm_model": g.p_itm_model.mean(), "p_itm_emp": g.itm.mean(),
        "p_be_model": g.p_be_model.mean(), "p_be_emp": g.beat_be.mean(),
        "payback_mid": g.payoff.sum() / g.mid.sum(),
        "payback_ask": g.payoff.sum() / g.ask.sum(),
        "seller_keep_bid": 1 - g.payoff.sum() / g.bid.sum().replace(0, np.nan),
        "spread_share": ((g.ask.sum() - g.bid.sum()) / (2 * g.mid.sum())),
    })
    t["itm_gap"] = t.p_itm_emp - t.p_itm_model
    return t.reset_index()


def edge_model(train: pd.DataFrame, prior_n: float = 60.0) -> pd.DataFrame:
    """Shrunk buyer edge (payback_ask - 1) and seller edge per bucket.

    Bucket estimate is shrunk toward the pooled (kind, m, event) estimate with
    weight n / (n + prior_n), so thin buckets do not drive the optimiser.
    """
    fine = calibration_table(train, KEYS)
    pooled = calibration_table(train, ["kind", "m", "event"])
    t = fine.merge(pooled[["kind", "m", "event", "payback_ask", "seller_keep_bid"]],
                   on=["kind", "m", "event"], suffixes=("", "_pool"))
    w = t.n / (t.n + prior_n)
    t["buy_edge"] = w * (t.payback_ask - 1) + (1 - w) * (t.payback_ask_pool - 1)
    t["sell_edge"] = (w * t.seller_keep_bid.fillna(0) + (1 - w) * t.seller_keep_bid_pool.fillna(0))
    return t[KEYS + ["n", "buy_edge", "sell_edge"]]
