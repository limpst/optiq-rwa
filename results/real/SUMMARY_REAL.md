# Real-data backtest (Deribit trade VWAP chains)

Quotes = VWAP of trades within +/-20 min of 19:20 UTC, bid/ask rebuilt with the synthetic spread model (10% + 2bp). Indicative only. Event nights = entry on a FOMC decision day or US CPI day (data/events.csv; the print is already out at the 19:20 UTC entry, so the night carries the post-event move).


## BTC: 201 nights (2026-05-01 .. 2026-11-18), 1494 traded strikes, 11 event nights

Nights with a strike within tol of each m bucket:

|        |   -2.5 |   -2.0 |   -1.5 |   -1.0 |   -0.5 |   0.0 |   0.5 |   1.0 |   1.5 |   2.0 |   2.5 |
|:-------|-------:|-------:|-------:|-------:|-------:|------:|------:|------:|------:|------:|------:|
| nights |     69 |    107 |    127 |    131 |    135 |   147 |   127 |   127 |   125 |    88 |    59 |

Event vs non-event nights, calls m=1 (payback_ask):

| event   |   n |   p_itm_model |   p_itm_emp |   payback_mid |   payback_ask |
|:--------|----:|--------------:|------------:|--------------:|--------------:|
| False   | 120 |         0.143 |       0.108 |         0.816 |         0.621 |
| True    |   7 |         0.142 |       0     |         0     |         0     |

### Idea 4 - calibration (calls)

|   m |   n |   p_itm_model |   p_itm_emp |   p_be_model |   p_be_emp |   payback_mid |   payback_ask |
|----:|----:|--------------:|------------:|-------------:|-----------:|--------------:|--------------:|
| 0   | 105 |         0.485 |       0.448 |        0.315 |      0.229 |         0.789 |         0.689 |
| 0   |   9 |         0.515 |       0.667 |        0.332 |      0.333 |         0.882 |         0.775 |
| 0.5 | 118 |         0.299 |       0.246 |        0.221 |      0.153 |         0.646 |         0.543 |
| 0.5 |   9 |         0.281 |       0.111 |        0.221 |      0.111 |         0.289 |         0.24  |
| 1   | 120 |         0.143 |       0.108 |        0.12  |      0.1   |         0.816 |         0.621 |
| 1   |   7 |         0.142 |       0     |        0.121 |      0     |         0     |         0     |
| 1.5 | 118 |         0.069 |       0.059 |        0.062 |      0.059 |         1.016 |         0.651 |
| 1.5 |   7 |         0.064 |       0     |        0.058 |      0     |         0     |         0     |
| 2   |  83 |         0.038 |       0     |        0.035 |      0     |         0     |         0     |
| 2   |   5 |         0.046 |       0     |        0.043 |      0     |         0     |         0     |
| 2.5 |  51 |         0.022 |       0     |        0.021 |      0     |         0     |         0     |
| 2.5 |   8 |         0.023 |       0     |        0.021 |      0     |         0     |         0     |

### Ideas 1 / 3 on real quotes, cost model = none (fee per $ premium -0.002); **bold** = SR>0, IR>0.5, MDD>=-15%, DSR>=0.95

