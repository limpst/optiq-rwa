# Sweep summary (seed-averaged, out-of-sample nights)

Cost models: none / base (Deribit fee 0.03% notional, cap 12.5% of price; daily settlement exempt) / stress (2x spread, +50% slippage, settlement fee on). SR = Sharpe vs 0, IR = vs RWA 4.5%, DSR = deflated Sharpe on the excess over RWA; trials N = parameter configs of the same idea in one scenario x cost model x seed search. **bold** = highlight rule SR > 0.0, IR > 0.5, MDD >= -15%, DSR >= 0.95, nights >= 60 (seed-averaged metrics).

Highlighted configs: 8 of 576 (scenario x cost model x config).

| scenario           | cost_model   | idea                  | params                                               |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |    dsr |   seed_min_ret |   n_nights |
|:-------------------|:-------------|:----------------------|:-----------------------------------------------------|-------------:|----------------:|---------:|------------:|---------------:|-------:|---------------:|-----------:|
| events_underpriced | base         | 2_qubo_event_selector | {'solver': 'greedy', 'lam': 0.0, 'budget_mult': 1.0} |       0.073  |          0.028  |   3.1636 |      1.1166 |        -0.0005 | 0.9896 |         0.0643 |        700 |
| events_underpriced | base         | 2_qubo_event_selector | {'solver': 'greedy', 'lam': 0.5, 'budget_mult': 1.0} |       0.064  |          0.019  |   4.6518 |      1.1588 |        -0.0005 | 0.983  |         0.0563 |        700 |
| events_underpriced | base         | 2_qubo_event_selector | {'solver': 'milp', 'lam': 0.5, 'budget_mult': 1.0}   |       0.0576 |          0.0126 |   6.4238 |      1.0864 |        -0.0005 | 0.9581 |         0.0517 |        700 |
| events_underpriced | base         | 2_qubo_event_selector | {'solver': 'sa', 'lam': 0.5, 'budget_mult': 1.0}     |       0.0572 |          0.0122 |   6.3914 |      1.0538 |        -0.0005 | 0.9504 |         0.0517 |        700 |
| events_underpriced | none         | 2_qubo_event_selector | {'solver': 'greedy', 'lam': 0.0, 'budget_mult': 1.0} |       0.0794 |          0.0344 |   3.0402 |      1.2238 |        -0.0005 | 0.997  |         0.07   |        700 |
| events_underpriced | none         | 2_qubo_event_selector | {'solver': 'greedy', 'lam': 0.5, 'budget_mult': 1.0} |       0.0688 |          0.0238 |   4.4699 |      1.3398 |        -0.0005 | 0.9977 |         0.0603 |        700 |
| events_underpriced | none         | 2_qubo_event_selector | {'solver': 'milp', 'lam': 0.5, 'budget_mult': 1.0}   |       0.0603 |          0.0153 |   6.0635 |      1.249  |        -0.0005 | 0.9864 |         0.0536 |        700 |
| events_underpriced | none         | 2_qubo_event_selector | {'solver': 'sa', 'lam': 0.5, 'budget_mult': 1.0}     |       0.0599 |          0.0149 |   6.0103 |      1.2091 |        -0.0005 | 0.9814 |         0.0536 |        700 |

## Scenario: base - cost model: none

| idea                  | params                                                       |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |      dsr |   seed_min_ret |   n_nights |
|:----------------------|:-------------------------------------------------------------|-------------:|----------------:|---------:|------------:|---------------:|---------:|---------------:|-----------:|
| 0_rwa_only            | {}                                                           |       0.046  |          0.001  | nan      |    nan      |         0      | nan      |         0.046  |        700 |
| 1_yield_funded_calls  | {'m': 1.0, 'mode': 'event_only', 'budget_mult': 3.0}         |       0.0574 |          0.0124 |   5.1315 |      0.9528 |        -0.0006 |   0.0759 |         0.0536 |        700 |
| 2_qubo_event_selector | {'solver': 'greedy', 'lam': 0.0, 'budget_mult': 1.0}         |       0.0466 |          0.0016 |   4.1061 |      0.1262 |        -0.0005 |   0.5239 |         0.0405 |        700 |
| 3_short_premium       | {'m': 1.0, 'frac': 0.5, 'skip_events': True, 'wing_m': None} |      -0.0181 |         -0.0631 |  -0.2261 |     -0.8699 |        -0.0947 |   0      |        -0.0349 |        700 |


