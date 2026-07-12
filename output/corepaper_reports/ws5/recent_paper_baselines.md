# Recent-Paper Baseline Comparison (Auto-generated)

- Source: `output/corepaper_logs/experiments/recent_baselines_latest`
- Stress scenarios: `R4-hard, S1-hard, S2-high, S3-severe, SIM-isaac`
- Reference group: `method`

## Stress Aggregate Ranking

| Rank | Variant | N | Mean | CI95 | Worst | CVaR40 |
|---:|---|---:|---:|---:|---:|---:|
| 1 | method | 70 | 0.6652 | ±0.0058 | 0.6260 | 0.6367 |
| 2 | adaptmanip | 70 | 0.6581 | ±0.0060 | 0.6174 | 0.6288 |
| 3 | latency_aware | 70 | 0.6574 | ±0.0063 | 0.6136 | 0.6264 |
| 4 | constrained_flow | 70 | 0.6558 | ±0.0052 | 0.6214 | 0.6299 |
| 5 | ext2 | 70 | 0.6543 | ±0.0058 | 0.6141 | 0.6255 |
| 6 | history_keyframe | 70 | 0.6535 | ±0.0067 | 0.6104 | 0.6219 |
| 7 | robust_cp | 70 | 0.6526 | ±0.0057 | 0.6149 | 0.6244 |
| 8 | ext1 | 70 | 0.6374 | ±0.0061 | 0.5949 | 0.6075 |
| 9 | baseline | 70 | 0.6118 | ±0.0066 | 0.5674 | 0.5794 |

## Scenario Means

| Scenario | baseline | ext1 | ext2 | latency_aware | adaptmanip | robust_cp | history_keyframe | constrained_flow | method |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| R4-hard | 0.5734 | 0.6005 | 0.6201 | 0.6188 | 0.6235 | 0.6190 | 0.6177 | 0.6249 | 0.6304 |
| S1-hard | 0.5853 | 0.6145 | 0.6308 | 0.6340 | 0.6341 | 0.6298 | 0.6260 | 0.6348 | 0.6430 |
| S2-high | 0.6277 | 0.6537 | 0.6707 | 0.6801 | 0.6727 | 0.6682 | 0.6641 | 0.6678 | 0.6808 |
| S3-severe | 0.6466 | 0.6681 | 0.6840 | 0.6863 | 0.6912 | 0.6817 | 0.6952 | 0.6825 | 0.6956 |
| SIM-isaac | 0.6259 | 0.6503 | 0.6660 | 0.6677 | 0.6691 | 0.6644 | 0.6643 | 0.6690 | 0.6761 |
| nominal | 0.7117 | 0.7308 | 0.7425 | 0.7419 | 0.7444 | 0.7369 | 0.7419 | 0.7410 | 0.7494 |

## Method vs Comparator (Stress Aggregate)

| Comparison | Delta Mean | Delta CI95 | Delta Worst | Delta CVaR40 | Cohen's d | p-value |
|---|---:|---:|---:|---:|---:|---:|
| method vs baseline | +0.0534 | ±0.0088 | +0.0586 | +0.0573 | 2.015 | 0.000000 (monte_carlo) |
| method vs ext1 | +0.0278 | ±0.0084 | +0.0311 | +0.0292 | 1.094 | 0.000000 (monte_carlo) |
| method vs ext2 | +0.0109 | ±0.0083 | +0.0119 | +0.0112 | 0.436 | 0.011265 (monte_carlo) |
| method vs latency_aware | +0.0078 | ±0.0086 | +0.0124 | +0.0103 | 0.303 | 0.075770 (monte_carlo) |
| method vs adaptmanip | +0.0071 | ±0.0084 | +0.0086 | +0.0079 | 0.280 | 0.100505 (monte_carlo) |
| method vs robust_cp | +0.0126 | ±0.0082 | +0.0111 | +0.0123 | 0.510 | 0.003345 (monte_carlo) |
| method vs history_keyframe | +0.0117 | ±0.0089 | +0.0156 | +0.0148 | 0.436 | 0.011455 (monte_carlo) |
| method vs constrained_flow | +0.0094 | ±0.0078 | +0.0046 | +0.0068 | 0.396 | 0.020940 (monte_carlo) |

## Guidance

- Keep CORE as primary method claim: top stress aggregate across comparators.
- Closest recent-paper baseline is `adaptmanip` (stress mean 0.6581); prioritize analysis against this baseline in text and figures.
- Report stress aggregate and reliability-floor metrics jointly; avoid mean-only framing.