| idea                 | params                                  |   nights |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |   worst_night |    dsr |   payback_ask |
|:---------------------|:----------------------------------------|---------:|-------------:|----------------:|---------:|------------:|---------------:|--------------:|-------:|--------------:|
| 1_yield_funded_calls | m=0.5 daily bm=1.0                      |      102 |       0.0205 |         -0.0245 |   7.1549 |     -8.6876 |         0      |        0      | 0.0003 |        0.4515 |
| 1_yield_funded_calls | m=0.5 daily bm=3.0                      |      102 |      -0.0286 |         -0.0736 |  -3.4067 |     -8.6876 |        -0.0093 |       -0.0002 | 0.0003 |        0.4514 |
| 1_yield_funded_calls | m=0.5 event_only bm=3.0                 |      102 |       0.0362 |         -0.0088 |  17.578  |     -4.6507 |        -0.0002 |       -0.0002 | 0      |        0.2092 |
| 1_yield_funded_calls | m=0.5 bank_event bm=1.0                 |      102 |       0.0097 |         -0.0353 |   1.1754 |     -4.2627 |        -0.0021 |       -0.0021 | 0      |        0.1748 |
| 1_yield_funded_calls | m=1.0 daily bm=1.0                      |       97 |       0.0316 |         -0.0134 |   5.226  |     -2.3302 |         0      |        0      | 0.0124 |        0.6904 |
| 1_yield_funded_calls | m=1.0 daily bm=3.0                      |       97 |       0.0032 |         -0.0418 |   0.1885 |     -2.3302 |        -0.0092 |       -0.0002 | 0.0124 |        0.6904 |
| 1_yield_funded_calls | m=1.0 event_only bm=3.0                 |       97 |       0.0373 |         -0.0077 |  21.4193 |     -4.8804 |        -0.0004 |       -0.0002 | 0      |        0      |
| 1_yield_funded_calls | m=1.0 bank_event bm=1.0                 |       97 |       0.0117 |         -0.0333 |   1.3139 |     -3.7674 |        -0.0028 |       -0.0028 | 0      |        0      |
| 1_yield_funded_calls | m=1.5 daily bm=1.0                      |       94 |       0.0238 |         -0.0212 |   4.2565 |     -3.8901 |         0      |        0      | 0.0121 |        0.5218 |
| 1_yield_funded_calls | m=1.5 daily bm=3.0                      |       94 |      -0.0194 |         -0.0644 |  -1.1745 |     -3.8901 |        -0.0082 |       -0.0002 | 0.0121 |        0.5218 |
| 1_yield_funded_calls | m=1.5 event_only bm=3.0                 |       94 |       0.037  |         -0.008  |  20.9507 |     -4.962  |        -0.0004 |       -0.0002 | 0      |        0      |
| 1_yield_funded_calls | m=1.5 bank_event bm=1.0                 |       94 |       0.0072 |         -0.0378 |   0.7291 |     -3.8094 |        -0.0031 |       -0.0031 | 0      |        0      |
| 3_short_premium      | m=1.5 wing=2.5 frac=0.25 skip_ev=False  |       13 |       0.0273 |         -0.0177 |  18.6503 |    -12.5638 |        -0.0001 |       -0.0001 | 0      |      nan      |
| 3_short_premium      | m=1.5 wing=2.5 frac=0.5 skip_ev=False   |       13 |       0.0088 |         -0.0362 |   3.0433 |    -12.5638 |        -0.0003 |       -0.0002 | 0      |      nan      |
| 3_short_premium      | m=1.5 wing=2.5 frac=0.5 skip_ev=True    |       13 |       0.0191 |         -0.0259 |   8.0379 |    -11.1021 |        -0.0002 |       -0.0002 | 0      |      nan      |
| 3_short_premium      | m=1.5 wing=None frac=0.25 skip_ev=False |       61 |       0.0632 |          0.0182 |   6.4762 |      1.7226 |        -0.0024 |       -0.0024 | 0      |      nan      |
| 3_short_premium      | m=1.5 wing=None frac=0.5 skip_ev=False  |       61 |       0.0805 |          0.0355 |   4.0994 |      1.7226 |        -0.0054 |       -0.005  | 0      |      nan      |
| 3_short_premium      | m=1.5 wing=None frac=0.5 skip_ev=True   |       61 |       0.0685 |          0.0235 |   3.5224 |      1.1362 |        -0.0056 |       -0.005  | 0      |      nan      |
| 3_short_premium      | m=2.0 wing=None frac=0.25 skip_ev=False |       41 |       0.0623 |          0.0173 |  70.7979 |     18.0862 |         0      |        0.0001 | 0.3136 |      nan      |
| 3_short_premium      | m=2.0 wing=None frac=0.5 skip_ev=False  |       41 |       0.0788 |          0.0338 |  44.442  |     18.0862 |        -0      |       -0      | 0.3136 |      nan      |
| 3_short_premium      | m=2.0 wing=None frac=0.5 skip_ev=True   |       41 |       0.0756 |          0.0306 |  42.891  |     16.4025 |        -0      |       -0      | 0.1313 |      nan      |

### Ideas 1 / 3 on real quotes, cost model = base (fee per $ premium 0.083); **bold** = SR>0, IR>0.5, MDD>=-15%, DSR>=0.95

