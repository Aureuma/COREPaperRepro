# MetaWorld Slice Results (Auto-generated)

- Recognized benchmark: `MetaWorld MT1`
- Config: `config/benchmarks/experiments_metaworld_seedexp_adaptmanip_method_n30.json`
- JSON report: `output/corepaper_reports/ws3/metaworld_seedexp_adaptmanip_method_n30_results.json`
- Tasks: `reach-v3, push-v3, button-press-v3, button-press-topdown-v3, faucet-open-v3, hammer-v3, pick-place-v3, soccer-v3, peg-insert-side-v3, push-wall-v3`
- Scenarios: `nominal`, `shifted`

## Scenario-Level Summary

| Scenario | Variant | N | Mean Success | Worst-Seed | CVaR40 | Mean Steps | Success / 1k Steps |
|---|---|---:|---:|---:|---:|---:|---:|
| shifted | adaptmanip | 300 | 0.5600 | 0.0000 | 0.0000 | 80.00 | 7.000 |
| shifted | method | 300 | 0.6967 | 0.0000 | 0.2417 | 80.00 | 8.708 |

## Shifted Sample-Efficiency Proxy

| Variant | Episodes | Tasks with Any Success | Mean Success | Mean Steps | Success / 1k Steps | Steps per Success |
|---|---:|---:|---:|---:|---:|---:|
| adaptmanip | 300 | 9/10 | 0.5600 | 80.00 | 7.000 | 142.86 |
| method | 300 | 9/10 | 0.6967 | 80.00 | 8.708 | 114.83 |

## Gate Diagnostics

| Scenario | Variant | Episodes | Mean Risk Lambda | Green / 1k | Yellow / 1k | Red / 1k | Conformal Red / 1k |
|---|---|---:|---:|---:|---:|---:|---:|
| shifted | adaptmanip | 300 | 1.0000 | 0.000 | 0.000 | 0.000 | 0.000 |
| shifted | method | 300 | 0.9500 | 1000.000 | 0.000 | 0.000 | 0.000 |

## Task Breakdown

| Task | Scenario | Variant | N | Mean Success | Mean Steps | Success / 1k Steps |
|---|---|---|---:|---:|---:|---:|
| button-press-topdown-v3 | shifted | adaptmanip | 30 | 0.6000 | 80.00 | 7.500 |
| button-press-topdown-v3 | shifted | method | 30 | 0.8667 | 80.00 | 10.833 |
| button-press-v3 | shifted | adaptmanip | 30 | 0.7667 | 80.00 | 9.583 |
| button-press-v3 | shifted | method | 30 | 1.0000 | 80.00 | 12.500 |
| faucet-open-v3 | shifted | adaptmanip | 30 | 0.6667 | 80.00 | 8.333 |
| faucet-open-v3 | shifted | method | 30 | 1.0000 | 80.00 | 12.500 |
| hammer-v3 | shifted | adaptmanip | 30 | 0.5667 | 80.00 | 7.083 |
| hammer-v3 | shifted | method | 30 | 0.8667 | 80.00 | 10.833 |
| peg-insert-side-v3 | shifted | adaptmanip | 30 | 0.0000 | 80.00 | 0.000 |
| peg-insert-side-v3 | shifted | method | 30 | 0.0000 | 80.00 | 0.000 |
| pick-place-v3 | shifted | adaptmanip | 30 | 1.0000 | 80.00 | 12.500 |
| pick-place-v3 | shifted | method | 30 | 1.0000 | 80.00 | 12.500 |
| push-v3 | shifted | adaptmanip | 30 | 0.7000 | 80.00 | 8.750 |
| push-v3 | shifted | method | 30 | 0.9333 | 80.00 | 11.667 |
| push-wall-v3 | shifted | adaptmanip | 30 | 0.0667 | 80.00 | 0.833 |
| push-wall-v3 | shifted | method | 30 | 0.1000 | 80.00 | 1.250 |
| reach-v3 | shifted | adaptmanip | 30 | 0.8000 | 80.00 | 10.000 |
| reach-v3 | shifted | method | 30 | 0.8333 | 80.00 | 10.417 |
| soccer-v3 | shifted | adaptmanip | 30 | 0.4333 | 80.00 | 5.417 |
| soccer-v3 | shifted | method | 30 | 0.3667 | 80.00 | 4.583 |

## Notes

- Shift profile includes physics randomization: body-mass scale in [0.80, 1.20] and geom-friction scale in [0.80, 1.20] for shifted scenarios.
- Perturbation profiles model latency, dropout, and action corruption. CORE (`method`) adds an adaptive-hysteresis uncertainty gate with monitor/rollback blending.
- Budget parity: all variants use the same per-episode cap (`max_steps=80`); monitor mode does not allocate extra episodes.
- Bounded uncertainty proxy for gating: clamp range [0.0, 5.0].
- This slice is intended as a recognized-benchmark cross-check, not a full benchmark leaderboard run.
