# Recent-Paper Baseline Comparison (Auto-generated)

- Source: `output/corepaper_logs/experiments/training_backed_latest`
- Stress scenarios: `R4-hard, S1-hard, S2-high, S3-severe, SIM-isaac`
- Reference group: `method`

## Stress Aggregate Ranking

| Rank | Variant | N | Mean | CI95 | Worst | CVaR40 |
|---:|---|---:|---:|---:|---:|---:|
| 1 | baseline | 40 | 0.7706 | ±0.0074 | 0.7074 | 0.7472 |
| 2 | adaptmanip | 40 | 0.7663 | ±0.0076 | 0.7070 | 0.7425 |
| 3 | ext2 | 40 | 0.7588 | ±0.0085 | 0.6937 | 0.7312 |
| 4 | latency_aware | 40 | 0.7536 | ±0.0108 | 0.6610 | 0.7183 |
| 5 | robust_cp | 40 | 0.7488 | ±0.0113 | 0.6608 | 0.7142 |
| 6 | method | 40 | 0.5480 | ±0.0289 | 0.3535 | 0.4550 |

## Scenario Means

| Scenario | baseline | ext1 | ext2 | latency_aware | adaptmanip | robust_cp | history_keyframe | constrained_flow | method |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| R4-hard | 0.7496 | - | 0.7401 | 0.7293 | 0.7409 | 0.7475 | - | - | 0.5667 |
| S1-hard | 0.7662 | - | 0.7498 | 0.7557 | 0.7599 | 0.7466 | - | - | 0.5394 |
| S2-high | 0.7747 | - | 0.7756 | 0.7478 | 0.7673 | 0.7554 | - | - | 0.5220 |
| S3-severe | 0.7903 | - | 0.7638 | 0.7653 | 0.7825 | 0.7532 | - | - | 0.4899 |
| SIM-isaac | 0.7722 | - | 0.7645 | 0.7699 | 0.7808 | 0.7415 | - | - | 0.6219 |
| nominal | 0.7811 | - | 0.7811 | 0.7584 | 0.7851 | 0.7667 | - | - | 0.5283 |

## Method vs Comparator (Stress Aggregate)

| Comparison | Delta Mean | Delta CI95 | Delta Worst | Delta CVaR40 | Cohen's d | p-value |
|---|---:|---:|---:|---:|---:|---:|
| method vs baseline | -0.2226 | ±0.0299 | -0.3539 | -0.2923 | -3.267 | 0.000000 (monte_carlo) |
| method vs ext2 | -0.2108 | ±0.0302 | -0.3402 | -0.2762 | -3.062 | 0.000000 (monte_carlo) |
| method vs latency_aware | -0.2056 | ±0.0309 | -0.3075 | -0.2633 | -2.917 | 0.000000 (monte_carlo) |
| method vs adaptmanip | -0.2183 | ±0.0299 | -0.3535 | -0.2875 | -3.196 | 0.000000 (monte_carlo) |
| method vs robust_cp | -0.2009 | ±0.0311 | -0.3073 | -0.2592 | -2.833 | 0.000000 (monte_carlo) |

## Guidance

- CORE is not top on stress aggregate; narrow claims or retune method before submission.
- Closest recent-paper baseline is `adaptmanip` (stress mean 0.7663); prioritize analysis against this baseline in text and figures.
- Report stress aggregate and reliability-floor metrics jointly; avoid mean-only framing.