| idea                 | params                                  |   nights |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |   worst_night |    dsr |   payback_ask |
|:---------------------|:----------------------------------------|---------:|-------------:|----------------:|---------:|------------:|---------------:|--------------:|-------:|--------------:|
| 1_yield_funded_calls | m=0.5 daily bm=1.0                      |      102 |       0.0187 |         -0.0263 |   7.1734 |    -10.2505 |         0      |        0      | 0.0001 |        0.4116 |
| 1_yield_funded_calls | m=0.5 daily bm=3.0                      |      102 |      -0.0339 |         -0.0789 |  -4.4425 |    -10.2505 |        -0.0106 |       -0.0002 | 0.0001 |        0.4115 |
| 1_yield_funded_calls | m=0.5 event_only bm=3.0                 |      102 |       0.036  |         -0.009  |  17.8141 |     -4.8775 |        -0.0002 |       -0.0002 | 0      |        0.1877 |
| 1_yield_funded_calls | m=0.5 bank_event bm=1.0                 |      102 |       0.009  |         -0.036  |   1.0942 |     -4.4051 |        -0.0021 |       -0.0021 | 0      |        0.1568 |
| 1_yield_funded_calls | m=1.0 daily bm=1.0                      |       97 |       0.028  |         -0.017  |   5.226  |     -3.2748 |         0      |        0      | 0.0049 |        0.6138 |
| 1_yield_funded_calls | m=1.0 daily bm=3.0                      |       97 |      -0.0071 |         -0.0521 |  -0.4412 |     -3.2748 |        -0.0099 |       -0.0002 | 0.0049 |        0.614  |
| 1_yield_funded_calls | m=1.0 event_only bm=3.0                 |       97 |       0.0373 |         -0.0077 |  21.4193 |     -4.8804 |        -0.0004 |       -0.0002 | 0      |        0      |
| 1_yield_funded_calls | m=1.0 bank_event bm=1.0                 |       97 |       0.0117 |         -0.0333 |   1.3139 |     -3.7674 |        -0.0028 |       -0.0028 | 0      |        0      |
| 1_yield_funded_calls | m=1.5 daily bm=1.0                      |       94 |       0.0211 |         -0.0239 |   4.2565 |     -4.9084 |         0      |        0      | 0.0064 |        0.4639 |
| 1_yield_funded_calls | m=1.5 daily bm=3.0                      |       94 |      -0.027  |         -0.072  |  -1.8534 |     -4.9084 |        -0.0092 |       -0.0002 | 0.0064 |        0.464  |
| 1_yield_funded_calls | m=1.5 event_only bm=3.0                 |       94 |       0.037  |         -0.008  |  20.9507 |     -4.962  |        -0.0004 |       -0.0002 | 0      |        0      |
| 1_yield_funded_calls | m=1.5 bank_event bm=1.0                 |       94 |       0.0072 |         -0.0378 |   0.7291 |     -3.8094 |        -0.0031 |       -0.0031 | 0      |        0      |
| 3_short_premium      | m=1.5 wing=2.5 frac=0.25 skip_ev=False  |       13 |       0.0151 |         -0.0299 |  10.6316 |    -21.2075 |        -0.0001 |       -0.0001 | 0      |      nan      |
| 3_short_premium      | m=1.5 wing=2.5 frac=0.5 skip_ev=False   |       13 |      -0.0148 |         -0.0598 |  -5.288  |    -21.2075 |        -0.0005 |       -0.0003 | 0      |      nan      |
| 3_short_premium      | m=1.5 wing=2.5 frac=0.5 skip_ev=True    |       13 |       0.0033 |         -0.0417 |   1.3274 |    -16.7871 |        -0.0002 |       -0.0002 | 0      |      nan      |
| 3_short_premium      | m=1.5 wing=None frac=0.25 skip_ev=False |       61 |       0.0557 |          0.0107 |   5.7463 |      0.9784 |        -0.0025 |       -0.0025 | 0      |      nan      |
| 3_short_premium      | m=1.5 wing=None frac=0.5 skip_ev=False  |       61 |       0.0653 |          0.0203 |   3.3624 |      0.9784 |        -0.0059 |       -0.005  | 0      |      nan      |
| 3_short_premium      | m=1.5 wing=None frac=0.5 skip_ev=True   |       61 |       0.055  |          0.01   |   2.8546 |      0.4616 |        -0.006  |       -0.005  | 0      |      nan      |
| 3_short_premium      | m=2.0 wing=None frac=0.25 skip_ev=False |       41 |       0.0601 |          0.0151 |  76.2406 |     17.4674 |         0      |        0.0001 | 0.0203 |      nan      |
| 3_short_premium      | m=2.0 wing=None frac=0.5 skip_ev=False  |       41 |       0.0744 |          0.0294 |  46.854  |     17.4674 |        -0      |       -0      | 0.0203 |      nan      |
| 3_short_premium      | m=2.0 wing=None frac=0.5 skip_ev=True   |       41 |       0.0715 |          0.0265 |  45.3868 |     15.8339 |        -0      |       -0      | 0.0033 |      nan      |

