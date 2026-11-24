# Regime classification (real Deribit chains)

Nearest-centroid on walk-forward features (IV/RV, trailing payback, P(ITM) gap, IV percentile); reference = synthetic scenarios (results/regime_reference.csv). Label share per month:

| coin   | month   |   base |   events_underpriced |   fair_iv |   rich_iv |   unknown |   nights |
|:-------|:--------|-------:|---------------------:|----------:|----------:|----------:|---------:|
| BTC    | 2026-05 |   0    |                 0    |      0    |      0.74 |      0.26 |       31 |
| BTC    | 2026-06 |   0.07 |                 0    |      0    |      0.93 |      0    |       30 |
| BTC    | 2026-07 |   0.45 |                 0    |      0    |      0.55 |      0    |       31 |
| BTC    | 2026-08 |   0.1  |                 0    |      0.84 |      0.06 |      0    |       31 |
| BTC    | 2026-09 |   0.07 |                 0.17 |      0.73 |      0.03 |      0    |       30 |
| BTC    | 2026-10 |   0.26 |                 0.06 |      0.29 |      0.39 |      0    |       31 |
| BTC    | 2026-11 |   0    |                 0    |      0    |      1    |      0    |       22 |
| ETH    | 2026-11 |   0    |                 0    |      0    |      0    |      1    |        4 |
| SOL    | 2026-05 |   0    |                 0    |      0.08 |      0.15 |      0.77 |       13 |
| SOL    | 2026-06 |   0    |                 0.24 |      0.43 |      0.33 |      0    |       21 |
| SOL    | 2026-07 |   0    |                 0.75 |      0.08 |      0.17 |      0    |       12 |
| SOL    | 2026-08 |   0    |                 0.3  |      0    |      0.7  |      0    |       10 |
| SOL    | 2026-09 |   0    |                 0    |      0    |      1    |      0    |       17 |
| SOL    | 2026-10 |   0    |                 0    |      0    |      1    |      0    |       21 |
| SOL    | 2026-11 |   0    |                 0    |      0    |      1    |      0    |       16 |

## Latest label

- BTC 2026-11-23: rich_iv ({'base': np.float64(0.16), 'events_underpriced': np.float64(0.16), 'fair_iv': np.float64(0.13), 'rich_iv': np.float64(0.55)}); rule-based: rich_iv - IV/RV 1.40 >= 1.15 and payback_mid 0.36 < 0.85: options cost more than they pay back

- ETH 2026-11-23: unknown ({'base': np.float64(nan), 'events_underpriced': np.float64(nan), 'fair_iv': np.float64(nan), 'rich_iv': np.float64(nan)}); rule-based: unknown - no usable IV/RV or payback history

- SOL 2026-11-23: rich_iv ({'base': np.float64(0.17), 'events_underpriced': np.float64(0.18), 'fair_iv': np.float64(0.15), 'rich_iv': np.float64(0.5)}); rule-based: rich_iv - IV/RV 1.40 >= 1.15 and payback_mid 0.57 < 0.85: options cost more than they pay back

## Interpretation

- BTC: label share over 198 classified nights {'rich_iv': 0.53, 'fair_iv': 0.29, 'base': 0.15, 'events_underpriced': 0.04}; latest rich_iv. Why: IV/RV 1.40, payback_mid60 0.36, P(ITM) gap -0.075 (realised minus model). So what: sell premium (idea 3, with wings). Real chains are sparse (BTC ~7, SOL ~2.6 quotes/night), so payback features are noisy; treat label as a tilt, not a signal.
- ETH: label share over 0 classified nights {}; latest unknown. Why: IV/RV nan, payback_mid60 nan, P(ITM) gap +nan (realised minus model). So what: no action (insufficient history). Real chains are sparse (BTC ~7, SOL ~2.6 quotes/night), so payback features are noisy; treat label as a tilt, not a signal.
- SOL: label share over 100 classified nights {'rich_iv': 0.72, 'events_underpriced': 0.17, 'fair_iv': 0.11}; latest rich_iv. Why: IV/RV 1.40, payback_mid60 0.57, P(ITM) gap -0.063 (realised minus model). So what: sell premium (idea 3, with wings). Real chains are sparse (BTC ~7, SOL ~2.6 quotes/night), so payback features are noisy; treat label as a tilt, not a signal.

Limitation: base, fair_iv and events_underpriced are nearly indistinguishable on these features (only rich_iv separates); distinguishing them needs event-night flags and IV mark-up on events.
