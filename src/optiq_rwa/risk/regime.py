"""Regime classifier ("국면 판별"): is implied vol rich, fair, or are event nights under-priced?

Project conclusion so far: returns come from the pricing regime, not product structure. This module
tells which of the four synthetic scenarios (see backtest.sweep.SCENARIOS) the market currently
looks like, and maps the answer to an action.

Pipeline
  1. night_features(chain_coin)  walk-forward features per night (only nights < n are used for night n).
  2. build_reference()           feature mean/sd per scenario from the synthetic generator -> results/regime_reference.csv
  3. RegimeClassifier            nearest centroid, diagonal Mahalanobis, softmax probabilities + rule-based fallback.
  4. classify_history(chain)     per (coin, night) features + labels.
  5. classify_live(con)          latest regime per base from the SQLite store (see its docstring for gaps).

Features (all known at entry of night n)
  ivrv        iv_atm(n) / trailing 20-night realised overnight vol (annualised, hours=12.7)
  pb_mid20/60 payoff-sum / mid-sum of the m~+1 call over trailing 20 / 60 nights
  pb_ask20/60 same at the ask
  itm_gap60   realised P(ITM) - mean model P(ITM) for the m~+1 call over trailing 60 nights
  iv_pct120   percentile of iv_atm(n) among trailing 120 nights
"""
from __future__ import annotations

import pathlib
import warnings

import numpy as np
import pandas as pd

from ..pricing import prob_itm

HOURS = 12.7
FEATURES = ["ivrv", "pb_mid20", "pb_ask20", "pb_mid60", "pb_ask60", "itm_gap60", "iv_pct120"]
MAX_DM = 0.35                      # nearest strike must satisfy |m - 1| <= MAX_DM
ACTIONS = {
    "rich_iv": "sell premium (idea 3, with wings)",
    "base": "hold RWA, buy only on events (idea 1 event_only)",
    "fair_iv": "hold RWA, buy only on events (idea 1 event_only)",
    "events_underpriced": "buy event calls (idea 2)",
}
REF_PATH = pathlib.Path(__file__).resolve().parents[3] / "results" / "regime_reference.csv"


# --------------------------------------------------------------------------- features
def _night_base(chain: pd.DataFrame, hours: float = HOURS, target_m: float = 1.0) -> pd.DataFrame:
    """One row per night: iv_atm, settle_rel and the (nearest) m~+1 call leg; NaN leg if none within MAX_DM."""
    c = chain[["night", "kind", "k_rel", "iv", "iv_atm", "mid", "ask", "settle_rel", "payoff"]].copy()
    nights = pd.Index(sorted(c.night.unique()), name="night")
    g = c.groupby("night")
    base = pd.DataFrame({"iv_atm": g.iv_atm.median(), "settle_rel": g.settle_rel.first()}).reindex(nights)
    iv_atm = c.night.map(base.iv_atm)
    c["m"] = np.log(c.k_rel) / (iv_atm * np.sqrt(hours / 8760.0))
    leg = c[(c.kind == "call") & ((c.m - target_m).abs() <= MAX_DM)].copy()
    leg["dm"] = (leg.m - target_m).abs()
    leg = leg.sort_values(["night", "dm"]).drop_duplicates("night").set_index("night")
    iv_k = leg.iv.where(leg.iv > 0, base.iv_atm.reindex(leg.index))
    leg["p_model"] = prob_itm(leg.k_rel, iv_k, hours, "call")
    leg["itm"] = (leg.payoff > 0).astype(float)
    for col in ("payoff", "mid", "ask", "p_model", "itm"):
        base[col] = leg[col].reindex(nights)
    return base


def _roll_ratio(num: pd.Series, den: pd.Series, w: int, minp: int) -> pd.Series:
    """Trailing ratio of sums over the previous w nights (current night excluded)."""
    valid = num.notna() & den.notna()
    n, d = num.where(valid).shift(1), den.where(valid).shift(1)
    cnt = valid.astype(float).shift(1).rolling(w, min_periods=1).sum()
    r = n.rolling(w, min_periods=minp).sum() / d.rolling(w, min_periods=minp).sum()
    return r.where(cnt >= minp)


def _trailing_pct(x: pd.Series, w: int, minp: int) -> pd.Series:
    """Percentile of x[t] among x[t-w .. t-1] (fraction of past values <= x[t])."""
    v = x.to_numpy(float)
    out = np.full(len(v), np.nan)
    for t in range(len(v)):
        past = v[max(0, t - w):t]
        past = past[~np.isnan(past)]
        if len(past) >= minp and not np.isnan(v[t]):
            out[t] = (past <= v[t]).mean()
    return pd.Series(out, index=x.index)