### Ideas 1 / 3 on real quotes, cost model = stress (fee per $ premium 0.466); **bold** = SR>0, IR>0.5, MDD>=-15%, DSR>=0.95

| idea                 | params                                  |   nights |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |   worst_night |    dsr |   payback_ask |
|:---------------------|:----------------------------------------|---------:|-------------:|----------------:|---------:|------------:|---------------:|--------------:|-------:|--------------:|
| 1_yield_funded_calls | m=0.5 daily bm=1.0                      |      102 |       0.0139 |         -0.0311 |   7.213  |    -16.2879 |         0      |        0      | 0      |        0.3069 |
| 1_yield_funded_calls | m=0.5 daily bm=3.0                      |      102 |      -0.0474 |         -0.0924 |  -8.4542 |    -16.2879 |        -0.0139 |       -0.0002 | 0      |        0.3068 |
| 1_yield_funded_calls | m=0.5 event_only bm=3.0                 |      102 |       0.0354 |         -0.0096 |  18.0717 |     -5.3146 |        -0.0002 |       -0.0002 | 0      |        0.1413 |
| 1_yield_funded_calls | m=0.5 bank_event bm=1.0                 |      102 |       0.0073 |         -0.0377 |   0.9058 |     -4.6833 |        -0.0021 |       -0.0021 | 0      |        0.118  |
| 1_yield_funded_calls | m=1.0 daily bm=1.0                      |       97 |       0.0182 |         -0.0268 |   4.9787 |     -7.4357 |         0      |        0      | 0.0002 |        0.4006 |
| 1_yield_funded_calls | m=1.0 daily bm=3.0                      |       97 |      -0.0353 |         -0.0803 |  -3.2976 |     -7.4357 |        -0.0116 |       -0.0002 | 0.0002 |        0.4012 |
| 1_yield_funded_calls | m=1.0 event_only bm=3.0                 |       97 |       0.0373 |         -0.0077 |  21.4193 |     -4.8804 |        -0.0004 |       -0.0002 | 0      |        0      |
| 1_yield_funded_calls | m=1.0 bank_event bm=1.0                 |       97 |       0.0117 |         -0.0333 |   1.3139 |     -3.7674 |        -0.0028 |       -0.0028 | 0      |        0      |
| 1_yield_funded_calls | m=1.5 daily bm=1.0                      |       94 |       0.0127 |         -0.0323 |   3.8758 |     -9.891  |         0      |        0      | 0.0014 |        0.2813 |
| 1_yield_funded_calls | m=1.5 daily bm=3.0                      |       94 |      -0.0507 |         -0.0957 |  -5.3021 |     -9.891  |        -0.0133 |       -0.0002 | 0.0014 |        0.2816 |
| 1_yield_funded_calls | m=1.5 event_only bm=3.0                 |       94 |       0.037  |         -0.008  |  20.9507 |     -4.962  |        -0.0004 |       -0.0002 | 0      |        0      |
| 1_yield_funded_calls | m=1.5 bank_event bm=1.0                 |       94 |       0.0072 |         -0.0378 |   0.7291 |     -3.8094 |        -0.0031 |       -0.0031 | 0      |        0      |
| 3_short_premium      | m=1.5 wing=2.5 frac=0.25 skip_ev=False  |       13 |      -0.1071 |         -0.1521 | -68.9738 |    -96.3727 |        -0.004  |       -0.0005 | 0      |      nan      |
| 3_short_premium      | m=1.5 wing=2.5 frac=0.5 skip_ev=False   |       13 |      -0.2379 |         -0.2829 | -82.6733 |    -96.3727 |        -0.0096 |       -0.001  | 0      |      nan      |
| 3_short_premium      | m=1.5 wing=2.5 frac=0.5 skip_ev=True    |       13 |      -0.1571 |         -0.2021 | -21.2595 |    -26.86   |        -0.0061 |       -0.0009 | 0      |      nan      |
| 3_short_premium      | m=1.5 wing=None frac=0.25 skip_ev=False |       61 |       0.0086 |         -0.0364 |   0.9088 |     -3.8247 |        -0.0038 |       -0.0027 | 0      |      nan      |
| 3_short_premium      | m=1.5 wing=None frac=0.5 skip_ev=False  |       61 |      -0.0275 |         -0.0725 |  -1.458  |     -3.8247 |        -0.009  |       -0.0055 | 0      |      nan      |
| 3_short_premium      | m=1.5 wing=None frac=0.5 skip_ev=True   |       61 |      -0.0283 |         -0.0733 |  -1.5029 |     -3.8711 |        -0.009  |       -0.0055 | 0      |      nan      |
| 3_short_premium      | m=2.0 wing=None frac=0.25 skip_ev=False |       41 |       0.0449 |         -0.0001 | 106.234  |     -2.7082 |        -0      |       -0      | 0      |      nan      |
| 3_short_premium      | m=2.0 wing=None frac=0.5 skip_ev=False  |       41 |       0.0437 |         -0.0013 |  51.7628 |     -2.7082 |        -0.0002 |       -0.0002 | 0      |      nan      |
| 3_short_premium      | m=2.0 wing=None frac=0.5 skip_ev=True   |       41 |       0.0437 |         -0.0013 |  51.7628 |     -2.7082 |        -0.0002 |       -0.0002 | 0      |      nan      |

