# Recent-Paper Baseline Comparison (Auto-generated)

- Source: `output/corepaper_logs/experiments/library_lane_latest`
- Stress scenarios: `R4-hard, S1-hard, S2-high, S3-severe, SIM-isaac`
- Reference group: `method`

## Stress Aggregate Ranking

| Rank | Variant | N | Mean | CI95 | Worst | CVaR40 |
|---:|---|---:|---:|---:|---:|---:|
| 1 | method | 50 | 0.6700 | ±0.0063 | 0.6351 | 0.6438 |
| 2 | rllib_sac | 50 | 0.6540 | ±0.0068 | 0.6140 | 0.6258 |
| 3 | sb3_ppo | 50 | 0.6481 | ±0.0072 | 0.6087 | 0.6184 |

## Scenario Means

| Scenario | baseline | ext1 | ext2 | latency_aware | adaptmanip | robust_cp | history_keyframe | constrained_flow | method |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| R4-hard | - | - | - | - | - | - | - | - | 0.6388 |
| S1-hard | - | - | - | - | - | - | - | - | 0.6488 |
| S2-high | - | - | - | - | - | - | - | - | 0.6831 |
| S3-severe | - | - | - | - | - | - | - | - | 0.6980 |
| SIM-isaac | - | - | - | - | - | - | - | - | 0.6815 |
| nominal | - | - | - | - | - | - | - | - | 0.7479 |

## Method vs Comparator (Stress Aggregate)

| Comparison | Delta Mean | Delta CI95 | Delta Worst | Delta CVaR40 | Cohen's d | p-value |
|---|---:|---:|---:|---:|---:|---:|
| method vs sb3_ppo | +0.0220 | ±0.0096 | +0.0264 | +0.0254 | 0.902 | 0.000025 (monte_carlo) |
| method vs rllib_sac | +0.0160 | ±0.0093 | +0.0211 | +0.0180 | 0.677 | 0.000990 (monte_carlo) |

## Guidance

- Keep CORE as primary method claim: top stress aggregate across comparators.
- Report stress aggregate and reliability-floor metrics jointly; avoid mean-only framing.
