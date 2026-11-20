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

### Ideas 1 / 3 on real quotes (out-of-sample after warmup)

| idea                 | params                                  |   nights |   ann_return |   excess_vs_rwa |   sharpe_vs_rwa |   max_drawdown |   worst_night |   payback_ask |
|:---------------------|:----------------------------------------|---------:|-------------:|----------------:|----------------:|---------------:|--------------:|--------------:|
| 1_yield_funded_calls | m=0.5 daily bm=1.0                      |      102 |       0.0205 |         -0.0245 |         -8.6876 |         0      |        0      |        0.4515 |
| 1_yield_funded_calls | m=0.5 daily bm=3.0                      |      102 |      -0.0286 |         -0.0736 |         -8.6876 |        -0.0093 |       -0.0002 |        0.4514 |
| 1_yield_funded_calls | m=0.5 event_only bm=3.0                 |      102 |       0.0362 |         -0.0088 |         -4.6507 |        -0.0002 |       -0.0002 |        0.2092 |
| 1_yield_funded_calls | m=0.5 bank_event bm=1.0                 |      102 |       0.0097 |         -0.0353 |         -4.2627 |        -0.0021 |       -0.0021 |        0.1748 |
| 1_yield_funded_calls | m=1.0 daily bm=1.0                      |       97 |       0.0316 |         -0.0134 |         -2.3302 |         0      |        0      |        0.6904 |
| 1_yield_funded_calls | m=1.0 daily bm=3.0                      |       97 |       0.0032 |         -0.0418 |         -2.3302 |        -0.0092 |       -0.0002 |        0.6904 |
| 1_yield_funded_calls | m=1.0 event_only bm=3.0                 |       97 |       0.0373 |         -0.0077 |         -4.8804 |        -0.0004 |       -0.0002 |        0      |
| 1_yield_funded_calls | m=1.0 bank_event bm=1.0                 |       97 |       0.0117 |         -0.0333 |         -3.7674 |        -0.0028 |       -0.0028 |        0      |
| 1_yield_funded_calls | m=1.5 daily bm=1.0                      |       94 |       0.0238 |         -0.0212 |         -3.8901 |         0      |        0      |        0.5218 |
| 1_yield_funded_calls | m=1.5 daily bm=3.0                      |       94 |      -0.0194 |         -0.0644 |         -3.8901 |        -0.0082 |       -0.0002 |        0.5218 |
| 1_yield_funded_calls | m=1.5 event_only bm=3.0                 |       94 |       0.037  |         -0.008  |         -4.962  |        -0.0004 |       -0.0002 |        0      |
| 1_yield_funded_calls | m=1.5 bank_event bm=1.0                 |       94 |       0.0072 |         -0.0378 |         -3.8094 |        -0.0031 |       -0.0031 |        0      |
| 3_short_premium      | m=1.5 wing=2.5 frac=0.25 skip_ev=False  |       13 |       0.0273 |         -0.0177 |        -12.5638 |        -0.0001 |       -0.0001 |      nan      |
| 3_short_premium      | m=1.5 wing=2.5 frac=0.5 skip_ev=False   |       13 |       0.0088 |         -0.0362 |        -12.5638 |        -0.0003 |       -0.0002 |      nan      |
| 3_short_premium      | m=1.5 wing=2.5 frac=0.5 skip_ev=True    |       13 |       0.0191 |         -0.0259 |        -11.1021 |        -0.0002 |       -0.0002 |      nan      |
| 3_short_premium      | m=1.5 wing=None frac=0.25 skip_ev=False |       61 |       0.0632 |          0.0182 |          1.7226 |        -0.0024 |       -0.0024 |      nan      |
| 3_short_premium      | m=1.5 wing=None frac=0.5 skip_ev=False  |       61 |       0.0805 |          0.0355 |          1.7226 |        -0.0054 |       -0.005  |      nan      |
| 3_short_premium      | m=1.5 wing=None frac=0.5 skip_ev=True   |       61 |       0.0685 |          0.0235 |          1.1362 |        -0.0056 |       -0.005  |      nan      |
| 3_short_premium      | m=2.0 wing=None frac=0.25 skip_ev=False |       41 |       0.0623 |          0.0173 |         18.0862 |         0      |        0.0001 |      nan      |
| 3_short_premium      | m=2.0 wing=None frac=0.5 skip_ev=False  |       41 |       0.0788 |          0.0338 |         18.0862 |        -0      |       -0      |      nan      |
| 3_short_premium      | m=2.0 wing=None frac=0.5 skip_ev=True   |       41 |       0.0756 |          0.0306 |         16.4025 |        -0      |       -0      |      nan      |

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

### Ideas 1 / 3 on real quotes (out-of-sample after warmup)

| idea                 | params                  |   nights |   ann_return |   excess_vs_rwa |   sharpe_vs_rwa |   max_drawdown |   worst_night |   payback_ask |
|:---------------------|:------------------------|---------:|-------------:|----------------:|----------------:|---------------:|--------------:|--------------:|
| 1_yield_funded_calls | m=0.5 daily bm=1.0      |       14 |       0.0224 |         -0.0226 |         -8.8817 |         0      |        0      |        0.4927 |
| 1_yield_funded_calls | m=0.5 daily bm=3.0      |       14 |      -0.0232 |         -0.0682 |         -8.8817 |        -0.0017 |       -0.0002 |        0.4925 |
| 1_yield_funded_calls | m=0.5 event_only bm=3.0 |       14 |       0.046  |          0.001  |        nan      |         0      |        0.0001 |      nan      |
| 1_yield_funded_calls | m=0.5 bank_event bm=1.0 |       14 |       0.046  |          0.001  |        nan      |         0      |        0.0001 |      nan      |
| 1_yield_funded_calls | m=1.0 daily bm=1.0      |       19 |       0.0233 |         -0.0217 |         -5.5097 |         0      |        0      |        0.5119 |
| 1_yield_funded_calls | m=1.0 daily bm=3.0      |       19 |      -0.0207 |         -0.0657 |         -5.5097 |        -0.0027 |       -0.0002 |        0.5113 |
| 1_yield_funded_calls | m=1.0 event_only bm=3.0 |       19 |       0.0386 |         -0.0064 |         -4.383  |        -0.0002 |       -0.0002 |        0      |
| 1_yield_funded_calls | m=1.0 bank_event bm=1.0 |       19 |       0.0411 |         -0.0039 |         -4.383  |        -0.0001 |       -0.0001 |        0      |

## Monthly returns, best strategy by final NAV: BTC short m=1.5 wing=None frac=0.5 skip_ev=False

| period     |   n_days |     ret |   excess |   max_dd |   worst_day |
|:-----------|---------:|--------:|---------:|---------:|------------:|
| 2026-06-30 |       11 |  0.0028 |   0.0014 |  -0.0016 |     -0.0016 |
| 2026-07-31 |       10 |  0.0036 |   0.0024 |   0      |      0.0002 |
| 2026-08-31 |        9 |  0.0039 |   0.0028 |   0      |      0.0003 |
| 2026-09-30 |       11 |  0.0032 |   0.0019 |  -0.0005 |     -0.0005 |
| 2026-10-31 |       10 | -0.0012 |  -0.0025 |  -0.0047 |     -0.0047 |
| 2026-11-30 |       10 |  0.0002 |  -0.001  |  -0.005  |     -0.005  |