## Scenario: events_underpriced - cost model: none

| idea                      | params                                                       |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |      dsr |   seed_min_ret |   n_nights |
|:--------------------------|:-------------------------------------------------------------|-------------:|----------------:|---------:|------------:|---------------:|---------:|---------------:|-----------:|
| 0_rwa_only                | {}                                                           |       0.046  |          0.001  | nan      |    nan      |         0      | nan      |         0.046  |        700 |
| 1_yield_funded_calls      | {'m': 0.5, 'mode': 'event_only', 'budget_mult': 1.0}         |       0.0511 |          0.0061 |  17.8552 |      1.6969 |         0      |   0.2039 |         0.0501 |        700 |
| **2_qubo_event_selector** | {'solver': 'greedy', 'lam': 0.5, 'budget_mult': 1.0}         |       0.0688 |          0.0238 |   4.4699 |      1.3398 |        -0.0005 |   0.9977 |         0.0603 |        700 |
| 3_short_premium           | {'m': 1.0, 'frac': 0.5, 'skip_events': True, 'wing_m': None} |       0.0558 |          0.0108 |   0.8335 |      0.1708 |        -0.0677 |   0      |         0.0394 |        700 |


## Scenario: fair_iv - cost model: none

| idea                  | params                                                       |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |      dsr |   seed_min_ret |   n_nights |
|:----------------------|:-------------------------------------------------------------|-------------:|----------------:|---------:|------------:|---------------:|---------:|---------------:|-----------:|
| 0_rwa_only            | {}                                                           |       0.046  |          0.001  | nan      |    nan      |         0      | nan      |         0.046  |        700 |
| 1_yield_funded_calls  | {'m': 1.5, 'mode': 'event_only', 'budget_mult': 1.0}         |       0.05   |          0.005  |   9.0187 |      0.6474 |         0      |   0.1614 |         0.0475 |        700 |
| 2_qubo_event_selector | {'solver': 'greedy', 'lam': 0.5, 'budget_mult': 1.0}         |       0.0437 |         -0.0013 |  12.3453 |     -0.1722 |        -0.0005 |   0.2112 |         0.0374 |        700 |
| 3_short_premium       | {'m': 1.0, 'frac': 0.5, 'skip_events': True, 'wing_m': None} |      -0.09   |         -0.135  |  -1.275  |     -1.9004 |        -0.1884 |   0      |        -0.1066 |        700 |


## Scenario: rich_iv - cost model: none

| idea                  | params                                                        |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |      dsr |   seed_min_ret |   n_nights |
|:----------------------|:--------------------------------------------------------------|-------------:|----------------:|---------:|------------:|---------------:|---------:|---------------:|-----------:|
| 0_rwa_only            | {}                                                            |       0.046  |          0.001  | nan      |    nan      |         0      | nan      |         0.046  |        700 |
| 1_yield_funded_calls  | {'m': 1.5, 'mode': 'bank_event', 'budget_mult': 3.0}          |       0.0853 |          0.0403 |   0.2039 |     -0.2059 |        -0.0861 |   0.0003 |        -0.0354 |        700 |
| 2_qubo_event_selector | {'solver': 'greedy', 'lam': 0.0, 'budget_mult': 1.0}          |       0.0419 |         -0.0031 |  33.1038 |     -3.6287 |        -0.0002 |   0.0193 |         0.0356 |        700 |
| 3_short_premium       | {'m': 1.0, 'frac': 1.0, 'skip_events': False, 'wing_m': None} |       0.5339 |          0.4889 |   2.7534 |      2.4729 |        -0.1386 |   0.0288 |         0.5095 |        700 |


## Scenario: base - cost model: base

