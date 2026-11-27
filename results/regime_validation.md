# Regime validation (real chains, base TC)

Long overlay = m≈+1 call at ask (incl. fee), return per $ premium = payback − 1. Short overlay = m≈±1.5 strangle at bid (incl. fee), P&L per $ notional per leg. Labels are walk-forward (features use earlier nights only). regime_follow: rich_iv → sell strangle (frac 0.5), else buy calls with 3× accrual on event nights only.


## BTC: 209 nights, labels {'rich_iv': 108, 'fair_iv': 57, 'base': 29, 'unknown': 8, 'events_underpriced': 7}

| coin   | label              |   nights |   long_n |   long_mean |   long_hit |   short_n |   short_mean |   short_worst |   short_hit |
|:-------|:-------------------|---------:|---------:|------------:|-----------:|----------:|-------------:|--------------:|------------:|
| BTC    | base               |       29 |       13 |     -0.3132 |     0.069  |         9 |       0.0005 |        0.0002 |      0.3103 |
| BTC    | events_underpriced |        7 |        3 |     -1      |     0      |         5 |       0.0004 |        0.0001 |      0.7143 |
| BTC    | fair_iv            |       57 |       33 |     -0.3903 |     0.0526 |        18 |       0.0004 |       -0.0012 |      0.2807 |
| BTC    | rich_iv            |      108 |       80 |     -0.5608 |     0.0741 |        56 |       0.0003 |       -0.0103 |      0.4815 |
| BTC    | unknown            |        8 |        5 |     -1      |     0      |         4 |       0.0003 |        0.0002 |      0.5    |

### BTC NAV paths (SR · IR · MDD · DSR; bold = highlight rule)

| strategy          |   n_nights |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |   worst_night |      dsr |
|:------------------|-----------:|-------------:|----------------:|---------:|------------:|---------------:|--------------:|---------:|
| rwa_only          |        209 |       0.046  |          0.001  | nan      |    nan      |         0      |        0.0001 | nan      |
| always_long_daily |        209 |       0.0304 |         -0.0146 |   8.0687 |     -4.0469 |         0      |        0      |   0.0005 |
| always_short      |        209 |       0.0601 |          0.0151 |  10.6559 |      2.4487 |        -0.0025 |       -0.0025 |   0.2799 |
| regime_follow     |        209 |       0.0509 |          0.0059 |   9.0838 |      0.8527 |        -0.0025 |       -0.0025 |   0.0372 |

- BTC: short strangle mean P&L per $ notional was +0.0003 on rich_iv nights (n=56) vs +0.0004 on other labelled nights (n=32). Long m=1 call return per $ was -0.561 on rich_iv vs -0.407 elsewhere. Label does not separate the sell edge.

## ETH: 7 nights, labels {'unknown': 5, 'rich_iv': 2}

| coin   | label   |   nights |   long_n |   long_mean |   long_hit |   short_n |   short_mean |   short_worst |   short_hit |
|:-------|:--------|---------:|---------:|------------:|-----------:|----------:|-------------:|--------------:|------------:|
| ETH    | rich_iv |        2 |        2 |          -1 |          0 |         2 |       0.0015 |        0.0012 |           1 |
| ETH    | unknown |        5 |        5 |          -1 |          0 |         5 |       0.0024 |        0.0018 |           1 |

### ETH NAV paths (SR · IR · MDD · DSR; bold = highlight rule)

| strategy          |   n_nights |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |   worst_night |      dsr |
|:------------------|-----------:|-------------:|----------------:|---------:|------------:|---------------:|--------------:|---------:|
| rwa_only          |          7 |       0.046  |          0.001  | nan      |    nan      |              0 |        0.0001 | nan      |
| always_long_daily |          7 |       0      |         -0.045  | nan      |    nan      |              0 |        0      | nan      |
| always_short      |          7 |       0.2748 |          0.2298 |  83.5534 |     68.0704 |              0 |        0.0004 |   0.9452 |
| regime_follow     |          7 |       0.0874 |          0.0424 |  23.6555 |     10.9506 |              0 |        0.0001 |   0      |

- ETH: short strangle mean P&L per $ notional was +0.0015 on rich_iv nights (n=2) vs +nan on other labelled nights (n=0). Long m=1 call return per $ was -1.000 on rich_iv vs +nan elsewhere. Label does not separate the sell edge.

## SOL: 111 nights, labels {'rich_iv': 75, 'events_underpriced': 16, 'fair_iv': 11, 'unknown': 9}

| coin   | label              |   nights |   long_n |   long_mean |   long_hit |   short_n |   short_mean |   short_worst |   short_hit |
|:-------|:-------------------|---------:|---------:|------------:|-----------:|----------:|-------------:|--------------:|------------:|
| SOL    | events_underpriced |       16 |        4 |     -1      |       0    |         0 |     nan      |      nan      |      0      |
| SOL    | fair_iv            |       11 |        3 |     -1      |       0    |         0 |     nan      |      nan      |      0      |
| SOL    | rich_iv            |       75 |       29 |     -0.4403 |       0.04 |        10 |       0.0019 |        0.0013 |      0.1333 |
| SOL    | unknown            |        9 |        2 |     -1      |       0    |         0 |     nan      |      nan      |      0      |

### SOL NAV paths (SR · IR · MDD · DSR; bold = highlight rule)

| strategy          |   n_nights |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |   worst_night |      dsr |
|:------------------|-----------:|-------------:|----------------:|---------:|------------:|---------------:|--------------:|---------:|
| rwa_only          |        111 |       0.046  |          0.001  | nan      |    nan      |         0      |        0.0001 | nan      |
| always_long_daily |        111 |       0.0368 |         -0.0082 |  15.9452 |     -3.89   |         0      |        0      |   0.0002 |
| always_short      |        111 |       0.0627 |          0.0177 |  22.3547 |      5.8272 |         0      |        0.0001 |   0.5443 |
| regime_follow     |        111 |       0.0615 |          0.0165 |  21.1293 |      5.1893 |        -0.0002 |       -0.0002 |   0.3325 |

- SOL: short strangle mean P&L per $ notional was +0.0019 on rich_iv nights (n=10) vs +nan on other labelled nights (n=0). Long m=1 call return per $ was -0.440 on rich_iv vs -1.000 elsewhere. Label does not separate the sell edge.