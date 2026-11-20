# Sweep summary (seed-averaged, out-of-sample nights)


## Scenario: base

| idea                  | params                                                       |   ann_return |   excess_vs_rwa |   ann_vol |   sharpe_vs_rwa |   max_drawdown |   cvar5_night |   seed_min_ret |
|:----------------------|:-------------------------------------------------------------|-------------:|----------------:|----------:|----------------:|---------------:|--------------:|---------------:|
| 0_rwa_only            | {}                                                           |       0.046  |          0.001  |    0      |        nan      |         0      |        0.0001 |         0.046  |
| 1_yield_funded_calls  | {'m': 1.0, 'mode': 'event_only', 'budget_mult': 3.0}         |       0.0574 |          0.0124 |    0.011  |          0.9528 |        -0.0006 |       -0.0002 |         0.0536 |
| 2_qubo_event_selector | {'solver': 'greedy', 'lam': 0.0, 'budget_mult': 1.0}         |       0.0473 |          0.0023 |    0.0121 |          0.1802 |        -0.0005 |       -0.0001 |         0.042  |
| 3_short_premium       | {'m': 1.0, 'frac': 0.5, 'skip_events': True, 'wing_m': None} |      -0.0181 |         -0.0631 |    0.0699 |         -0.8699 |        -0.0947 |       -0.0123 |        -0.0349 |


## Scenario: events_underpriced

| idea                  | params                                                       |   ann_return |   excess_vs_rwa |   ann_vol |   sharpe_vs_rwa |   max_drawdown |   cvar5_night |   seed_min_ret |
|:----------------------|:-------------------------------------------------------------|-------------:|----------------:|----------:|----------------:|---------------:|--------------:|---------------:|
| 0_rwa_only            | {}                                                           |       0.046  |          0.001  |    0      |        nan      |         0      |        0.0001 |         0.046  |
| 1_yield_funded_calls  | {'m': 0.5, 'mode': 'event_only', 'budget_mult': 1.0}         |       0.0511 |          0.0061 |    0.0028 |          1.6969 |         0      |        0      |         0.0501 |
| 2_qubo_event_selector | {'solver': 'greedy', 'lam': 0.5, 'budget_mult': 1.0}         |       0.069  |          0.024  |    0.0155 |          1.3602 |        -0.0005 |       -0.0002 |         0.0603 |
| 3_short_premium       | {'m': 1.0, 'frac': 0.5, 'skip_events': True, 'wing_m': None} |       0.0558 |          0.0108 |    0.0679 |          0.1708 |        -0.0677 |       -0.0117 |         0.0394 |


## Scenario: fair_iv

| idea                  | params                                                       |   ann_return |   excess_vs_rwa |   ann_vol |   sharpe_vs_rwa |   max_drawdown |   cvar5_night |   seed_min_ret |
|:----------------------|:-------------------------------------------------------------|-------------:|----------------:|----------:|----------------:|---------------:|--------------:|---------------:|
| 0_rwa_only            | {}                                                           |       0.046  |          0.001  |    0      |        nan      |         0      |        0.0001 |         0.046  |
| 1_yield_funded_calls  | {'m': 1.5, 'mode': 'event_only', 'budget_mult': 1.0}         |       0.05   |          0.005  |    0.0056 |          0.6474 |         0      |        0      |         0.0475 |
| 2_qubo_event_selector | {'solver': 'greedy', 'lam': 0.5, 'budget_mult': 1.0}         |       0.0431 |         -0.0019 |    0.0072 |         -0.2302 |        -0.0004 |       -0.0001 |         0.0364 |
| 3_short_premium       | {'m': 1.0, 'frac': 0.5, 'skip_events': True, 'wing_m': None} |      -0.09   |         -0.135  |    0.072  |         -1.9004 |        -0.1884 |       -0.0129 |        -0.1066 |


## Scenario: rich_iv

| idea                  | params                                                        |   ann_return |   excess_vs_rwa |   ann_vol |   sharpe_vs_rwa |   max_drawdown |   cvar5_night |   seed_min_ret |
|:----------------------|:--------------------------------------------------------------|-------------:|----------------:|----------:|----------------:|---------------:|--------------:|---------------:|
| 0_rwa_only            | {}                                                            |       0.046  |          0.001  |    0      |        nan      |         0      |        0.0001 |         0.046  |
| 1_yield_funded_calls  | {'m': 1.5, 'mode': 'bank_event', 'budget_mult': 3.0}          |       0.0853 |          0.0403 |    0.207  |         -0.2059 |        -0.0861 |       -0.0047 |        -0.0354 |
| 2_qubo_event_selector | {'solver': 'greedy', 'lam': 0.0, 'budget_mult': 1.0}          |       0.0419 |         -0.0031 |    0.0009 |         -3.6286 |        -0.0001 |        0      |         0.0356 |
| 3_short_premium       | {'m': 1.0, 'frac': 1.0, 'skip_events': False, 'wing_m': None} |       0.5339 |          0.4889 |    0.1607 |          2.4729 |        -0.1386 |       -0.0261 |         0.5095 |


## Idea 2 - QUBO solver comparison (SA vs greedy)

