# Regime validation (real chains, base TC)

Long overlay = m≈+1 call at ask (incl. fee), return per $ premium = payback − 1. Short overlay = m≈±1.5 strangle at bid (incl. fee), P&L per $ notional per leg. Labels are walk-forward (features use earlier nights only). regime_follow: rich_iv → sell strangle (frac 0.5), else buy calls with 3× accrual on event nights only.


## BTC: 206 nights, labels {'rich_iv': 105, 'fair_iv': 57, 'base': 29, 'unknown': 8, 'events_underpriced': 7}

| coin   | label              |   nights |   long_n |   long_mean |   long_hit |   short_n |   short_mean |   short_worst |   short_hit |
|:-------|:-------------------|---------:|---------:|------------:|-----------:|----------:|-------------:|--------------:|------------:|
| BTC    | base               |       29 |       13 |     -0.3132 |     0.069  |         9 |       0.0005 |        0.0002 |      0.3103 |
| BTC    | events_underpriced |        7 |        3 |     -1      |     0      |         5 |       0.0004 |        0.0001 |      0.7143 |
| BTC    | fair_iv            |       57 |       33 |     -0.3903 |     0.0526 |        18 |       0.0004 |       -0.0012 |      0.2807 |
| BTC    | rich_iv            |      105 |       77 |     -0.5574 |     0.0667 |        53 |       0.0002 |       -0.0103 |      0.4667 |
| BTC    | unknown            |        8 |        5 |     -1      |     0      |         4 |       0.0003 |        0.0002 |      0.5    |

### BTC NAV paths (SR · IR · MDD · DSR; bold = highlight rule)

| strategy          |   n_nights |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |   worst_night |      dsr |
|:------------------|-----------:|-------------:|----------------:|---------:|------------:|---------------:|--------------:|---------:|
| rwa_only          |        206 |       0.046  |          0.001  | nan      |    nan      |         0      |        0.0001 | nan      |
| always_long_daily |        206 |       0.0306 |         -0.0144 |   8.0733 |     -3.9668 |         0      |        0      |   0.0007 |
| always_short      |        206 |       0.0587 |          0.0137 |  10.3928 |      2.1926 |        -0.0025 |       -0.0025 |   0.2654 |
| regime_follow     |        206 |       0.0493 |          0.0043 |   8.8088 |      0.5746 |        -0.0025 |       -0.0025 |   0.0287 |

- BTC: short strangle mean P&L per $ notional was +0.0002 on rich_iv nights (n=53) vs +0.0004 on other labelled nights (n=32). Long m=1 call return per $ was -0.557 on rich_iv vs -0.407 elsewhere. Label does not separate the sell edge.

## ETH: 4 nights, labels {'unknown': 4}

| coin   | label   |   nights |   long_n |   long_mean |   long_hit |   short_n |   short_mean |   short_worst |   short_hit |
|:-------|:--------|---------:|---------:|------------:|-----------:|----------:|-------------:|--------------:|------------:|
| ETH    | unknown |        4 |        4 |          -1 |          0 |         4 |       0.0026 |        0.0021 |           1 |

### ETH NAV paths (SR · IR · MDD · DSR; bold = highlight rule)

| strategy          |   n_nights |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |   worst_night |      dsr |
|:------------------|-----------:|-------------:|----------------:|---------:|------------:|---------------:|--------------:|---------:|
| rwa_only          |          4 |       0.046  |          0.001  |  nan     |     nan     |              0 |        0.0001 | nan      |
| always_long_daily |          4 |       0      |         -0.045  |  nan     |     nan     |              0 |        0      | nan      |
| always_short      |          4 |       0.3249 |          0.2799 |  176.684 |     148.432 |              0 |        0.0006 |   0.9949 |
| regime_follow     |          4 |       0.046  |          0.001  |  nan     |     nan     |              0 |        0.0001 | nan      |

- ETH: short strangle mean P&L per $ notional was +nan on rich_iv nights (n=0) vs +nan on other labelled nights (n=0). Long m=1 call return per $ was +nan on rich_iv vs +nan elsewhere. Label does not separate the sell edge.

## SOL: 108 nights, labels {'rich_iv': 72, 'events_underpriced': 16, 'fair_iv': 11, 'unknown': 9}

| coin   | label              |   nights |   long_n |   long_mean |   long_hit |   short_n |   short_mean |   short_worst |   short_hit |
|:-------|:-------------------|---------:|---------:|------------:|-----------:|----------:|-------------:|--------------:|------------:|
| SOL    | events_underpriced |       16 |        4 |     -1      |     0      |         0 |     nan      |      nan      |      0      |
| SOL    | fair_iv            |       11 |        3 |     -1      |     0      |         0 |     nan      |      nan      |      0      |
| SOL    | rich_iv            |       72 |       26 |     -0.3757 |     0.0417 |         7 |       0.0019 |        0.0013 |      0.0972 |
| SOL    | unknown            |        9 |        2 |     -1      |     0      |         0 |     nan      |      nan      |      0      |

### SOL NAV paths (SR · IR · MDD · DSR; bold = highlight rule)

| strategy          |   n_nights |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |   worst_night |      dsr |
|:------------------|-----------:|-------------:|----------------:|---------:|------------:|---------------:|--------------:|---------:|
| rwa_only          |        108 |       0.046  |          0.001  | nan      |    nan      |         0      |        0.0001 | nan      |
| always_long_daily |        108 |       0.0379 |         -0.0071 |  16.3233 |     -3.4335 |         0      |        0      |   0.0009 |
| always_short      |        108 |       0.0579 |          0.0129 |  24.1462 |      4.8339 |         0      |        0.0001 |   0.5083 |
| regime_follow     |        108 |       0.0565 |          0.0115 |  22.5162 |      4.0984 |        -0.0002 |       -0.0002 |   0.288  |

- SOL: short strangle mean P&L per $ notional was +0.0019 on rich_iv nights (n=7) vs +nan on other labelled nights (n=0). Long m=1 call return per $ was -0.376 on rich_iv vs -1.000 elsewhere. Label does not separate the sell edge.