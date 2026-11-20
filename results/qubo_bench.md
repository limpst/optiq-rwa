# QUBO solver benchmark

Synthetic weekly sets: 84 binaries (7 nights x 3 coins x 4 strikes), K=7, rho=0.7, 30 seeds.
gap = (objective - MILP objective)/|MILP objective|, lower is better (0 = optimal). SA objective is measured after the core.py repair step; feasible = budget and one-strike satisfied *before* repair.

## lam = 0.0

| solver                    |   gap_pct |   worst_gap_pct |   feasible |   runtime_s |
|:--------------------------|----------:|----------------:|-----------:|------------:|
| greedy                    |     0     |           0     |          1 |       0     |
| milp                      |     0     |           0     |          1 |       0.003 |
| sa_old(P2=2,120sw,1r)     |    64.53  |         107.394 |          1 |       0.006 |
| sa_tuned_polish(500sw,4r) |     0     |           0     |          0 |       0.089 |
| sa_s120_r1_p1             |     0.212 |           4.258 |          0 |       0.005 |
| sa_s120_r1_p3             |     0.448 |           8.178 |          0 |       0.005 |
| sa_s120_r1_p10            |     0.797 |           9.65  |          0 |       0.006 |
| sa_s120_r4_p1             |     0.004 |           0.116 |          0 |       0.021 |
| sa_s120_r4_p3             |     0     |           0     |          0 |       0.021 |
| sa_s120_r4_p10            |     0.004 |           0.116 |          0 |       0.023 |
| sa_s500_r1_p1             |     0.445 |           8.769 |          0 |       0.022 |
| sa_s500_r1_p3             |     0.054 |           1.499 |          0 |       0.022 |
| sa_s500_r1_p10            |     0.025 |           0.738 |          0 |       0.024 |
| sa_s500_r4_p1             |     0     |           0     |          0 |       0.087 |
| sa_s500_r4_p3             |     0     |           0     |          0 |       0.089 |
| sa_s500_r4_p10            |     0     |           0     |          0 |       0.097 |
| sa_s2000_r1_p1            |     0.099 |           1.393 |          0 |       0.087 |
| sa_s2000_r1_p3            |     0.087 |           1.393 |          0 |       0.089 |
| sa_s2000_r1_p10           |     0.095 |           1.983 |          0 |       0.095 |
| sa_s2000_r4_p1            |     0     |           0     |          0 |       0.347 |
| sa_s2000_r4_p3            |     0     |           0     |          0 |       0.354 |
| sa_s2000_r4_p10           |     0     |           0     |          0 |       0.382 |

## lam = 0.5

| solver                    |   gap_pct |   worst_gap_pct |   feasible |   runtime_s |
|:--------------------------|----------:|----------------:|-----------:|------------:|
| greedy                    |     1.091 |           6.913 |      1     |       0     |
| milp                      |     0     |           0     |      1     |       0.025 |
| sa_old(P2=2,120sw,1r)     |    83.907 |         147.817 |      1     |       0.009 |
| sa_tuned_polish(500sw,4r) |     0     |           0     |      0.1   |       0.106 |
| sa_s120_r1_p1             |     0.344 |           2.143 |      0.1   |       0.006 |
| sa_s120_r1_p3             |     0.707 |           6.661 |      0.1   |       0.006 |
| sa_s120_r1_p10            |     0.904 |           5.876 |      0.1   |       0.007 |
| sa_s120_r4_p1             |     0.07  |           0.735 |      0.1   |       0.025 |
| sa_s120_r4_p3             |     0.12  |           1.035 |      0.1   |       0.025 |
| sa_s120_r4_p10            |     0.279 |           2.592 |      0.1   |       0.028 |
| sa_s500_r1_p1             |     0.192 |           2.422 |      0.067 |       0.026 |
| sa_s500_r1_p3             |     0.249 |           2.034 |      0.1   |       0.027 |
| sa_s500_r1_p10            |     0.606 |           5.04  |      0.1   |       0.028 |
| sa_s500_r4_p1             |     0.116 |           1.035 |      0.1   |       0.103 |
| sa_s500_r4_p3             |     0.094 |           1.035 |      0.1   |       0.105 |
| sa_s500_r4_p10            |     0.185 |           1.671 |      0.1   |       0.112 |
| sa_s2000_r1_p1            |     0.291 |           2.857 |      0.1   |       0.1   |
| sa_s2000_r1_p3            |     0.249 |           1.764 |      0.1   |       0.103 |
| sa_s2000_r1_p10           |     0.796 |           7.499 |      0.1   |       0.112 |
| sa_s2000_r4_p1            |     0.099 |           1.035 |      0.1   |       0.403 |
| sa_s2000_r4_p3            |     0.099 |           1.035 |      0.1   |       0.431 |
| sa_s2000_r4_p10           |     0.242 |           2.777 |      0.067 |       0.459 |

## Interpretation

- What changed: the old SA (P2 = 2x edge scale, 120 sweeps, 1 restart) was 65-84% worse than MILP (greedy: 0% at lam=0, 1.1% at lam=0.5). Tuned SA (P2 = 0.1x, 500 sweeps, 4 restarts, repair + polish) is at 0.000% gap in both cases; without polish 0.0% / 0.12% (still better than greedy at lam=0.5).
- Why: the budget is encoded as an equality with binary slack bits, and SA starts from x=0 where all slack bits are 1 (energy 0). Adding one unit costs P2 = 2x edge scale > any single edge, so every first flip is rejected and SA freezes near the empty set (feasible = 100% but useless). A soft P2 = 0.1x lets SA fill the book; the budget is then enforced by the repair step.
- Cost of soft P2: SA output is infeasible before repair (feasible column 0-10%), so repair_selection (budget + one strike per night/coin) is mandatory. polish() (feasible 1-flip/swap descent) closes the last gap (seed with 2% miss).
- More compute helps less than the fix: with the old P2 even 2000 sweeps x 4 restarts stayed 24-41% off; restarts matter more than sweeps once P2 is soft; p1 multiplier 1 is enough (3-10 slightly worse).
- What to do: use solver="sa" (new defaults, ~0.09 s per weekly set) or solver="milp" (exact, ~5 ms, so it is also the cheapest exact reference); keep greedy only as a baseline. Re-run results/run_sweep.py to refresh SUMMARY.md.