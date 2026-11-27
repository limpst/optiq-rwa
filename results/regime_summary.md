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
| BTC    | 2026-11 |   0    |                 0    |      0    |      1    |      0    |       25 |
| ETH    | 2026-11 |   0    |                 0    |      0    |      0.29 |      0.71 |        7 |
| SOL    | 2026-05 |   0    |                 0    |      0.08 |      0.15 |      0.77 |       13 |
| SOL    | 2026-06 |   0    |                 0.24 |      0.43 |      0.33 |      0    |       21 |
| SOL    | 2026-07 |   0    |                 0.75 |      0.08 |      0.17 |      0    |       12 |
| SOL    | 2026-08 |   0    |                 0.3  |      0    |      0.7  |      0    |       10 |
| SOL    | 2026-09 |   0    |                 0    |      0    |      1    |      0    |       17 |
| SOL    | 2026-10 |   0    |                 0    |      0    |      1    |      0    |       21 |
| SOL    | 2026-11 |   0    |                 0    |      0    |      1    |      0    |       19 |

## Latest label

- BTC 2026-11-26: rich_iv ({'base': np.float64(0.16), 'events_underpriced': np.float64(0.16), 'fair_iv': np.float64(0.13), 'rich_iv': np.float64(0.55)}); rule-based: base - IV/RV 0.96, payback_mid 0.34 within neutral band

- ETH 2026-11-26: rich_iv ({'base': np.float64(0.16), 'events_underpriced': np.float64(0.16), 'fair_iv': np.float64(0.14), 'rich_iv': np.float64(0.54)}); rule-based: base - IV/RV nan, payback_mid 0.00 within neutral band

- SOL 2026-11-26: rich_iv ({'base': np.float64(0.15), 'events_underpriced': np.float64(0.15), 'fair_iv': np.float64(0.12), 'rich_iv': np.float64(0.57)}); rule-based: rich_iv - IV/RV 1.27 >= 1.15 and payback_mid 0.51 < 0.85: options cost more than they pay back

## Interpretation

- BTC: label share over 201 classified nights {'rich_iv': 0.54, 'fair_iv': 0.28, 'base': 0.14, 'events_underpriced': 0.03}; latest rich_iv. Why: IV/RV 0.96, payback_mid60 0.34, P(ITM) gap -0.075 (realised minus model). So what: sell premium (idea 3, with wings). Real chains are sparse (BTC ~7, SOL ~2.6 quotes/night), so payback features are noisy; treat label as a tilt, not a signal.
- ETH: label share over 2 classified nights {'rich_iv': 1.0}; latest rich_iv. Why: IV/RV nan, payback_mid60 nan, P(ITM) gap +nan (realised minus model). So what: sell premium (idea 3, with wings). Real chains are sparse (BTC ~7, SOL ~2.6 quotes/night), so payback features are noisy; treat label as a tilt, not a signal.
- SOL: label share over 103 classified nights {'rich_iv': 0.73, 'events_underpriced': 0.17, 'fair_iv': 0.11}; latest rich_iv. Why: IV/RV 1.27, payback_mid60 0.51, P(ITM) gap -0.074 (realised minus model). So what: sell premium (idea 3, with wings). Real chains are sparse (BTC ~7, SOL ~2.6 quotes/night), so payback features are noisy; treat label as a tilt, not a signal.

Limitation: base, fair_iv and events_underpriced are nearly indistinguishable on these features (only rich_iv separates); distinguishing them needs event-night flags and IV mark-up on events.