## SOL: 95 nights (2026-05-01 .. 2026-11-17), 275 traded strikes, 8 event nights

Nights with a strike within tol of each m bucket:

|        |   -2.5 |   -2.0 |   -1.5 |   -1.0 |   -0.5 |   0.0 |   0.5 |   1.0 |   1.5 |   2.0 |   2.5 |
|:-------|-------:|-------:|-------:|-------:|-------:|------:|------:|------:|------:|------:|------:|
| nights |      2 |      3 |     23 |     26 |     34 |    61 |    35 |    32 |    19 |     5 |     2 |

Event vs non-event nights, calls m=1 (payback_ask):

| event   |   n |   p_itm_model |   p_itm_emp |   payback_mid |   payback_ask |
|:--------|----:|--------------:|------------:|--------------:|--------------:|
| False   |  30 |         0.172 |         0.1 |         0.819 |         0.693 |
| True    |   2 |         0.126 |         0   |         0     |         0     |

### Idea 4 - calibration (calls)

|   m |   n |   p_itm_model |   p_itm_emp |   p_be_model |   p_be_emp |   payback_mid |   payback_ask |
|----:|----:|--------------:|------------:|-------------:|-----------:|--------------:|--------------:|
| 0   |  38 |         0.495 |       0.289 |        0.318 |      0.132 |         0.434 |         0.387 |
| 0   |   1 |         0.423 |       0     |        0.283 |      0     |         0     |         0     |
| 0.5 |  34 |         0.303 |       0.176 |        0.227 |      0.147 |         0.696 |         0.609 |
| 0.5 |   1 |         0.423 |       0     |        0.283 |      0     |         0     |         0     |
| 1   |  30 |         0.172 |       0.1   |        0.143 |      0.1   |         0.819 |         0.693 |
| 1   |   2 |         0.126 |       0     |        0.108 |      0     |         0     |         0     |
| 1.5 |  16 |         0.098 |       0.062 |        0.087 |      0.062 |         0.3   |         0.241 |
| 1.5 |   3 |         0.09  |       0     |        0.08  |      0     |         0     |         0     |
| 2   |   5 |         0.055 |       0     |        0.051 |      0     |         0     |         0     |
| 2.5 |   2 |         0.05  |       0     |        0.047 |      0     |         0     |         0     |

### Ideas 1 / 3 on real quotes, cost model = none (fee per $ premium 0.000); **bold** = SR>0, IR>0.5, MDD>=-15%, DSR>=0.95

