import numpy as np
import pandas as pd

from optiq_rwa.data.synthetic import MarketScenario, generate
from optiq_rwa.risk import regime


def _chain(vrp, evm, seed=11, n=500):
    return generate(MarketScenario(n_nights=n, vrp=vrp, event_iv_markup=evm, seed=seed))[0]


def test_rich_iv_classified_rich_oos():
    h = regime.classify_history(_chain(0.20, 1.8))
    oos = h[h.night >= 200]
    assert (oos.label == "rich_iv").mean() > 0.5


def test_fair_iv_not_rich():
    h = regime.classify_history(_chain(0.0, 1.6))
    oos = h[h.night >= 200]
    assert (oos.label != "rich_iv").mean() > 0.5


def test_no_lookahead():
    ch = _chain(0.05, 1.4, n=300)
    a = regime.night_features(ch[ch.coin == "BTC"])
    alt = ch.copy()
    late = alt.night >= 200
    rng = np.random.default_rng(0)
    alt.loc[late, "settle_rel"] = alt.loc[late, "settle_rel"] * np.exp(0.05 * rng.standard_normal(late.sum()))
    for c in ("payoff", "mid", "ask", "iv_atm"):
        alt.loc[late, c] = alt.loc[late, c] * 1.7
    b = regime.night_features(alt[alt.coin == "BTC"])
    # night 200 uses only nights < 200 for history-based features; iv_atm(200) is entry info and is changed
    hist_cols = ["rv20", "pb_mid20", "pb_ask20", "pb_mid60", "pb_ask60", "itm_gap60"]
    pd.testing.assert_frame_equal(a.loc[:200, hist_cols], b.loc[:200, hist_cols])
    assert not np.allclose(a.loc[250:, "rv20"], b.loc[250:, "rv20"])


def test_sparse_chain_nan_no_raise():
    ch = _chain(0.05, 1.4, n=40)
    sp = ch[(ch.coin == "BTC") & (ch.m == -2.0)]          # no m~+1 call anywhere
    f = regime.night_features(sp)
    assert f[["pb_mid20", "pb_ask60", "itm_gap60"]].isna().all().all()
    out = regime.classify_history(sp.assign(coin="BTC"))
    assert len(out) == sp.night.nunique() and "label" in out
    assert regime.night_features(sp.iloc[0:0]).empty