| idea                  | params                                                       |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |      dsr |   seed_min_ret |   n_nights |
|:----------------------|:-------------------------------------------------------------|-------------:|----------------:|---------:|------------:|---------------:|---------:|---------------:|-----------:|
| 0_rwa_only            | {}                                                           |       0.046  |          0.001  | nan      |    nan      |         0      | nan      |         0.046  |        700 |
| 1_yield_funded_calls  | {'m': 1.5, 'mode': 'event_only', 'budget_mult': 3.0}         |       0.0612 |          0.0162 |   3.5288 |      0.816  |        -0.0007 |   0.0032 |         0.0542 |        700 |
| 2_qubo_event_selector | {'solver': 'greedy', 'lam': 0.0, 'budget_mult': 1.0}         |       0.0435 |         -0.0015 |   4.3518 |     -0.1177 |        -0.0005 |   0.4268 |         0.0361 |        700 |
| 3_short_premium       | {'m': 1.0, 'frac': 0.5, 'skip_events': True, 'wing_m': None} |      -0.0795 |         -0.1245 |  -1.1488 |     -1.7921 |        -0.1712 |   0      |        -0.0946 |        700 |


## Scenario: events_underpriced - cost model: base

| idea                      | params                                                       |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |      dsr |   seed_min_ret |   n_nights |
|:--------------------------|:-------------------------------------------------------------|-------------:|----------------:|---------:|------------:|---------------:|---------:|---------------:|-----------:|
| 0_rwa_only                | {}                                                           |       0.046  |          0.001  | nan      |    nan      |         0      | nan      |         0.046  |        700 |
| 1_yield_funded_calls      | {'m': 0.5, 'mode': 'event_only', 'budget_mult': 1.0}         |       0.0506 |          0.0056 |  18.6268 |      1.5801 |         0      |   0.0408 |         0.0496 |        700 |
| **2_qubo_event_selector** | {'solver': 'greedy', 'lam': 0.5, 'budget_mult': 1.0}         |       0.064  |          0.019  |   4.6518 |      1.1588 |        -0.0005 |   0.983  |         0.0563 |        700 |
| 3_short_premium           | {'m': 1.0, 'frac': 0.5, 'skip_events': True, 'wing_m': None} |      -0.0131 |         -0.0581 |  -0.1592 |     -0.8217 |        -0.0872 |   0      |        -0.0277 |        700 |


## Scenario: fair_iv - cost model: base

| idea                  | params                                                       |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |      dsr |   seed_min_ret |   n_nights |
|:----------------------|:-------------------------------------------------------------|-------------:|----------------:|---------:|------------:|---------------:|---------:|---------------:|-----------:|
| 0_rwa_only            | {}                                                           |       0.046  |          0.001  | nan      |    nan      |         0      | nan      |         0.046  |        700 |
| 1_yield_funded_calls  | {'m': 0.0, 'mode': 'bank_event', 'budget_mult': 1.0}         |       0.058  |          0.013  |   3.3473 |      0.5346 |        -0.0029 |   0.0493 |         0.0474 |        700 |
| 2_qubo_event_selector | {'solver': 'greedy', 'lam': 0.5, 'budget_mult': 1.0}         |       0.041  |         -0.004  |  13.6049 |     -0.4922 |        -0.0005 |   0.1119 |         0.0343 |        700 |
| 3_short_premium       | {'m': 1.5, 'frac': 0.5, 'skip_events': True, 'wing_m': None} |      -0.0943 |         -0.1393 |  -1.8182 |     -2.6574 |        -0.1866 |   0      |        -0.1012 |        700 |


## Scenario: rich_iv - cost model: base

| idea                  | params                                                        |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |      dsr |   seed_min_ret |   n_nights |
|:----------------------|:--------------------------------------------------------------|-------------:|----------------:|---------:|------------:|---------------:|---------:|---------------:|-----------:|
| 0_rwa_only            | {}                                                            |       0.046  |          0.001  | nan      |    nan      |         0      | nan      |         0.046  |        700 |
| 1_yield_funded_calls  | {'m': 1.5, 'mode': 'bank_event', 'budget_mult': 1.0}          |       0.0575 |          0.0125 |   1.0195 |     -0.3287 |        -0.004  |   0.0001 |         0.0168 |        700 |
| 2_qubo_event_selector | {'solver': 'greedy', 'lam': 0.0, 'budget_mult': 1.0}          |       0.0418 |         -0.0032 |  34.393  |     -3.9657 |        -0.0002 |   0.0153 |         0.0354 |        700 |
| 3_short_premium       | {'m': 1.0, 'frac': 1.0, 'skip_events': False, 'wing_m': None} |       0.2895 |          0.2445 |   1.6714 |      1.3908 |        -0.1476 |   0      |         0.2714 |        700 |


