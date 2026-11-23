# Maker-fill backfill (resting at mid, live order books)

| strategy              | side   |   legs |   leg_fill |   pkg_fill |   hours_to_fill |   adverse_pct |   payback_mid_filled |
|:----------------------|:-------|-------:|-----------:|-----------:|----------------:|--------------:|---------------------:|
| short_condor          | buy    |     20 |      0.65  |      0.1   |           1.909 |         0.429 |                    0 |
| short_condor          | sell   |     20 |      0.55  |      0.1   |           1.909 |         0.293 |                    0 |
| short_condor (pegged) | buy    |     20 |      0.75  |      0.2   |           3.823 |         0.248 |                    0 |
| short_condor (pegged) | sell   |     20 |      0.85  |      0.2   |           2.677 |         0.262 |                    0 |
| yield_calls           | buy    |     13 |      1     |      1     |           2.796 |         0.259 |                    0 |
| yield_calls (pegged)  | buy    |     13 |      0.923 |      0.923 |           1.144 |         0.16  |                    0 |

## yield_calls (m~1 call buy at mid) by base

| strategy             | base     |   nights |   fill |    h |
|:---------------------|:---------|---------:|-------:|-----:|
| yield_calls          | BTC      |        3 |    1   | 2.8  |
| yield_calls          | BTC_USDC |        2 |    1   | 1.97 |
| yield_calls          | ETH      |        3 |    1   | 3.06 |
| yield_calls          | ETH_USDC |        3 |    1   | 1.14 |
| yield_calls          | SOL_USDC |        2 |    1   | 2.35 |
| yield_calls (pegged) | BTC      |        3 |    1   | 1.14 |
| yield_calls (pegged) | BTC_USDC |        2 |    1   | 1.02 |
| yield_calls (pegged) | ETH      |        3 |    1   | 2.68 |
| yield_calls (pegged) | ETH_USDC |        3 |    1   | 1.14 |
| yield_calls (pegged) | SOL_USDC |        2 |    0.5 | 1.53 |

## nights


adverse_pct = (our limit / mid at fill − 1) for buys: how far above the then-fair mid we paid; sells mirrored.

