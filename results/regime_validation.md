# Regime validation (real chains, base TC)

Long overlay = m≈+1 call at ask (incl. fee), return per $ premium = payback − 1. Short overlay = m≈±1.5 strangle at bid (incl. fee), P&L per $ notional per leg. Labels are walk-forward (features use earlier nights only). regime_follow: rich_iv → sell strangle (frac 0.5), else buy calls with 3× accrual on event nights only.


## BTC: 210 nights, labels {'rich_iv': 109, 'fair_iv': 57, 'base': 29, 'unknown': 8, 'events_underpriced': 7}

| coin   | label              |   nights |   long_n |   long_mean |   long_hit |   short_n |   short_mean |   short_worst |   short_hit |
|:-------|:-------------------|---------:|---------:|------------:|-----------:|----------:|-------------:|--------------:|------------:|
| BTC    | base               |       29 |       13 |     -0.3132 |     0.069  |         9 |       0.0005 |        0.0002 |      0.3103 |
| BTC    | events_underpriced |        7 |        3 |     -1      |     0      |         5 |       0.0004 |        0.0001 |      0.7143 |
| BTC    | fair_iv            |       57 |       33 |     -0.3903 |     0.0526 |        18 |       0.0004 |       -0.0012 |      0.2807 |
| BTC    | rich_iv            |      109 |       81 |     -0.5662 |     0.0734 |        57 |       0.0003 |       -0.0103 |      0.4862 |
| BTC    | unknown            |        8 |        5 |     -1      |     0      |         4 |       0.0003 |        0.0002 |      0.5    |

### BTC NAV paths (SR · IR · MDD · DSR; bold = highlight rule)

| strategy          |   n_nights |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |   worst_night |      dsr |
|:------------------|-----------:|-------------:|----------------:|---------:|------------:|---------------:|--------------:|---------:|
| rwa_only          |        210 |       0.046  |          0.001  | nan      |    nan      |         0      |        0.0001 | nan      |
| always_long_daily |        210 |       0.0303 |         -0.0147 |   8.0461 |     -4.0934 |         0      |        0      |   0.0004 |
| always_short      |        210 |       0.0606 |          0.0156 |  10.7374 |      2.5226 |        -0.0025 |       -0.0025 |   0.2816 |
| regime_follow     |        210 |       0.0514 |          0.0064 |   9.1685 |      0.9326 |        -0.0025 |       -0.0025 |   0.039  |

- BTC: short strangle mean P&L per $ notional was +0.0003 on rich_iv nights (n=57) vs +0.0004 on other labelled nights (n=32). Long m=1 call return per $ was -0.566 on rich_iv vs -0.407 elsewhere. Label does not separate the sell edge.

## ETH: 8 nights, labels {'unknown': 5, 'rich_iv': 3}

| coin   | label   |   nights |   long_n |   long_mean |   long_hit |   short_n |   short_mean |   short_worst |   short_hit |
|:-------|:--------|---------:|---------:|------------:|-----------:|----------:|-------------:|--------------:|------------:|
| ETH    | rich_iv |        3 |        3 |          -1 |          0 |         3 |       0.0014 |        0.0012 |           1 |
| ETH    | unknown |        5 |        5 |          -1 |          0 |         5 |       0.0024 |        0.0018 |           1 |

### ETH NAV paths (SR · IR · MDD · DSR; bold = highlight rule)

| strategy          |   n_nights |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |   worst_night |      dsr |
|:------------------|-----------:|-------------:|----------------:|---------:|------------:|---------------:|--------------:|---------:|
| rwa_only          |          8 |       0.046  |          0.001  | nan      |    nan      |              0 |        0.0001 | nan      |
| always_long_daily |          8 |       0      |         -0.045  | nan      |    nan      |              0 |        0      | nan      |
| always_short      |          8 |       0.2624 |          0.2174 |  76.319  |     61.5846 |              0 |        0.0004 |   0.9902 |
| regime_follow     |          8 |       0.0984 |          0.0534 |  26.0464 |     13.5655 |              0 |        0.0001 |   0      |

- ETH: short strangle mean P&L per $ notional was +0.0014 on rich_iv nights (n=3) vs +nan on other labelled nights (n=0). Long m=1 call return per $ was -1.000 on rich_iv vs +nan elsewhere. Label does not separate the sell edge.

## SOL: 112 nights, labels {'rich_iv': 76, 'events_underpriced': 16, 'fair_iv': 11, 'unknown': 9}

| coin   | label              |   nights |   long_n |   long_mean |   long_hit |   short_n |   short_mean |   short_worst |   short_hit |
|:-------|:-------------------|---------:|---------:|------------:|-----------:|----------:|-------------:|--------------:|------------:|
| SOL    | events_underpriced |       16 |        4 |      -1     |     0      |         0 |      nan     |      nan      |      0      |
| SOL    | fair_iv            |       11 |        3 |      -1     |     0      |         0 |      nan     |      nan      |      0      |
| SOL    | rich_iv            |       76 |       30 |      -0.459 |     0.0395 |        11 |        0.002 |        0.0013 |      0.1447 |
| SOL    | unknown            |        9 |        2 |      -1     |     0      |         0 |      nan     |      nan      |      0      |

### SOL NAV paths (SR · IR · MDD · DSR; bold = highlight rule)

| strategy          |   n_nights |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |   worst_night |      dsr |
|:------------------|-----------:|-------------:|----------------:|---------:|------------:|---------------:|--------------:|---------:|
| rwa_only          |        112 |       0.046  |          0.001  | nan      |    nan      |         0      |        0.0001 | nan      |
| always_long_daily |        112 |       0.0365 |         -0.0085 |  15.825  |     -4.038  |         0      |        0      |   0.0001 |
| always_short      |        112 |       0.0648 |          0.0198 |  21.5451 |      6.1072 |         0      |        0.0001 |   0.5475 |
| regime_follow     |        112 |       0.0635 |          0.0185 |  20.4628 |      5.5135 |        -0.0002 |       -0.0002 |   0.3452 |

- SOL: short strangle mean P&L per $ notional was +0.0020 on rich_iv nights (n=11) vs +nan on other labelled nights (n=0). Long m=1 call return per $ was -0.459 on rich_iv vs -1.000 elsewhere. Label does not separate the sell edge.