## Scenario: base - cost model: stress

| idea                  | params                                                       |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |      dsr |   seed_min_ret |   n_nights |
|:----------------------|:-------------------------------------------------------------|-------------:|----------------:|---------:|------------:|---------------:|---------:|---------------:|-----------:|
| 0_rwa_only            | {}                                                           |       0.046  |          0.001  | nan      |    nan      |         0      | nan      |         0.046  |        700 |
| 1_yield_funded_calls  | {'m': 1.5, 'mode': 'bank_event', 'budget_mult': 1.0}         |       0.0947 |          0.0497 |   1.3396 |      0.4462 |        -0.004  |   0      |         0.0455 |        700 |
| 2_qubo_event_selector | {'solver': 'sa', 'lam': 0.5, 'budget_mult': 1.0}             |       0.0421 |         -0.0029 |  33.3829 |     -0.898  |        -0.0003 |   0.1276 |         0.0398 |        700 |
| 3_short_premium       | {'m': 2.0, 'frac': 0.5, 'skip_events': True, 'wing_m': None} |      -0.0794 |         -0.1244 |  -2.1816 |     -3.3787 |        -0.1507 |   0      |        -0.0879 |        700 |


## Scenario: events_underpriced - cost model: stress

| idea                  | params                                                       |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |      dsr |   seed_min_ret |   n_nights |
|:----------------------|:-------------------------------------------------------------|-------------:|----------------:|---------:|------------:|---------------:|---------:|---------------:|-----------:|
| 0_rwa_only            | {}                                                           |       0.046  |          0.001  | nan      |    nan      |         0      | nan      |         0.046  |        700 |
| 1_yield_funded_calls  | {'m': 1.0, 'mode': 'event_only', 'budget_mult': 3.0}         |       0.0582 |          0.0132 |   5.59   |      1.1054 |        -0.0006 |   0      |         0.0548 |        700 |
| 2_qubo_event_selector | {'solver': 'greedy', 'lam': 0.5, 'budget_mult': 1.0}         |       0.0557 |          0.0107 |   4.8708 |      0.7682 |        -0.0005 |   0.8563 |         0.0521 |        700 |
| 3_short_premium       | {'m': 2.0, 'frac': 0.5, 'skip_events': True, 'wing_m': None} |      -0.0656 |         -0.1106 |  -1.9031 |     -3.1758 |        -0.1269 |   0      |        -0.0738 |        700 |


## Scenario: fair_iv - cost model: stress

| idea                  | params                                                       |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |      dsr |   seed_min_ret |   n_nights |
|:----------------------|:-------------------------------------------------------------|-------------:|----------------:|---------:|------------:|---------------:|---------:|---------------:|-----------:|
| 0_rwa_only            | {}                                                           |       0.046  |          0.001  | nan      |    nan      |         0      | nan      |         0.046  |        700 |
| 1_yield_funded_calls  | {'m': 1.5, 'mode': 'bank_event', 'budget_mult': 1.0}         |       0.0812 |          0.0362 |   1.2657 |      0.2423 |        -0.004  |   0      |         0.0355 |        700 |
| 2_qubo_event_selector | {'solver': 'greedy', 'lam': 0.5, 'budget_mult': 1.0}         |       0.0347 |         -0.0103 |  17.8217 |     -1.5041 |        -0.0004 |   0.0118 |         0.0275 |        700 |
| 3_short_premium       | {'m': 2.0, 'frac': 0.5, 'skip_events': True, 'wing_m': None} |      -0.0952 |         -0.1402 |  -2.4839 |     -3.6104 |        -0.1775 |   0      |        -0.1035 |        700 |


## Scenario: rich_iv - cost model: stress

| idea                  | params                                                        |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |   max_drawdown |      dsr |   seed_min_ret |   n_nights |
|:----------------------|:--------------------------------------------------------------|-------------:|----------------:|---------:|------------:|---------------:|---------:|---------------:|-----------:|
| 0_rwa_only            | {}                                                            |       0.046  |          0.001  | nan      |    nan      |         0      | nan      |         0.046  |        700 |
| 1_yield_funded_calls  | {'m': 1.5, 'mode': 'bank_event', 'budget_mult': 3.0}          |       0.0334 |         -0.0116 |  -0.1269 |     -0.692  |        -0.0962 |   0      |        -0.0505 |        700 |
| 2_qubo_event_selector | {'solver': 'greedy', 'lam': 0.0, 'budget_mult': 1.0}          |       0.0415 |         -0.0035 |  39.9337 |     -5.2412 |        -0.0002 |   0.0031 |         0.0348 |        700 |
| 3_short_premium       | {'m': 1.0, 'frac': 1.0, 'skip_events': False, 'wing_m': None} |      -0.3076 |         -0.3526 |  -2.1996 |     -2.4795 |        -0.5265 |   0      |        -0.3143 |        700 |