| date       | strategy              | base     | side   |     m |     mid |     ask | crossed   |   hours_to_fill |   fill_mid |   adverse_pct | package_filled   |   payback_mid |
|:-----------|:----------------------|:---------|:-------|------:|--------:|--------:|:----------|----------------:|-----------:|--------------:|:-----------------|--------------:|
| 2026-11-20 | yield_calls (pegged)  | BTC      | buy    |  1.1  |  84.187 | 104.507 | True      |           2.582 |    nan     |         1.535 | True             |             0 |
| 2026-11-20 | yield_calls           | BTC      | buy    |  1.1  |  84.187 | 104.507 | True      |           4.435 |     67.694 |         0.244 | True             |             0 |
| 2026-11-20 | yield_calls (pegged)  | ETH      | buy    |  0.99 |   3.833 |   4.632 | True      |           3.336 |    nan     |         0.205 | True             |             0 |
| 2026-11-20 | yield_calls           | ETH      | buy    |  0.99 |   3.833 |   4.632 | True      |           4.071 |      2.505 |         0.53  | True             |             0 |
| 2026-11-20 | yield_calls (pegged)  | ETH_USDC | buy    |  0.84 |   5.2   |   6.6   | True      |           3.336 |    nan     |         0.074 | True             |             0 |
| 2026-11-20 | yield_calls           | ETH_USDC | buy    |  0.84 |   5.2   |   6.6   | True      |           4.071 |      3.9   |         0.333 | True             |             0 |
| 2026-11-20 | short_condor (pegged) | BTC      | sell   |  1.37 |  43.545 |  58.06  | True      |           2.582 |    nan     |         0.284 | False            |             0 |
| 2026-11-20 | short_condor          | BTC      | sell   |  1.37 |  43.545 |  58.06  | True      |           2.582 |     55.911 |         0.284 | False            |             0 |
| 2026-11-20 | short_condor (pegged) | BTC      | sell   | -1.2  | 200.306 | 220.627 | True      |           5.515 |    nan     |         0.251 | False            |             0 |
| 2026-11-20 | short_condor          | BTC      | sell   | -1.2  | 200.306 | 220.627 | True      |           8.563 |    265.713 |         0.327 | False            |             0 |
| 2026-11-20 | short_condor (pegged) | BTC      | buy    |  2.46 |   3.339 |  17.418 | False     |         nan     |    nan     |       nan     | False            |             0 |
| 2026-11-20 | short_condor          | BTC      | buy    |  2.46 |   3.339 |  17.418 | False     |         nan     |    nan     |       nan     | False            |             0 |
| 2026-11-20 | short_condor (pegged) | BTC      | buy    | -2.42 |  72.575 | 104.507 | True      |           2.582 |    nan     |         3.929 | False            |             0 |
| 2026-11-20 | short_condor          | BTC      | buy    | -2.42 |  72.575 | 104.507 | True      |           2.582 |     14.723 |         3.929 | False            |             0 |
| 2026-11-21 | yield_calls (pegged)  | BTC      | buy    |  1.01 |  87.196 |  96.216 | True      |           0.899 |    nan     |         0.113 | True             |             0 |
| 2026-11-21 | yield_calls           | BTC      | buy    |  1.01 |  87.196 |  96.216 | True      |           2.796 |     66.057 |         0.32  | True             |             0 |
| 2026-11-21 | yield_calls (pegged)  | BTC_USDC | buy    |  1.01 |  85     |  95     | True      |           0.899 |    nan     |         0.125 | True             |             0 |
| 2026-11-21 | yield_calls           | BTC_USDC | buy    |  1.01 |  85     |  95     | True      |           2.796 |     67.5   |         0.259 | True             |             0 |
| 2026-11-21 | yield_calls (pegged)  | ETH      | buy    |  0.89 |   4.537 |   4.873 | True      |           0.899 |    nan     |         0.108 | True             |             0 |
| 2026-11-21 | yield_calls           | ETH      | buy    |  0.89 |   4.537 |   4.873 | True      |           0.899 |      3.952 |         0.148 | True             |             0 |
| 2026-11-21 | yield_calls (pegged)  | ETH_USDC | buy    |  0.87 |   4.5   |   4.8   | True      |           0.518 |    nan     |         0.175 | True             |             0 |
| 2026-11-21 | yield_calls           | ETH_USDC | buy    |  0.87 |   4.5   |   4.8   | True      |           0.518 |      4     |         0.125 | True             |             0 |
| 2026-11-21 | yield_calls (pegged)  | SOL_USDC | buy    |  1.13 |   0.14  |   0.21  | False     |         nan     |    nan     |       nan     | False            |             0 |
| 2026-11-21 | yield_calls           | SOL_USDC | buy    |  1.13 |   0.14  |   0.21  | True      |           2.796 |      0.08  |         0.75  | True             |             0 |
| 2026-11-21 | short_condor (pegged) | BTC      | sell   |  1.37 |  39.091 |  42.098 | True      |           1.655 |    nan     |         0.143 | True             |             0 |
| 2026-11-21 | short_condor          | BTC      | sell   |  1.37 |  39.091 |  42.098 | True      |           1.655 |     48.242 |         0.234 | True             |             0 |
| 2026-11-21 | short_condor (pegged) | BTC      | sell   | -1.64 |  60.149 |  72.179 | True      |           2.796 |    nan     |         0.262 | True             |             0 |
| 2026-11-21 | short_condor          | BTC      | sell   | -1.64 |  60.149 |  72.179 | True      |           7.635 |     83.028 |         0.38  | True             |             0 |
| 2026-11-21 | short_condor (pegged) | BTC      | buy    |  2.45 |   9.556 |  12.028 | True      |           3.941 |    nan     |         0.997 | True             |             0 |
| 2026-11-21 | short_condor          | BTC      | buy    |  2.45 |   9.556 |  12.028 | True      |           3.941 |      6.014 |         0.589 | True             |             0 |
| 2026-11-21 | short_condor (pegged) | BTC      | buy    | -2.43 |  21.056 |  24.064 | True      |           2.034 |    nan     |         0.399 | True             |             0 |
| 2026-11-21 | short_condor          | BTC      | buy    | -2.43 |  21.056 |  24.064 | True      |           2.034 |     15.087 |         0.396 | True             |             0 |
| 2026-11-21 | short_condor (pegged) | BTC_USDC | sell   |  1.37 |  37.5   |  45     | False     |         nan     |    nan     |       nan     | False            |             0 |
| 2026-11-21 | short_condor          | BTC_USDC | sell   |  1.37 |  37.5   |  45     | False     |         nan     |    nan     |       nan     | False            |             0 |
| 2026-11-21 | short_condor (pegged) | BTC_USDC | sell   | -1.64 |  60     |  70     | True      |           2.796 |    nan     |         0.294 | False            |             0 |
| 2026-11-21 | short_condor          | BTC_USDC | sell   | -1.64 |  60     |  70     | True      |           7.277 |     70     |         0.167 | False            |             0 |
| 2026-11-21 | short_condor (pegged) | BTC_USDC | buy    |  2.45 |   9.371 |  20     | True      |           4.699 |    nan     |         0     | False            |             0 |
| 2026-11-21 | short_condor          | BTC_USDC | buy    |  2.45 |   9.371 |  20     | False     |         nan     |    nan     |       nan     | False            |             0 |
| 2026-11-21 | short_condor (pegged) | BTC_USDC | buy    | -2.42 |  25     |  35     | True      |           0.518 |    nan     |         0.429 | False            |             0 |
| 2026-11-21 | short_condor          | BTC_USDC | buy    | -2.42 |  25     |  35     | True      |           0.518 |     17.5   |         0.429 | False            |             0 |
| 2026-11-21 | short_condor (pegged) | ETH      | sell   |  1.32 |   2.269 |   2.521 | False     |         nan     |    nan     |       nan     | False            |             0 |
| 2026-11-21 | short_condor          | ETH      | sell   |  1.32 |   2.269 |   2.521 | False     |         nan     |    nan     |       nan     | False            |             0 |
| 2026-11-21 | short_condor (pegged) | ETH      | sell   | -1.39 |   3.781 |   4.201 | True      |           2.796 |    nan     |         0.246 | False            |             0 |
| 2026-11-21 | short_condor          | ETH      | sell   | -1.39 |   3.781 |   4.201 | False     |         nan     |    nan     |       nan     | False            |             0 |
| 2026-11-21 | short_condor (pegged) | ETH      | buy    |  2.61 |   0.672 |   0.84  | True      |           4.321 |    nan     |         0.248 | False            |             0 |
| 2026-11-21 | short_condor          | ETH      | buy    |  2.61 |   0.672 |   0.84  | True      |           3.561 |      0.419 |         0.603 | False            |             0 |
| 2026-11-21 | short_condor (pegged) | ETH      | buy    | -2.34 |   1.428 |   1.68  | True      |           0.518 |    nan     |         0.542 | False            |             0 |
| 2026-11-21 | short_condor          | ETH      | buy    | -2.34 |   1.428 |   1.68  | True      |           0.518 |      0.927 |         0.542 | False            |             0 |
| 2026-11-21 | short_condor (pegged) | ETH_USDC | sell   |  1.31 |   2.3   |   2.6   | False     |         nan     |    nan     |       nan     | False            |             0 |
| 2026-11-21 | short_condor          | ETH_USDC | sell   |  1.31 |   2.3   |   2.6   | False     |         nan     |    nan     |       nan     | False            |             0 |
| 2026-11-21 | short_condor (pegged) | ETH_USDC | sell   | -1.4  |   4     |   4.4   | True      |           6.916 |    nan     |         0.375 | False            |             0 |
| 2026-11-21 | short_condor          | ETH_USDC | sell   | -1.4  |   4     |   4.4   | False     |         nan     |    nan     |       nan     | False            |             0 |
| 2026-11-21 | short_condor (pegged) | ETH_USDC | buy    |  2.59 |   0.6   |   0.8   | True      |           5.073 |    nan     |         0.167 | False            |             0 |
| 2026-11-21 | short_condor          | ETH_USDC | buy    |  2.59 |   0.6   |   0.8   | True      |           5.073 |      0.6   |         0     | False            |             0 |
| 2026-11-21 | short_condor (pegged) | ETH_USDC | buy    | -2.35 |   1.5   |   2     | True      |           8.69  |    nan     |         0     | False            |             0 |
| 2026-11-21 | short_condor          | ETH_USDC | buy    | -2.35 |   1.5   |   2     | True      |           1.277 |      1     |         0.5   | False            |             0 |
| 2026-11-22 | yield_calls (pegged)  | BTC      | buy    |  0.88 | 118.195 | 133.348 | True      |           1.144 |    nan     |         0.196 | True             |           nan |
| 2026-11-22 | yield_calls           | BTC      | buy    |  0.88 | 118.195 | 133.348 | True      |           1.144 |     93.767 |         0.261 | True             |           nan |
| 2026-11-22 | yield_calls (pegged)  | BTC_USDC | buy    |  0.92 | 110     | 125     | True      |           1.144 |    nan     |         0.154 | True             |           nan |
| 2026-11-22 | yield_calls           | BTC_USDC | buy    |  0.92 | 110     | 125     | True      |           1.144 |     97.5   |         0.128 | True             |           nan |
| 2026-11-22 | yield_calls (pegged)  | ETH      | buy    |  0.97 |   4.022 |   4.45  | True      |           2.677 |    nan     |         0.277 | True             |           nan |
| 2026-11-22 | yield_calls           | ETH      | buy    |  0.97 |   4.022 |   4.45  | True      |           3.058 |      3.591 |         0.12  | True             |           nan |
| 2026-11-22 | yield_calls (pegged)  | ETH_USDC | buy    |  0.96 |   4     |   4.4   | True      |           1.144 |    nan     |         0.086 | True             |           nan |
| 2026-11-22 | yield_calls           | ETH_USDC | buy    |  0.96 |   4     |   4.4   | True      |           1.144 |      3.5   |         0.143 | True             |           nan |
| 2026-11-22 | yield_calls (pegged)  | SOL_USDC | buy    |  0.81 |   0.26  |   0.33  | True      |           1.525 |    nan     |         0.167 | True             |           nan |
| 2026-11-22 | yield_calls           | SOL_USDC | buy    |  0.81 |   0.26  |   0.33  | True      |           1.909 |      0.185 |         0.405 | True             |           nan |
| 2026-11-22 | short_condor (pegged) | BTC      | sell   |  1.5  |  24.245 |  30.307 | True      |           1.525 |    nan     |         0.34  | False            |           nan |
| 2026-11-22 | short_condor          | BTC      | sell   |  1.5  |  24.245 |  30.307 | True      |           1.909 |     33.467 |         0.38  | False            |           nan |
| 2026-11-22 | short_condor (pegged) | BTC      | sell   | -1.4  | 112.208 | 121.306 | True      |           1.144 |    nan     |         0.216 | False            |           nan |
| 2026-11-22 | short_condor          | BTC      | sell   | -1.4  | 112.208 | 121.306 | False     |         nan     |    nan     |       nan     | False            |           nan |
| 2026-11-22 | short_condor (pegged) | BTC      | buy    |  2.39 |   3.083 |   6.065 | False     |         nan     |    nan     |       nan     | False            |           nan |
| 2026-11-22 | short_condor          | BTC      | buy    |  2.39 |   3.083 |   6.065 | False     |         nan     |    nan     |       nan     | False            |           nan |
| 2026-11-22 | short_condor (pegged) | BTC      | buy    | -2.41 |  42.459 |  48.525 | True      |           4.204 |    nan     |         0.491 | False            |           nan |
| 2026-11-22 | short_condor          | BTC      | buy    | -2.41 |  42.459 |  48.525 | True      |           0.762 |     36.382 |         0.167 | False            |           nan |
| 2026-11-22 | short_condor (pegged) | BTC_USDC | sell   |  1.55 |  25     |  30     | True      |           8.062 |    nan     |         1     | False            |           nan |
| 2026-11-22 | short_condor          | BTC_USDC | sell   |  1.55 |  25     |  30     | True      |           1.909 |     32.5   |         0.3   | False            |           nan |
| 2026-11-22 | short_condor (pegged) | BTC_USDC | sell   | -1.66 |  90     | 100     | True      |           7.381 |    nan     |         0.571 | False            |           nan |
| 2026-11-22 | short_condor          | BTC_USDC | sell   | -1.66 |  90     | 100     | False     |         nan     |    nan     |       nan     | False            |           nan |
| 2026-11-22 | short_condor (pegged) | BTC_USDC | buy    |  2.4  |   3.081 |  15     | False     |         nan     |    nan     |       nan     | False            |           nan |
| 2026-11-22 | short_condor          | BTC_USDC | buy    |  2.4  |   3.081 |  15     | False     |         nan     |    nan     |       nan     | False            |           nan |
| 2026-11-22 | short_condor (pegged) | BTC_USDC | buy    | -2.34 |  45     |  55     | True      |           1.909 |    nan     |         0.231 | False            |           nan |
| 2026-11-22 | short_condor          | BTC_USDC | buy    | -2.34 |  45     |  55     | True      |           1.909 |     32.5   |         0.385 | False            |           nan |
| 2026-11-22 | short_condor (pegged) | ETH      | sell   |  1.36 |   1.797 |   2.054 | True      |           1.909 |    nan     |         0.23  | True             |           nan |
| 2026-11-22 | short_condor          | ETH      | sell   |  1.36 |   1.797 |   2.054 | True      |           1.909 |      2.324 |         0.293 | False            |           nan |
| 2026-11-22 | short_condor (pegged) | ETH      | sell   | -1.48 |   4.28  |   4.622 | True      |           2.677 |    nan     |         0.157 | True             |           nan |
| 2026-11-22 | short_condor          | ETH      | sell   | -1.48 |   4.28  |   4.622 | False     |         nan     |    nan     |       nan     | False            |           nan |
| 2026-11-22 | short_condor (pegged) | ETH      | buy    |  2.5  |   0.262 |   0.342 | True      |           4.967 |    nan     |         0.522 | True             |           nan |
| 2026-11-22 | short_condor          | ETH      | buy    |  2.5  |   0.262 |   0.342 | True      |           4.967 |      0.172 |         0.522 | False            |           nan |
| 2026-11-22 | short_condor (pegged) | ETH      | buy    | -2.34 |   2.311 |   2.568 | True      |           3.823 |    nan     |         0.189 | True             |           nan |
| 2026-11-22 | short_condor          | ETH      | buy    | -2.34 |   2.311 |   2.568 | True      |           1.525 |      1.976 |         0.17  | False            |           nan |
| 2026-11-22 | short_condor (pegged) | ETH_USDC | sell   |  1.35 |   1.8   |   2.2   | True      |           1.909 |    nan     |         0.222 | False            |           nan |
| 2026-11-22 | short_condor          | ETH_USDC | sell   |  1.35 |   1.8   |   2.2   | True      |           1.909 |      2.2   |         0.222 | False            |           nan |
| 2026-11-22 | short_condor (pegged) | ETH_USDC | sell   | -1.48 |   4.4   |   4.8   | True      |           2.677 |    nan     |         0.152 | False            |           nan |
| 2026-11-22 | short_condor          | ETH_USDC | sell   | -1.48 |   4.4   |   4.8   | False     |         nan     |    nan     |       nan     | False            |           nan |
| 2026-11-22 | short_condor (pegged) | ETH_USDC | buy    |  2.5  |   0.264 |   0.4   | False     |         nan     |    nan     |       nan     | False            |           nan |
| 2026-11-22 | short_condor          | ETH_USDC | buy    |  2.5  |   0.264 |   0.4   | False     |         nan     |    nan     |       nan     | False            |           nan |
| 2026-11-22 | short_condor (pegged) | ETH_USDC | buy    | -2.33 |   2.5   |   2.8   | True      |           1.525 |    nan     |         0.211 | False            |           nan |
| 2026-11-22 | short_condor          | ETH_USDC | buy    | -2.33 |   2.5   |   2.8   | True      |           1.525 |      1.9   |         0.316 | False            |           nan |
| 2026-11-22 | short_condor (pegged) | SOL_USDC | sell   |  1.7  |   0.08  |   0.1   | True      |           1.144 |    nan     |         0.267 | False            |           nan |
| 2026-11-22 | short_condor          | SOL_USDC | sell   |  1.7  |   0.08  |   0.1   | True      |           1.144 |      0.095 |         0.188 | False            |           nan |
| 2026-11-22 | short_condor (pegged) | SOL_USDC | sell   | -1.53 |   0.135 |   0.18  | True      |           0.381 |    nan     |         0.444 | False            |           nan |
| 2026-11-22 | short_condor          | SOL_USDC | sell   | -1.53 |   0.135 |   0.18  | True      |           0.381 |      0.195 |         0.444 | False            |           nan |
| 2026-11-22 | short_condor (pegged) | SOL_USDC | buy    |  2.56 |   0.013 |   0.11  | False     |         nan     |    nan     |       nan     | False            |           nan |
| 2026-11-22 | short_condor          | SOL_USDC | buy    |  2.56 |   0.013 |   0.11  | False     |         nan     |    nan     |       nan     | False            |           nan |
| 2026-11-22 | short_condor (pegged) | SOL_USDC | buy    | -2.51 |   0.041 |   0.13  | True      |           2.677 |    nan     |         0     | False            |           nan |
| 2026-11-22 | short_condor          | SOL_USDC | buy    | -2.51 |   0.041 |   0.13  | False     |         nan     |    nan     |       nan     | False            |           nan |