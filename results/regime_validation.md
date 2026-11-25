# Regime validation (real chains, base TC)

Long overlay = m≈+1 call at ask (incl. fee), return per $ premium = payback − 1. Short overlay = m≈±1.5 strangle at bid (incl. fee), P&L per $ notional per leg. Labels are walk-forward (features use earlier nights only). regime_follow: rich_iv → sell strangle (frac 0.5), else buy calls with 3× accrual on event nights only.


## BTC: 207 nights, labels {'rich_iv': 106, 'fair_iv': 57, 'base': 29, 'unknown': 8, 'events_underpriced': 7}

| coin   | label              |   nights |   long_n |   long_mean |   long_hit |   short_n |   short_mean |   short_worst |   short_hit |
|:-------|:-------------------|---------:|---------:|------------:|-----------:|----------:|-------------:|--------------:|------------:|
| BTC    | base               |       29 |       13 |     -0.3132 |     0.069  |         9 |       0.0005 |        0.0002 |      0.3103 |
| BTC    | events_underpriced |        7 |        3 |     -1      |     0      |         5 |       0.0004 |        0.0001 |      0.7143 |
| BTC    | fair_iv            |       57 |       33 |     -0.3903 |     0.0526 |        18 |       0.0004 |       -0.0012 |      0.2807 |
| BTC    | rich_iv            |      106 |       78 |     -0.5631 |     0.066  |        54 |       0.0002 |       -0.0103 |      0.4717 |
| BTC    | unknown            |        8 |        5 |     -1      |     0      |         4 |       0.0003 |        0.0002 |      0.5    |

### BTC NAV paths (SR · IR · MDD · DSR; bold = highlight rule)

| strategy          |   n_nights |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |   worst_night |      dsr |
|:------------------|-----------:|-------------:|----------------:|---------:|------------:|---------------:|--------------:|---------:|
| rwa_only          |        207 |       0.046  |          0.001  | nan      |    nan      |         0      |        0.0001 | nan      |
| always_long_daily |        207 |       0.0305 |         -0.0145 |   8.0504 |     -4.0138 |         0      |        0      |   0.0006 |
| always_short      |        207 |       0.0593 |          0.0143 |  10.4919 |      2.2994 |        -0.0025 |       -0.0025 |   0.2701 |
| regime_follow     |        207 |       0.05   |          0.005  |   8.913  |      0.6908 |        -0.0025 |       -0.0025 |   0.0318 |

- BTC: short strangle mean P&L per $ notional was +0.0002 on rich_iv nights (n=54) vs +0.0004 on other labelled nights (n=32). Long m=1 call return per $ was -0.563 on rich_iv vs -0.407 elsewhere. Label does not separate the sell edge.

## ETH: 5 nights, labels {'unknown': 5}

| coin   | label   |   nights |   long_n |   long_mean |   long_hit |   short_n |   short_mean |   short_worst |   short_hit |
|:-------|:--------|---------:|---------:|------------:|-----------:|----------:|-------------:|--------------:|------------:|
| ETH    | unknown |        5 |        5 |          -1 |          0 |         5 |       0.0024 |        0.0018 |           1 |

### ETH NAV paths (SR · IR · MDD · DSR; bold = highlight rule)

| strategy          |   n_nights |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |   worst_night |   dsr |
|:------------------|-----------:|-------------:|----------------:|---------:|------------:|---------------:|--------------:|------:|
| rwa_only          |          5 |       0.046  |          0.001  |  nan     |     nan     |              0 |        0.0001 |   nan |
| always_long_daily |          5 |       0      |         -0.045  |  nan     |     nan     |              0 |        0      |   nan |
| always_short      |          5 |       0.3068 |          0.2618 |  126.307 |     105.073 |              0 |        0.0006 |     1 |
| regime_follow     |          5 |       0.046  |          0.001  |  nan     |     nan     |              0 |        0.0001 |   nan |

- ETH: short strangle mean P&L per $ notional was +nan on rich_iv nights (n=0) vs +nan on other labelled nights (n=0). Long m=1 call return per $ was +nan on rich_iv vs +nan elsewhere. Label does not separate the sell edge.

## SOL: 109 nights, labels {'rich_iv': 73, 'events_underpriced': 16, 'fair_iv': 11, 'unknown': 9}

| coin   | label              |   nights |   long_n |   long_mean |   long_hit |   short_n |   short_mean |   short_worst |   short_hit |
|:-------|:-------------------|---------:|---------:|------------:|-----------:|----------:|-------------:|--------------:|------------:|
| SOL    | events_underpriced |       16 |        4 |     -1      |     0      |         0 |     nan      |      nan      |      0      |
| SOL    | fair_iv            |       11 |        3 |     -1      |     0      |         0 |     nan      |      nan      |      0      |
| SOL    | rich_iv            |       73 |       27 |     -0.3989 |     0.0411 |         8 |       0.0019 |        0.0013 |      0.1096 |
| SOL    | unknown            |        9 |        2 |     -1      |     0      |         0 |     nan      |      nan      |      0      |

### SOL NAV paths (SR · IR · MDD · DSR; bold = highlight rule)

| strategy          |   n_nights |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |   worst_night |      dsr |
|:------------------|-----------:|-------------:|----------------:|---------:|------------:|---------------:|--------------:|---------:|
| rwa_only          |        109 |       0.046  |          0.001  | nan      |    nan      |         0      |        0.0001 | nan      |
| always_long_daily |        109 |       0.0375 |         -0.0075 |  16.1943 |     -3.5878 |         0      |        0      |   0.0005 |
| always_short      |        109 |       0.0597 |          0.0147 |  23.2116 |      5.1889 |         0      |        0.0001 |   0.5224 |
| regime_follow     |        109 |       0.0583 |          0.0133 |  21.7804 |      4.4996 |        -0.0002 |       -0.0002 |   0.306  |

- SOL: short strangle mean P&L per $ notional was +0.0019 on rich_iv nights (n=8) vs +nan on other labelled nights (n=0). Long m=1 call return per $ was -0.399 on rich_iv vs -1.000 elsewhere. Label does not separate the sell edge.