## Idea 2 - QUBO solver comparison (base costs)

| scenario           | params                                               |   ann_return |   excess_vs_rwa |   sharpe |   ir_vs_rwa |    dsr |   payback_ask |
|:-------------------|:-----------------------------------------------------|-------------:|----------------:|---------:|------------:|-------:|--------------:|
| base               | {'solver': 'greedy', 'lam': 0.0, 'budget_mult': 1.0} |       0.0435 |         -0.0015 |   4.3518 |     -0.1177 | 0.4268 |        2.4382 |
| base               | {'solver': 'greedy', 'lam': 0.5, 'budget_mult': 1.0} |       0.0449 |         -0.0001 |  12.0506 |     -0.2071 | 0.365  |        1.264  |
| base               | {'solver': 'milp', 'lam': 0.5, 'budget_mult': 1.0}   |       0.0447 |         -0.0003 |  27.1302 |     -0.3134 | 0.2943 |        0.9545 |
| base               | {'solver': 'sa', 'lam': 0.5, 'budget_mult': 1.0}     |       0.0449 |         -0.0001 |  27.1527 |     -0.2831 | 0.3028 |        0.9634 |
| events_underpriced | {'solver': 'greedy', 'lam': 0.0, 'budget_mult': 1.0} |       0.073  |          0.028  |   3.1636 |      1.1166 | 0.9896 |        2.3081 |
| events_underpriced | {'solver': 'greedy', 'lam': 0.5, 'budget_mult': 1.0} |       0.064  |          0.019  |   4.6518 |      1.1588 | 0.983  |        1.9975 |
| events_underpriced | {'solver': 'milp', 'lam': 0.5, 'budget_mult': 1.0}   |       0.0576 |          0.0126 |   6.4238 |      1.0864 | 0.9581 |        1.7136 |
| events_underpriced | {'solver': 'sa', 'lam': 0.5, 'budget_mult': 1.0}     |       0.0572 |          0.0122 |   6.3914 |      1.0538 | 0.9504 |        1.6986 |
| fair_iv            | {'solver': 'greedy', 'lam': 0.0, 'budget_mult': 1.0} |       0.0355 |         -0.0095 |   7.6699 |     -1.7862 | 0.0745 |        0.5956 |
| fair_iv            | {'solver': 'greedy', 'lam': 0.5, 'budget_mult': 1.0} |       0.041  |         -0.004  |  13.6049 |     -0.4922 | 0.1119 |        1.0429 |
| fair_iv            | {'solver': 'milp', 'lam': 0.5, 'budget_mult': 1.0}   |       0.041  |         -0.004  |  86.8024 |     -1.0545 | 0.1123 |        0.552  |
| fair_iv            | {'solver': 'sa', 'lam': 0.5, 'budget_mult': 1.0}     |       0.0413 |         -0.0037 |  86.8394 |     -1.0136 | 0.1162 |        0.5596 |
| rich_iv            | {'solver': 'greedy', 'lam': 0.0, 'budget_mult': 1.0} |       0.0418 |         -0.0032 |  34.393  |     -3.9657 | 0.0153 |        0.306  |
| rich_iv            | {'solver': 'greedy', 'lam': 0.5, 'budget_mult': 1.0} |       0.0449 |         -0.0001 |  68.1066 |     -5.3518 | 0      |        0      |
| rich_iv            | {'solver': 'milp', 'lam': 0.5, 'budget_mult': 1.0}   |       0.0449 |         -0.0001 |  68.1066 |     -5.3518 | 0      |        0      |
| rich_iv            | {'solver': 'sa', 'lam': 0.5, 'budget_mult': 1.0}     |       0.0449 |         -0.0001 |  68.1066 |     -5.3518 | 0      |        0      |

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