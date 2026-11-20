# Regime validation (real chains, base TC)

Long overlay = m≈+1 call at ask (incl. fee), return per $ premium = payback − 1. Short overlay = m≈±1.5 strangle at bid (incl. fee), P&L per $ notional per leg. Labels are walk-forward (features use earlier nights only). regime_follow: rich_iv → sell strangle (frac 0.5), else buy calls with 3× accrual on event nights only.


## BTC: 202 nights, labels {'rich_iv': 101, 'fair_iv': 57, 'base': 29, 'unknown': 8, 'events_underpriced': 7}

| coin   | label              |   nights |   long_n |   long_mean |   long_hit |   short_n |   short_mean |   short_worst |   short_hit |
|:-------|:-------------------|---------:|---------:|------------:|-----------:|----------:|-------------:|--------------:|------------:|
| BTC    | base               |       29 |       13 |     -0.3132 |     0.069  |         9 |       0.0005 |        0.0002 |      0.3103 |
| BTC    | events_underpriced |        7 |        3 |     -1      |     0      |         5 |       0.0004 |        0.0001 |      0.7143 |
| BTC    | fair_iv            |       57 |       33 |     -0.3903 |     0.0526 |        18 |       0.0004 |       -0.0012 |      0.2807 |
| BTC    | rich_iv            |      101 |       73 |     -0.5331 |     0.0693 |        49 |       0.0001 |       -0.0103 |      0.4455 |
| BTC    | unknown            |        8 |        5 |     -1      |     0      |         4 |       0.0003 |        0.0002 |      0.5    |

### BTC NAV paths (SR · IR · MDD · DSR; bold = highlight rule)

| strategy          |   n_nights |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |   worst_night |      dsr |
|:------------------|-----------:|-------------:|----------------:|---------:|------------:|---------------:|--------------:|---------:|
| rwa_only          |        202 |       0.046  |          0.001  | nan      |    nan      |         0      |        0.0001 | nan      |
| always_long_daily |        202 |       0.0312 |         -0.0138 |   8.167  |     -3.7763 |         0      |        0      |   0.0016 |
| always_short      |        202 |       0.0552 |          0.0102 |   9.9978 |      1.634  |        -0.0025 |       -0.0025 |   0.2352 |
| regime_follow     |        202 |       0.0457 |          0.0007 |   8.3733 |     -0.0517 |        -0.0025 |       -0.0025 |   0.0132 |

- BTC: short strangle mean P&L per $ notional was +0.0001 on rich_iv nights (n=49) vs +0.0004 on other labelled nights (n=32). Long m=1 call return per $ was -0.533 on rich_iv vs -0.407 elsewhere. Label does not separate the sell edge.

## SOL: 105 nights, labels {'rich_iv': 69, 'events_underpriced': 16, 'fair_iv': 11, 'unknown': 9}

| coin   | label              |   nights |   long_n |   long_mean |   long_hit |   short_n |   short_mean |   short_worst |   short_hit |
|:-------|:-------------------|---------:|---------:|------------:|-----------:|----------:|-------------:|--------------:|------------:|
| SOL    | events_underpriced |       16 |        4 |     -1      |     0      |         0 |     nan      |      nan      |      0      |
| SOL    | fair_iv            |       11 |        3 |     -1      |     0      |         0 |     nan      |      nan      |      0      |
| SOL    | rich_iv            |       69 |       23 |     -0.2943 |     0.0435 |         5 |       0.0019 |        0.0013 |      0.0725 |
| SOL    | unknown            |        9 |        2 |     -1      |     0      |         0 |     nan      |      nan      |      0      |

### SOL NAV paths (SR · IR · MDD · DSR; bold = highlight rule)

| strategy          |   n_nights |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |   worst_night |      dsr |
|:------------------|-----------:|-------------:|----------------:|---------:|------------:|---------------:|--------------:|---------:|
| rwa_only          |        105 |       0.046  |          0.001  | nan      |    nan      |         0      |        0.0001 | nan      |
| always_long_daily |        105 |       0.039  |         -0.006  |  16.7297 |     -2.9565 |         0      |        0      |   0.0032 |
| always_short      |        105 |       0.0548 |          0.0098 |  25.8179 |      4.0614 |         0      |        0.0001 |   0.5102 |
| regime_follow     |        105 |       0.0535 |          0.0085 |  23.754  |      3.2429 |        -0.0002 |       -0.0002 |   0.2771 |

- SOL: short strangle mean P&L per $ notional was +0.0019 on rich_iv nights (n=5) vs +nan on other labelled nights (n=0). Long m=1 call return per $ was -0.294 on rich_iv vs -1.000 elsewhere. Label does not separate the sell edge.