def night_features(chain: pd.DataFrame, hours: float = HOURS) -> pd.DataFrame:
    """Walk-forward features for ONE coin; index = night. Sparse nights give NaN features, never errors."""
    if chain.empty:
        return pd.DataFrame(columns=FEATURES)
    b = _night_base(chain, hours)
    lr = np.log(b.settle_rel)
    rv = lr.shift(1).rolling(20, min_periods=10).std() / np.sqrt(hours / 8760.0)
    f = pd.DataFrame(index=b.index)
    f["ivrv"] = b.iv_atm / rv
    for w in (20, 60):
        minp = 5 if w == 20 else 10
        f[f"pb_mid{w}"] = _roll_ratio(b.payoff, b.mid, w, minp)
        f[f"pb_ask{w}"] = _roll_ratio(b.payoff, b.ask, w, minp)
    gap = b.itm - b.p_model
    f["itm_gap60"] = gap.shift(1).rolling(60, min_periods=10).mean()
    f["iv_pct120"] = _trailing_pct(b.iv_atm, 120, 20)
    f.insert(0, "iv_atm", b.iv_atm)
    f.insert(1, "rv20", rv)
    return f


def features_by_coin(chain: pd.DataFrame, hours: float = HOURS) -> pd.DataFrame:
    """night_features for every coin in the chain, stacked with a `coin` column."""
    parts = []
    for coin, ch in chain.groupby("coin"):
        f = night_features(ch, hours)
        f.insert(0, "coin", coin)
        parts.append(f.reset_index())
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=["coin", "night"] + FEATURES)


# --------------------------------------------------------------------------- reference table
def build_reference(n_nights: int = 900, seeds=(0, 1, 2), warmup: int = 200, path=REF_PATH) -> pd.DataFrame:
    """Feature mean/sd per synthetic scenario on nights >= warmup (all coins and seeds pooled)."""
    from ..backtest.sweep import SCENARIOS
    from ..data.synthetic import MarketScenario, generate

    rows = []
    for name, (vrp, evm) in SCENARIOS.items():
        fs = []
        for seed in seeds:
            chain, *_ = generate(MarketScenario(n_nights=n_nights, vrp=vrp, event_iv_markup=evm, seed=seed))
            f = features_by_coin(chain)
            fs.append(f[f.night >= warmup])
        f = pd.concat(fs)
        for feat in FEATURES:
            rows.append(dict(scenario=name, feature=feat, mean=f[feat].mean(), sd=f[feat].std(), n=int(f[feat].notna().sum())))
    ref = pd.DataFrame(rows)
    if path is not None:
        pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
        ref.to_csv(path, index=False)
    return ref


def load_reference(path=REF_PATH) -> pd.DataFrame:
    p = pathlib.Path(path)
    return pd.read_csv(p) if p.exists() else build_reference(path=p)


# --------------------------------------------------------------------------- classifier
def rule_based(row) -> tuple[str, str]:
    """Explainable fallback: (label, reason) from IV/RV and payback thresholds. Uses what is available."""
    g = lambda k: row.get(k, np.nan)
    ivrv, pbm, pba = g("ivrv"), g("pb_mid60"), g("pb_ask60")
    if pd.isna(pbm):
        pbm, pba = g("pb_mid20"), g("pb_ask20")
    if pd.isna(ivrv) and pd.isna(pbm):
        return "unknown", "no usable IV/RV or payback history"
    if not pd.isna(ivrv) and ivrv >= 1.15 and (pd.isna(pbm) or pbm < 0.85):
        return "rich_iv", f"IV/RV {ivrv:.2f} >= 1.15 and payback_mid {pbm:.2f} < 0.85: options cost more than they pay back"
    if not pd.isna(ivrv) and ivrv < 1.0 and not pd.isna(pbm) and pbm >= 1.0:
        return "fair_iv", f"IV/RV {ivrv:.2f} < 1.0 and payback_mid {pbm:.2f} >= 1.0: IV not rich, buyer paid back"
    # events_underpriced cannot be told from base/fair_iv with these nightly features (needs event-night flags)
    return "base", f"IV/RV {ivrv:.2f}, payback_mid {pbm:.2f} within neutral band"