| scenario           | params                                               |   ann_return |   excess_vs_rwa |   sharpe_vs_rwa |   payback_ask |
|:-------------------|:-----------------------------------------------------|-------------:|----------------:|----------------:|--------------:|
| base               | {'solver': 'greedy', 'lam': 0.0, 'budget_mult': 1.0} |       0.0473 |          0.0023 |          0.1802 |        2.7561 |
| base               | {'solver': 'greedy', 'lam': 0.5, 'budget_mult': 1.0} |       0.0467 |          0.0017 |          0.0793 |        1.4215 |
| base               | {'solver': 'sa', 'lam': 0.5, 'budget_mult': 1.0}     |       0.0435 |         -0.0015 |         -0.2801 |        0.9481 |
| events_underpriced | {'solver': 'greedy', 'lam': 0.0, 'budget_mult': 1.0} |       0.0795 |          0.0345 |          1.2185 |        2.5908 |
| events_underpriced | {'solver': 'greedy', 'lam': 0.5, 'budget_mult': 1.0} |       0.069  |          0.024  |          1.3602 |        2.2591 |
| events_underpriced | {'solver': 'sa', 'lam': 0.5, 'budget_mult': 1.0}     |       0.0528 |          0.0078 |          0.6472 |        1.1494 |
| fair_iv            | {'solver': 'greedy', 'lam': 0.0, 'budget_mult': 1.0} |       0.0421 |         -0.0029 |         -1.0192 |        0.7459 |
| fair_iv            | {'solver': 'greedy', 'lam': 0.5, 'budget_mult': 1.0} |       0.0431 |         -0.0019 |         -0.2302 |        1.1543 |
| fair_iv            | {'solver': 'sa', 'lam': 0.5, 'budget_mult': 1.0}     |       0.0415 |         -0.0035 |         -0.8932 |        0.8995 |
| rich_iv            | {'solver': 'greedy', 'lam': 0.0, 'budget_mult': 1.0} |       0.0419 |         -0.0031 |         -3.6286 |        0.3235 |
| rich_iv            | {'solver': 'greedy', 'lam': 0.5, 'budget_mult': 1.0} |       0.0449 |         -0.0001 |         -5.3518 |        0      |
| rich_iv            | {'solver': 'sa', 'lam': 0.5, 'budget_mult': 1.0}     |       0.0301 |         -0.0149 |         -3.8031 |        0.6333 |

## Idea 5 - perp vs daily call ($1 at risk per trade, base scenario)

| scenario   | nights   | instrument        |   mean_ret |   p_profit |   p_lose_all |   liquidation_rate |   cvar5 |
|:-----------|:---------|:------------------|-----------:|-----------:|-------------:|-------------------:|--------:|
| base       | all      | perp 10x          |     -0.007 |      0.473 |        0.004 |              0.004 |   -0.57 |
| base       | all      | perp 25x          |     -0.011 |      0.472 |        0.099 |              0.099 |   -1    |
| base       | all      | perp 50x          |     -0.006 |      0.439 |        0.35  |              0.35  |   -1    |
| base       | all      | perp 100x         |     -0.037 |      0.301 |        0.659 |              0.659 |   -1    |
| base       | all      | daily call m=+0.0 |     -0.108 |      0.305 |        0.508 |            nan     |   -1    |
| base       | all      | daily call m=+1.0 |     -0.148 |      0.122 |        0.855 |            nan     |   -1    |
| base       | event    | perp 10x          |      0.025 |      0.514 |        0.016 |              0.016 |   -0.78 |
| base       | event    | perp 25x          |      0.09  |      0.506 |        0.203 |              0.203 |   -1    |
| base       | event    | perp 50x          |      0.242 |      0.45  |        0.451 |              0.451 |   -1    |
| base       | event    | perp 100x         |      0.415 |      0.3   |        0.682 |              0.682 |   -1    |
| base       | event    | daily call m=+0.0 |      0.217 |      0.373 |        0.475 |            nan     |   -1    |
| base       | event    | daily call m=+1.0 |      0.597 |      0.175 |        0.796 |            nan     |   -1    |

## Idea 4 - calibration, calls (base scenario)

| scenario   | kind   |   m | event   |   p_itm_model |   p_itm_emp |   p_be_model |   p_be_emp |   payback_mid |   payback_ask |
|:-----------|:-------|----:|:--------|--------------:|------------:|-------------:|-----------:|--------------:|--------------:|
| base       | call   | 0   | False   |         0.496 |       0.487 |        0.324 |      0.295 |         0.948 |         0.844 |
| base       | call   | 0   | True    |         0.494 |       0.525 |        0.323 |      0.373 |         1.374 |         1.23  |
| base       | call   | 0.5 | False   |         0.309 |       0.276 |        0.233 |      0.203 |         0.903 |         0.788 |
| base       | call   | 0.5 | True    |         0.307 |       0.353 |        0.233 |      0.273 |         1.56  |         1.377 |
| base       | call   | 1   | False   |         0.168 |       0.136 |        0.142 |      0.114 |         0.889 |         0.743 |
| base       | call   | 1   | True    |         0.166 |       0.204 |        0.142 |      0.175 |         1.92  |         1.641 |
| base       | call   | 1.5 | False   |         0.08  |       0.058 |        0.073 |      0.052 |         0.968 |         0.728 |
| base       | call   | 1.5 | True    |         0.079 |       0.107 |        0.072 |      0.097 |         2.683 |         2.118 |
| base       | call   | 2   | False   |         0.034 |       0.022 |        0.032 |      0.022 |         1.296 |         0.763 |
| base       | call   | 2   | True    |         0.033 |       0.058 |        0.032 |      0.055 |         4.299 |         2.793 |