| idea                 | params                  |   nights |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |   worst_night |      dsr |   payback_ask |
|:---------------------|:------------------------|---------:|-------------:|----------------:|---------:|------------:|---------------:|--------------:|---------:|--------------:|
| 1_yield_funded_calls | m=0.5 daily bm=1.0      |       14 |       0.0224 |         -0.0226 |   8.6276 |     -8.8817 |         0      |        0      |   0.06   |        0.4927 |
| 1_yield_funded_calls | m=0.5 daily bm=3.0      |       14 |      -0.0232 |         -0.0682 |  -3.0453 |     -8.8817 |        -0.0017 |       -0.0002 |   0.06   |        0.4925 |
| 1_yield_funded_calls | m=0.5 event_only bm=3.0 |       14 |       0.046  |          0.001  | nan      |    nan      |         0      |        0.0001 | nan      |      nan      |
| 1_yield_funded_calls | m=0.5 bank_event bm=1.0 |       14 |       0.046  |          0.001  | nan      |    nan      |         0      |        0.0001 | nan      |      nan      |
| 1_yield_funded_calls | m=1.0 daily bm=1.0      |       19 |       0.0233 |         -0.0217 |   5.7783 |     -5.5097 |         0      |        0      |   0.1004 |        0.5119 |
| 1_yield_funded_calls | m=1.0 daily bm=3.0      |       19 |      -0.0207 |         -0.0657 |  -1.747  |     -5.5097 |        -0.0027 |       -0.0002 |   0.1004 |        0.5113 |
| 1_yield_funded_calls | m=1.0 event_only bm=3.0 |       19 |       0.0386 |         -0.0064 |  23.3759 |     -4.383  |        -0.0002 |       -0.0002 |   0.0011 |        0      |
| 1_yield_funded_calls | m=1.0 bank_event bm=1.0 |       19 |       0.0411 |         -0.0039 |  37.2579 |     -4.383  |        -0.0001 |       -0.0001 |   0.0011 |        0      |

### Ideas 1 / 3 on real quotes, cost model = base (fee per $ premium 0.047); **bold** = SR>0, IR>0.5, MDD>=-15%, DSR>=0.95

| idea                 | params                  |   nights |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |   worst_night |      dsr |   payback_ask |
|:---------------------|:------------------------|---------:|-------------:|----------------:|---------:|------------:|---------------:|--------------:|---------:|--------------:|
| 1_yield_funded_calls | m=0.5 daily bm=1.0      |       14 |       0.0212 |         -0.0238 |   8.6336 |     -9.8513 |         0      |        0      |   0.0454 |        0.467  |
| 1_yield_funded_calls | m=0.5 daily bm=3.0      |       14 |      -0.0266 |         -0.0716 |  -3.6897 |     -9.8513 |        -0.0017 |       -0.0002 |   0.0454 |        0.4668 |
| 1_yield_funded_calls | m=0.5 event_only bm=3.0 |       14 |       0.046  |          0.001  | nan      |    nan      |         0      |        0.0001 | nan      |      nan      |
| 1_yield_funded_calls | m=0.5 bank_event bm=1.0 |       14 |       0.046  |          0.001  | nan      |    nan      |         0      |        0.0001 | nan      |      nan      |
| 1_yield_funded_calls | m=1.0 daily bm=1.0      |       19 |       0.021  |         -0.024  |   5.8325 |     -6.7775 |         0      |        0      |   0.074  |        0.4625 |
| 1_yield_funded_calls | m=1.0 daily bm=3.0      |       19 |      -0.0272 |         -0.0722 |  -2.5742 |     -6.7775 |        -0.0027 |       -0.0002 |   0.074  |        0.462  |
| 1_yield_funded_calls | m=1.0 event_only bm=3.0 |       19 |       0.0386 |         -0.0064 |  23.3759 |     -4.383  |        -0.0002 |       -0.0002 |   0.0005 |        0      |
| 1_yield_funded_calls | m=1.0 bank_event bm=1.0 |       19 |       0.0411 |         -0.0039 |  37.2579 |     -4.383  |        -0.0001 |       -0.0001 |   0.0005 |        0      |

### Ideas 1 / 3 on real quotes, cost model = stress (fee per $ premium 0.296); **bold** = SR>0, IR>0.5, MDD>=-15%, DSR>=0.95