class RegimeClassifier:
    """Nearest centroid in feature space standardised by pooled within-scenario sd (diagonal Mahalanobis)."""

    def __init__(self, ref: pd.DataFrame | None = None, features=FEATURES, temp: float = 1.0):
        ref = load_reference() if ref is None else ref
        self.features = list(features)
        self.mu = ref.pivot(index="scenario", columns="feature", values="mean")[self.features]
        sd = ref.pivot(index="scenario", columns="feature", values="sd")[self.features]
        self.sd = np.sqrt((sd**2).mean()).replace(0, np.nan)
        self.labels = list(self.mu.index)
        self.temp = temp

    def distances(self, X: pd.DataFrame) -> np.ndarray:
        """[n_rows, n_labels] distance; NaN features are skipped and the sum rescaled to the full feature count."""
        x = X.reindex(columns=self.features).to_numpy(float)
        d = np.full((len(x), len(self.labels)), np.nan)
        for j, lab in enumerate(self.labels):
            z = (x - self.mu.loc[lab].to_numpy()) / self.sd.to_numpy()
            ok = ~np.isnan(z)
            k = ok.sum(1)
            with np.errstate(invalid="ignore", divide="ignore"):
                d[:, j] = np.sqrt(np.where(ok, z**2, 0).sum(1) * len(self.features) / k)
            d[k == 0, j] = np.nan
        return d

    def predict(self, X: pd.DataFrame) -> pd.DataFrame:
        """Label, p_<scenario> columns, action, and rule-based label + reason (both returned)."""
        d = self.distances(X)
        out = pd.DataFrame(index=X.index)
        with np.errstate(invalid="ignore"), warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            e = np.exp(-(d - np.nanmin(d, axis=1, keepdims=True)) / self.temp)
            p = e / e.sum(1, keepdims=True)
        bad = np.isnan(d).all(1)
        for j, lab in enumerate(self.labels):
            out[f"p_{lab}"] = p[:, j]
        idx = np.nanargmax(np.where(np.isnan(p), -1, p), axis=1)
        out["label"] = np.where(bad, "unknown", np.array(self.labels)[idx])
        out["action"] = out.label.map(ACTIONS).fillna("no action (insufficient history)")
        rb = [rule_based(r) for r in X.to_dict("records")]
        out["rule_label"] = [r[0] for r in rb]
        out["rule_reason"] = [r[1] for r in rb]
        return out


def classify_history(chain: pd.DataFrame, clf: RegimeClassifier | None = None) -> pd.DataFrame:
    """Per (coin, night): features + label + probs + action + rule-based label. Walk-forward (no look-ahead)."""
    clf = clf or RegimeClassifier()
    f = features_by_coin(chain)
    if f.empty:
        return f
    return pd.concat([f, clf.predict(f).reset_index(drop=True)], axis=1)


# --------------------------------------------------------------------------- live
_COIN_OF = {"BTC": "BTC", "ETH": "ETH", "SOL_USDC": "SOL", "SOL": "SOL"}


def _delivery_rv(con, base: str, window: int = 20) -> tuple[float, int]:
    """Annualised realised vol from daily 08:00-UTC delivery prices (24h returns, NOT the 12.7h overnight window)."""
    from ..data import live, store

    px = store.read(con, "SELECT date, price FROM delivery_price WHERE index_name=? ORDER BY date",
                    (live.index_name_of(base),)).price.to_numpy(float)
    r = np.diff(np.log(px))[-window:]
    if len(r) < 5:
        return np.nan, len(r)
    return float(r.std(ddof=1) * np.sqrt(8760.0 / 24.0)), len(r)


def classify_live(con, bases=("BTC", "ETH", "SOL_USDC"), raw_dir=None, clf: RegimeClassifier | None = None) -> pd.DataFrame:
    """Latest regime per base. NaN-safe: missing pieces become NaN features, never exceptions.

    Inputs: current ATM IV from live_chain (front expiry), realised vol from delivery_price history
    (daily returns; the overnight 19:20-08:00 window is not observable from deliveries, so this is a proxy),
    payback / gap / IV-percentile features from the last night of the real raw chain parquet (BTC, SOL only; ETH has none).
    Still missing while the live history is short: <120 nights of live ATM IV (iv_pct comes from the raw chain,
    stale by days), no live trade history for payback, and only 10 delivery prints per index so RV uses <=9 returns.
    """
    from ..config import SETTINGS
    from ..data import live

    clf = clf or RegimeClassifier()
    raw = pathlib.Path(raw_dir) if raw_dir else pathlib.Path(SETTINGS.db_path).parent / "raw"
    rows = []
    for base in bases:
        coin = _COIN_OF.get(base, base)
        row = dict(base=base, iv_atm_live=np.nan, rv_delivery=np.nan, n_rv=0, hist_nights=0, hist_last_night=np.nan)
        feats = {k: np.nan for k in FEATURES}
        try:
            ch = live.live_chain(con, base=base)
            if len(ch):
                row["iv_atm_live"] = float(ch.iv_atm.iloc[0])
                row["hours_to_expiry"] = float(ch.hours.iloc[0])
        except Exception as e:  # keep going: live quotes are optional
            row["note"] = f"live_chain failed: {e}"
        row["rv_delivery"], row["n_rv"] = _delivery_rv(con, base)
        feats["ivrv"] = row["iv_atm_live"] / row["rv_delivery"] if row["rv_delivery"] else np.nan
        p = raw / f"{coin.lower()}_chain.parquet"
        if p.exists():
            hist = night_features(pd.read_parquet(p).query("coin == @coin"))
            if len(hist):
                last = hist.iloc[-1]
                row["hist_nights"], row["hist_last_night"] = len(hist), hist.index[-1]
                for k in ("pb_mid20", "pb_ask20", "pb_mid60", "pb_ask60", "itm_gap60", "iv_pct120"):
                    feats[k] = last[k]
        X = pd.DataFrame([feats])
        pred = clf.predict(X).iloc[0].to_dict()
        rows.append({**row, **feats, **pred})
    return pd.DataFrame(rows)
