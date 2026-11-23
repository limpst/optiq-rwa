# Maker-fill backfill (resting at mid, live order books)

| strategy     | side   |   legs |   leg_fill |   pkg_fill |   hours_to_fill |   payback_mid_filled |
|:-------------|:-------|-------:|-----------:|-----------:|----------------:|---------------------:|
| short_condor | buy    |     20 |       0.65 |        0.1 |           1.909 |                    0 |
| short_condor | sell   |     20 |       0.55 |        0.1 |           1.909 |                    0 |
| yield_calls  | buy    |     13 |       1    |        1   |           2.796 |                    0 |

## yield_calls (m~1 call buy at mid) by base

| base     |   nights |   fill |    h |
|:---------|---------:|-------:|-----:|
| BTC      |        3 |      1 | 2.8  |
| BTC_USDC |        2 |      1 | 1.97 |
| ETH      |        3 |      1 | 3.06 |
| ETH_USDC |        3 |      1 | 1.14 |
| SOL_USDC |        2 |      1 | 2.35 |

## nights

| date       | strategy     | base     | side   |     m |     mid |     ask | crossed   |   hours_to_fill | package_filled   |   payback_mid |
|:-----------|:-------------|:---------|:-------|------:|--------:|--------:|:----------|----------------:|:-----------------|--------------:|
| 2026-11-20 | yield_calls  | BTC      | buy    |  1.1  |  84.187 | 104.507 | True      |           4.435 | True             |             0 |
| 2026-11-20 | yield_calls  | ETH      | buy    |  0.99 |   3.833 |   4.632 | True      |           4.071 | True             |             0 |
| 2026-11-20 | yield_calls  | ETH_USDC | buy    |  0.84 |   5.2   |   6.6   | True      |           4.071 | True             |             0 |
| 2026-11-20 | short_condor | BTC      | sell   |  1.37 |  43.545 |  58.06  | True      |           2.582 | False            |             0 |
| 2026-11-20 | short_condor | BTC      | sell   | -1.2  | 200.306 | 220.627 | True      |           8.563 | False            |             0 |
| 2026-11-20 | short_condor | BTC      | buy    |  2.46 |   3.339 |  17.418 | False     |         nan     | False            |             0 |
| 2026-11-20 | short_condor | BTC      | buy    | -2.42 |  72.575 | 104.507 | True      |           2.582 | False            |             0 |
| 2026-11-21 | yield_calls  | BTC      | buy    |  1.01 |  87.196 |  96.216 | True      |           2.796 | True             |             0 |
| 2026-11-21 | yield_calls  | BTC_USDC | buy    |  1.01 |  85     |  95     | True      |           2.796 | True             |             0 |
| 2026-11-21 | yield_calls  | ETH      | buy    |  0.89 |   4.537 |   4.873 | True      |           0.899 | True             |             0 |
| 2026-11-21 | yield_calls  | ETH_USDC | buy    |  0.87 |   4.5   |   4.8   | True      |           0.518 | True             |             0 |
| 2026-11-21 | yield_calls  | SOL_USDC | buy    |  1.13 |   0.14  |   0.21  | True      |           2.796 | True             |             0 |
| 2026-11-21 | short_condor | BTC      | sell   |  1.37 |  39.091 |  42.098 | True      |           1.655 | True             |             0 |
| 2026-11-21 | short_condor | BTC      | sell   | -1.64 |  60.149 |  72.179 | True      |           7.635 | True             |             0 |
| 2026-11-21 | short_condor | BTC      | buy    |  2.45 |   9.556 |  12.028 | True      |           3.941 | True             |             0 |
| 2026-11-21 | short_condor | BTC      | buy    | -2.43 |  21.056 |  24.064 | True      |           2.034 | True             |             0 |
| 2026-11-21 | short_condor | BTC_USDC | sell   |  1.37 |  37.5   |  45     | False     |         nan     | False            |             0 |
| 2026-11-21 | short_condor | BTC_USDC | sell   | -1.64 |  60     |  70     | True      |           7.277 | False            |             0 |
| 2026-11-21 | short_condor | BTC_USDC | buy    |  2.45 |   9.371 |  20     | False     |         nan     | False            |             0 |
| 2026-11-21 | short_condor | BTC_USDC | buy    | -2.42 |  25     |  35     | True      |           0.518 | False            |             0 |
| 2026-11-21 | short_condor | ETH      | sell   |  1.32 |   2.269 |   2.521 | False     |         nan     | False            |             0 |
| 2026-11-21 | short_condor | ETH      | sell   | -1.39 |   3.781 |   4.201 | False     |         nan     | False            |             0 |
| 2026-11-21 | short_condor | ETH      | buy    |  2.61 |   0.672 |   0.84  | True      |           3.561 | False            |             0 |
| 2026-11-21 | short_condor | ETH      | buy    | -2.34 |   1.428 |   1.68  | True      |           0.518 | False            |             0 |
| 2026-11-21 | short_condor | ETH_USDC | sell   |  1.31 |   2.3   |   2.6   | False     |         nan     | False            |             0 |
| 2026-11-21 | short_condor | ETH_USDC | sell   | -1.4  |   4     |   4.4   | False     |         nan     | False            |             0 |
| 2026-11-21 | short_condor | ETH_USDC | buy    |  2.59 |   0.6   |   0.8   | True      |           5.073 | False            |             0 |
| 2026-11-21 | short_condor | ETH_USDC | buy    | -2.35 |   1.5   |   2     | True      |           1.277 | False            |             0 |
| 2026-11-22 | yield_calls  | BTC      | buy    |  0.88 | 118.195 | 133.348 | True      |           1.144 | True             |           nan |
| 2026-11-22 | yield_calls  | BTC_USDC | buy    |  0.92 | 110     | 125     | True      |           1.144 | True             |           nan |
| 2026-11-22 | yield_calls  | ETH      | buy    |  0.97 |   4.022 |   4.45  | True      |           3.058 | True             |           nan |
| 2026-11-22 | yield_calls  | ETH_USDC | buy    |  0.96 |   4     |   4.4   | True      |           1.144 | True             |           nan |
| 2026-11-22 | yield_calls  | SOL_USDC | buy    |  0.81 |   0.26  |   0.33  | True      |           1.909 | True             |           nan |
| 2026-11-22 | short_condor | BTC      | sell   |  1.5  |  24.245 |  30.307 | True      |           1.909 | False            |           nan |
| 2026-11-22 | short_condor | BTC      | sell   | -1.4  | 112.208 | 121.306 | False     |         nan     | False            |           nan |
| 2026-11-22 | short_condor | BTC      | buy    |  2.39 |   3.083 |   6.065 | False     |         nan     | False            |           nan |
| 2026-11-22 | short_condor | BTC      | buy    | -2.41 |  42.459 |  48.525 | True      |           0.762 | False            |           nan |
| 2026-11-22 | short_condor | BTC_USDC | sell   |  1.55 |  25     |  30     | True      |           1.909 | False            |           nan |
| 2026-11-22 | short_condor | BTC_USDC | sell   | -1.66 |  90     | 100     | False     |         nan     | False            |           nan |
| 2026-11-22 | short_condor | BTC_USDC | buy    |  2.4  |   3.081 |  15     | False     |         nan     | False            |           nan |
| 2026-11-22 | short_condor | BTC_USDC | buy    | -2.34 |  45     |  55     | True      |           1.909 | False            |           nan |
| 2026-11-22 | short_condor | ETH      | sell   |  1.36 |   1.797 |   2.054 | True      |           1.909 | False            |           nan |
| 2026-11-22 | short_condor | ETH      | sell   | -1.48 |   4.28  |   4.622 | False     |         nan     | False            |           nan |
| 2026-11-22 | short_condor | ETH      | buy    |  2.5  |   0.262 |   0.342 | True      |           4.967 | False            |           nan |
| 2026-11-22 | short_condor | ETH      | buy    | -2.34 |   2.311 |   2.568 | True      |           1.525 | False            |           nan |
| 2026-11-22 | short_condor | ETH_USDC | sell   |  1.35 |   1.8   |   2.2   | True      |           1.909 | False            |           nan |
| 2026-11-22 | short_condor | ETH_USDC | sell   | -1.48 |   4.4   |   4.8   | False     |         nan     | False            |           nan |
| 2026-11-22 | short_condor | ETH_USDC | buy    |  2.5  |   0.264 |   0.4   | False     |         nan     | False            |           nan |
| 2026-11-22 | short_condor | ETH_USDC | buy    | -2.33 |   2.5   |   2.8   | True      |           1.525 | False            |           nan |
| 2026-11-22 | short_condor | SOL_USDC | sell   |  1.7  |   0.08  |   0.1   | True      |           1.144 | False            |           nan |
| 2026-11-22 | short_condor | SOL_USDC | sell   | -1.53 |   0.135 |   0.18  | True      |           0.381 | False            |           nan |
| 2026-11-22 | short_condor | SOL_USDC | buy    |  2.56 |   0.013 |   0.11  | False     |         nan     | False            |           nan |
| 2026-11-22 | short_condor | SOL_USDC | buy    | -2.51 |   0.041 |   0.13  | False     |         nan     | False            |           nan |