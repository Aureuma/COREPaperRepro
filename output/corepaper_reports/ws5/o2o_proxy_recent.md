# Recent-Paper Baseline Comparison (Auto-generated)

- Source: `output/corepaper_logs/experiments/o2o_proxy_latest`
- Stress scenarios: `R4-hard, S1-hard, S2-high, S3-severe, SIM-isaac`
- Reference group: `method`

## Stress Aggregate Ranking

| Rank | Variant | N | Mean | CI95 | Worst | CVaR40 |
|---:|---|---:|---:|---:|---:|---:|
| 1 | method | 50 | 0.6889 | ±0.0047 | 0.6562 | 0.6710 |
| 2 | adaptmanip | 50 | 0.6697 | ±0.0057 | 0.6303 | 0.6467 |
| 3 | robust_cp | 50 | 0.6665 | ±0.0051 | 0.6247 | 0.6473 |
| 4 | ext2 | 50 | 0.6599 | ±0.0053 | 0.6246 | 0.6399 |
| 5 | latency_aware | 50 | 0.6578 | ±0.0054 | 0.6249 | 0.6372 |
| 6 | baseline | 50 | 0.6214 | ±0.0061 | 0.5840 | 0.5974 |

## Scenario Means

| Scenario | baseline | ext1 | ext2 | latency_aware | adaptmanip | robust_cp | history_keyframe | constrained_flow | method |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| R4-hard | 0.5941 | - | 0.6380 | 0.6329 | 0.6424 | 0.6417 | - | - | 0.6678 |
| S1-hard | 0.6006 | - | 0.6422 | 0.6422 | 0.6524 | 0.6533 | - | - | 0.6751 |
| S2-high | 0.6334 | - | 0.6665 | 0.6668 | 0.6838 | 0.6768 | - | - | 0.6988 |
| S3-severe | 0.6456 | - | 0.6850 | 0.6820 | 0.6907 | 0.6895 | - | - | 0.7087 |
| SIM-isaac | 0.6334 | - | 0.6678 | 0.6652 | 0.6794 | 0.6710 | - | - | 0.6941 |
| nominal | 0.6974 | - | 0.7301 | 0.7296 | 0.7418 | 0.7349 | - | - | 0.7545 |

## Method vs Comparator (Stress Aggregate)

| Comparison | Delta Mean | Delta CI95 | Delta Worst | Delta CVaR40 | Cohen's d | p-value |
|---|---:|---:|---:|---:|---:|---:|
| method vs baseline | +0.0675 | ±0.0077 | +0.0722 | +0.0736 | 3.449 | 0.000000 (monte_carlo) |
| method vs ext2 | +0.0290 | ±0.0071 | +0.0316 | +0.0311 | 1.610 | 0.000000 (monte_carlo) |
| method vs latency_aware | +0.0311 | ±0.0072 | +0.0313 | +0.0338 | 1.697 | 0.000000 (monte_carlo) |
| method vs adaptmanip | +0.0192 | ±0.0074 | +0.0259 | +0.0243 | 1.017 | 0.000000 (monte_carlo) |
| method vs robust_cp | +0.0224 | ±0.0069 | +0.0315 | +0.0236 | 1.271 | 0.000000 (monte_carlo) |

## Guidance

- Keep CORE as primary method claim: top stress aggregate across comparators.
- Closest recent-paper baseline is `adaptmanip` (stress mean 0.6697); prioritize analysis against this baseline in text and figures.
- Report stress aggregate and reliability-floor metrics jointly; avoid mean-only framing.
