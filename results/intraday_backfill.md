# Intraday short backfill (sell at 19:20 UTC bid; buy back at target or hold to settlement)

pnl_per_prem = net P&L per $1 premium received (taker fees both ways, 12.5% cap). closed = share of legs bought back before expiry.

| rule       |   legs |   mean |   median |   worst |   hit |   closed |   exit_h |
|:-----------|-------:|-------:|---------:|--------:|------:|---------:|---------:|
| hold       |     27 |  0.879 |    0.875 |   0.875 | 0.63  |    0     |   12.666 |
| target 25% |     27 |  0.177 |    0.121 |   0.031 | 0.926 |    0.889 |    4.802 |
| target 50% |     27 |  0.432 |    0.375 |   0.312 | 0.889 |    0.815 |    5.664 |
| target 75% |     27 |  0.737 |    0.726 |   0.599 | 0.778 |    0.519 |   11.791 |

## by base (hold)

| base     |   legs |   mean |   worst |
|:---------|-------:|-------:|--------:|
| BTC      |      6 |  0.882 |   0.875 |
| BTC_USDC |      5 |  0.88  |   0.875 |
| ETH      |      6 |  0.878 |   0.875 |
| ETH_USDC |      6 |  0.876 |   0.875 |
| SOL_USDC |      4 |  0.875 |   0.875 |

## mid decay (median mid_t / mid_entry) at +2h / +6h / +10h

|                      |   2.0 |    6.0 |   10.0 |
|:---------------------|------:|-------:|-------:|
| ('BTC', 'call')      |  1.27 |   0.38 | nan    |
| ('BTC', 'put')       |  0.79 |   0.39 |   1.64 |
| ('BTC_USDC', 'call') |  1.22 |   0.4  | nan    |
| ('BTC_USDC', 'put')  |  0.67 |   0.46 |   1.77 |
| ('ETH', 'call')      |  1.07 |   0.3  | nan    |
| ('ETH', 'put')       |  0.68 |   0.24 |   0.49 |
| ('ETH_USDC', 'call') |  0.98 |   0.27 | nan    |
| ('ETH_USDC', 'put')  |  0.65 |   0.26 |   0.53 |
| ('SOL_USDC', 'put')  |  0.95 | nan    | nan    |