| idea                 | params                  |   nights |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |   worst_night |      dsr |   payback_ask |
|:---------------------|:------------------------|---------:|-------------:|----------------:|---------:|------------:|---------------:|--------------:|---------:|--------------:|
| 1_yield_funded_calls | m=0.5 daily bm=1.0      |       14 |       0.017  |         -0.028  |   8.6223 |    -14.4513 |         0      |        0      |   0.011  |        0.3737 |
| 1_yield_funded_calls | m=0.5 daily bm=3.0      |       14 |      -0.0388 |         -0.0838 |  -6.7601 |    -14.4513 |        -0.002  |       -0.0002 |   0.011  |        0.3735 |
| 1_yield_funded_calls | m=0.5 event_only bm=3.0 |       14 |       0.046  |          0.001  | nan      |    nan      |         0      |        0.0001 | nan      |      nan      |
| 1_yield_funded_calls | m=0.5 bank_event bm=1.0 |       14 |       0.046  |          0.001  | nan      |    nan      |         0      |        0.0001 | nan      |      nan      |
| 1_yield_funded_calls | m=1.0 daily bm=1.0      |       19 |       0.0162 |         -0.0288 |   5.8731 |    -10.5762 |         0      |        0      |   0.0228 |        0.357  |
| 1_yield_funded_calls | m=1.0 daily bm=3.0      |       19 |      -0.041  |         -0.086  |  -5.0931 |    -10.5762 |        -0.0027 |       -0.0002 |   0.0228 |        0.3566 |
| 1_yield_funded_calls | m=1.0 event_only bm=3.0 |       19 |       0.0386 |         -0.0064 |  23.3759 |     -4.383  |        -0.0002 |       -0.0002 |   0      |        0      |
| 1_yield_funded_calls | m=1.0 bank_event bm=1.0 |       19 |       0.0411 |         -0.0039 |  37.2579 |     -4.383  |        -0.0001 |       -0.0001 |   0      |        0      |

## Period returns, best strategy by final NAV under base costs: BTC|base|short m=1.5 wing=None frac=0.5 skip_ev=False


### Monthly

| period     |   n_days |     ret |   excess |   max_dd |   worst_day |
|:-----------|---------:|--------:|---------:|---------:|------------:|
| 2026-06-30 |       11 |  0.0023 |   0.0009 |  -0.0017 |     -0.0017 |
| 2026-07-31 |       10 |  0.0033 |   0.0021 |   0      |      0.0002 |
| 2026-08-31 |        9 |  0.0036 |   0.0024 |   0      |      0.0003 |
| 2026-09-30 |       11 |  0.0029 |   0.0015 |  -0.0005 |     -0.0005 |
| 2026-10-31 |       10 | -0.0015 |  -0.0028 |  -0.0047 |     -0.0047 |
| 2026-11-30 |       10 | -0.0004 |  -0.0016 |  -0.005  |     -0.005  |

### Weekly (last 12)

| period     |   n_days |     ret |   excess |   max_dd |   worst_day |
|:-----------|---------:|--------:|---------:|---------:|------------:|
| 2026-09-06 |        3 |  0.0014 |   0.001  |   0      |      0.0003 |
| 2026-09-13 |        3 |  0.0006 |   0.0002 |   0      |      0.0002 |
| 2026-09-20 |        2 |  0.0008 |   0.0005 |   0      |      0.0003 |
| 2026-09-27 |        3 |  0.0001 |  -0.0003 |  -0.0005 |     -0.0005 |
| 2026-10-04 |        1 |  0.0004 |   0.0003 |   0      |      0.0004 |
| 2026-10-11 |        3 |  0.0011 |   0.0008 |   0      |      0.0003 |
| 2026-10-18 |        2 |  0.0009 |   0.0007 |   0      |      0.0004 |
| 2026-10-25 |        3 | -0.0041 |  -0.0045 |  -0.0047 |     -0.0047 |
| 2026-11-01 |        2 |  0.0005 |   0.0003 |   0      |      0.0002 |
| 2026-11-08 |        5 |  0.0022 |   0.0016 |   0      |      0.0002 |
| 2026-11-15 |        4 | -0.0034 |  -0.0039 |  -0.005  |     -0.005  |
| 2026-11-22 |        1 |  0.0008 |   0.0007 |   0      |      0.0008 |

### Final NAV by cost model (same strategy)

|    none |    base |   stress |
|--------:|--------:|---------:|
| 1.01302 | 1.01063 |  0.99535 |