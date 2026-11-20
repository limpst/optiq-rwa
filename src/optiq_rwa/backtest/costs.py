"""Transaction-cost model for Deribit options (relative units: prices as fraction of spot).

Fee schedule used (secondary sources, 2026-11-20; see README "거래비용"):
  trading fee   0.03% of underlying notional per contract, for maker and taker alike,
                capped at 12.5% of the option price          -> fee_rel = min(0.0003, 0.125 * price_rel)
  settlement    0.015% of underlying, capped at 12.5% of option value, charged on ITM settlement;
                daily options are reported exempt            -> settle_daily_exempt=True by default (0 for 0DTE)
  spread        already paid by filling at ask (buy) / bid (sell); `spread_mult` widens the half-spread
                around mid for stress runs (2.0 = double the modelled spread of the historical chains)
  slippage      historical chains carry no depth -> `slip_rel` adds a fixed fraction of the half-spread;
                the live paper engine walks the order-book levels instead (paper.engine)

`with_costs(chain, cm)` adds columns: ask_c, bid_c (fill prices incl. fee), payoff_long_c, payoff_short_c
(settlement cash flows incl. settlement fee). Strategies pick the *_c columns when `costs=True`.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class CostModel:
    fee_rel: float = 0.0003          # 0.03% of underlying per contract
    fee_cap: float = 0.125           # cap: fraction of option price
    settle_rel: float = 0.00015      # 0.015% of underlying on ITM settlement
    settle_cap: float = 0.125
    settle_daily_exempt: bool = True # daily (0DTE) options: no settlement fee
    spread_mult: float = 1.0         # 1.0 = modelled/observed spread, 2.0 = stress
    slip_rel: float = 0.0            # extra slippage as a fraction of the half-spread (historical chains)
    name: str = "deribit_base"

    def fee(self, price_rel):
        return np.minimum(self.fee_rel, self.fee_cap * np.asarray(price_rel, float))

    def settle_fee(self, payoff_rel):
        if self.settle_daily_exempt:
            return np.zeros_like(np.asarray(payoff_rel, float))
        return np.where(np.asarray(payoff_rel) > 0, np.minimum(self.settle_rel, self.settle_cap * np.asarray(payoff_rel, float)), 0.0)

    def to_dict(self):
        return asdict(self)


NO_COST = CostModel(fee_rel=0.0, settle_rel=0.0, name="none")
BASE = CostModel()
STRESS = CostModel(spread_mult=2.0, slip_rel=0.5, settle_daily_exempt=False, name="stress")
MODELS = {"none": NO_COST, "base": BASE, "stress": STRESS}


def with_costs(chain: pd.DataFrame, cm: CostModel = BASE) -> pd.DataFrame:
    """Return a copy of `chain` with cost-adjusted fill and settlement columns (relative to spot)."""
    out = chain.copy()
    mid = out["mid"].values if "mid" in out else (out.ask.values + out.bid.values) / 2
    half = np.maximum((out.ask.values - out.bid.values) / 2, 0.0) * cm.spread_mult
    slip = cm.slip_rel * half
    ask = np.maximum(mid + half + slip, 0.0)
    bid = np.maximum(mid - half - slip, 0.0)
    out["ask_c"] = ask + cm.fee(ask)
    out["bid_c"] = np.maximum(bid - cm.fee(bid), 0.0)
    pay = out.payoff.values
    out["payoff_long_c"] = pay - cm.settle_fee(pay)
    out["payoff_short_c"] = pay + cm.settle_fee(pay)
    out["cost_model"] = cm.name
    return out


def cost_summary(chain_c: pd.DataFrame) -> dict:
    """Average round-trip cost per $1 of premium (buyer) for the chain: fee + spread + slippage."""
    buy = chain_c[chain_c.ask > 0]
    return {"fee_per_premium": float((buy.ask_c - buy.ask).sum() / buy.ask.sum()) if len(buy) else np.nan,
            "spread_pct_of_mid": float(((buy.ask - buy.bid) / buy.mid.replace(0, np.nan)).mean()) if len(buy) else np.nan}
