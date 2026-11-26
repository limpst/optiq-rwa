# Regime validation (real chains, base TC)

Long overlay = m≈+1 call at ask (incl. fee), return per $ premium = payback − 1. Short overlay = m≈±1.5 strangle at bid (incl. fee), P&L per $ notional per leg. Labels are walk-forward (features use earlier nights only). regime_follow: rich_iv → sell strangle (frac 0.5), else buy calls with 3× accrual on event nights only.


## BTC: 208 nights, labels {'rich_iv': 107, 'fair_iv': 57, 'base': 29, 'unknown': 8, 'events_underpriced': 7}

| coin   | label              |   nights |   long_n |   long_mean |   long_hit |   short_n |   short_mean |   short_worst |   short_hit |
|:-------|:-------------------|---------:|---------:|------------:|-----------:|----------:|-------------:|--------------:|------------:|
| BTC    | base               |       29 |       13 |     -0.3132 |     0.069  |         9 |       0.0005 |        0.0002 |      0.3103 |
| BTC    | events_underpriced |        7 |        3 |     -1      |     0      |         5 |       0.0004 |        0.0001 |      0.7143 |
| BTC    | fair_iv            |       57 |       33 |     -0.3903 |     0.0526 |        18 |       0.0004 |       -0.0012 |      0.2807 |
| BTC    | rich_iv            |      107 |       79 |     -0.5686 |     0.0654 |        55 |       0.0003 |       -0.0103 |      0.4766 |
| BTC    | unknown            |        8 |        5 |     -1      |     0      |         4 |       0.0003 |        0.0002 |      0.5    |

### BTC NAV paths (SR · IR · MDD · DSR; bold = highlight rule)

| strategy          |   n_nights |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |   worst_night |      dsr |
|:------------------|-----------:|-------------:|----------------:|---------:|------------:|---------------:|--------------:|---------:|
| rwa_only          |        208 |       0.046  |          0.001  | nan      |    nan      |         0      |        0.0001 | nan      |
| always_long_daily |        208 |       0.0303 |         -0.0147 |   8.0277 |     -4.0606 |         0      |        0      |   0.0005 |
| always_short      |        208 |       0.0598 |          0.0148 |  10.5781 |      2.3806 |        -0.0025 |       -0.0025 |   0.2725 |
| regime_follow     |        208 |       0.0505 |          0.0055 |   9.0028 |      0.7789 |        -0.0025 |       -0.0025 |   0.0338 |

- BTC: short strangle mean P&L per $ notional was +0.0003 on rich_iv nights (n=55) vs +0.0004 on other labelled nights (n=32). Long m=1 call return per $ was -0.569 on rich_iv vs -0.407 elsewhere. Label does not separate the sell edge.

## ETH: 6 nights, labels {'unknown': 5, 'rich_iv': 1}

| coin   | label   |   nights |   long_n |   long_mean |   long_hit |   short_n |   short_mean |   short_worst |   short_hit |
|:-------|:--------|---------:|---------:|------------:|-----------:|----------:|-------------:|--------------:|------------:|
| ETH    | rich_iv |        1 |        1 |          -1 |          0 |         1 |       0.0018 |        0.0018 |           1 |
| ETH    | unknown |        5 |        5 |          -1 |          0 |         5 |       0.0024 |        0.0018 |           1 |

### ETH NAV paths (SR · IR · MDD · DSR; bold = highlight rule)

| strategy          |   n_nights |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |   worst_night |      dsr |
|:------------------|-----------:|-------------:|----------------:|---------:|------------:|---------------:|--------------:|---------:|
| rwa_only          |          6 |       0.046  |          0.001  | nan      |    nan      |              0 |        0.0001 | nan      |
| always_long_daily |          6 |       0      |         -0.045  | nan      |    nan      |              0 |        0      | nan      |
| always_short      |          6 |       0.2932 |          0.2482 | 110.637  |     91.2782 |              0 |        0.0006 |   0.9794 |
| regime_follow     |          6 |       0.0742 |          0.0292 |  20.9855 |      7.7996 |              0 |        0.0001 |   0      |

- ETH: short strangle mean P&L per $ notional was +0.0018 on rich_iv nights (n=1) vs +nan on other labelled nights (n=0). Long m=1 call return per $ was -1.000 on rich_iv vs +nan elsewhere. Label does not separate the sell edge.

## SOL: 110 nights, labels {'rich_iv': 74, 'events_underpriced': 16, 'fair_iv': 11, 'unknown': 9}

| coin   | label              |   nights |   long_n |   long_mean |   long_hit |   short_n |   short_mean |   short_worst |   short_hit |
|:-------|:-------------------|---------:|---------:|------------:|-----------:|----------:|-------------:|--------------:|------------:|
| SOL    | events_underpriced |       16 |        4 |     -1      |     0      |         0 |      nan     |      nan      |      0      |
| SOL    | fair_iv            |       11 |        3 |     -1      |     0      |         0 |      nan     |      nan      |      0      |
| SOL    | rich_iv            |       74 |       28 |     -0.4203 |     0.0405 |         9 |        0.002 |        0.0013 |      0.1216 |
| SOL    | unknown            |        9 |        2 |     -1      |     0      |         0 |      nan     |      nan      |      0      |

### SOL NAV paths (SR · IR · MDD · DSR; bold = highlight rule)

| strategy          |   n_nights |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |   worst_night |      dsr |
|:------------------|-----------:|-------------:|----------------:|---------:|------------:|---------------:|--------------:|---------:|
| rwa_only          |        110 |       0.046  |          0.001  | nan      |    nan      |         0      |        0.0001 | nan      |
| always_long_daily |        110 |       0.0372 |         -0.0078 |  16.0683 |     -3.74   |         0      |        0      |   0.0003 |
| always_short      |        110 |       0.0614 |          0.0164 |  22.5539 |      5.5217 |         0      |        0.0001 |   0.5342 |
| regime_follow     |        110 |       0.0601 |          0.0151 |  21.2633 |      4.868  |        -0.0002 |       -0.0002 |   0.3218 |

- SOL: short strangle mean P&L per $ notional was +0.0020 on rich_iv nights (n=9) vs +nan on other labelled nights (n=0). Long m=1 call return per $ was -0.420 on rich_iv vs -1.000 elsewhere. Label does not separate the sell edge.