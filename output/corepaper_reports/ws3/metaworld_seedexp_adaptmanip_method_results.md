# MetaWorld Slice Results (Auto-generated)

- Recognized benchmark: `MetaWorld MT1`
- Config: `config/benchmarks/experiments_metaworld_seedexp_adaptmanip_method.json`
- JSON report: `output/corepaper_reports/ws3/metaworld_seedexp_adaptmanip_method_results.json`
- Tasks: `reach-v3, push-v3, button-press-v3, button-press-topdown-v3, faucet-open-v3, hammer-v3, pick-place-v3, soccer-v3, peg-insert-side-v3, push-wall-v3`
- Scenarios: `nominal`, `shifted`

## Scenario-Level Summary

| Scenario | Variant | N | Mean Success | Worst-Seed | CVaR40 | Mean Steps | Success / 1k Steps |
|---|---|---:|---:|---:|---:|---:|---:|
| shifted | adaptmanip | 140 | 0.6214 | 0.0000 | 0.0536 | 80.00 | 7.768 |
| shifted | method | 140 | 0.7000 | 0.0000 | 0.2500 | 80.00 | 8.750 |

## Shifted Sample-Efficiency Proxy

| Variant | Episodes | Tasks with Any Success | Mean Success | Mean Steps | Success / 1k Steps | Steps per Success |
|---|---:|---:|---:|---:|---:|---:|
| adaptmanip | 140 | 8/10 | 0.6214 | 80.00 | 7.768 | 128.74 |
| method | 140 | 10/10 | 0.7000 | 80.00 | 8.750 | 114.29 |

## Gate Diagnostics

| Scenario | Variant | Episodes | Mean Risk Lambda | Green / 1k | Yellow / 1k | Red / 1k | Conformal Red / 1k |
|---|---|---:|---:|---:|---:|---:|---:|
| shifted | adaptmanip | 140 | 1.0000 | 0.000 | 0.000 | 0.000 | 0.000 |
| shifted | method | 140 | 0.9500 | 1000.000 | 0.000 | 0.000 | 0.000 |

## Task Breakdown

| Task | Scenario | Variant | N | Mean Success | Mean Steps | Success / 1k Steps |
|---|---|---|---:|---:|---:|---:|
| button-press-topdown-v3 | shifted | adaptmanip | 14 | 0.7857 | 80.00 | 9.821 |
| button-press-topdown-v3 | shifted | method | 14 | 0.8571 | 80.00 | 10.714 |
| button-press-v3 | shifted | adaptmanip | 14 | 0.7857 | 80.00 | 9.821 |
| button-press-v3 | shifted | method | 14 | 1.0000 | 80.00 | 12.500 |
| faucet-open-v3 | shifted | adaptmanip | 14 | 0.9286 | 80.00 | 11.607 |
| faucet-open-v3 | shifted | method | 14 | 0.9286 | 80.00 | 11.607 |
| hammer-v3 | shifted | adaptmanip | 14 | 0.6429 | 80.00 | 8.036 |
| hammer-v3 | shifted | method | 14 | 0.7857 | 80.00 | 9.821 |
| peg-insert-side-v3 | shifted | adaptmanip | 14 | 0.0000 | 80.00 | 0.000 |
| peg-insert-side-v3 | shifted | method | 14 | 0.0714 | 80.00 | 0.893 |
| pick-place-v3 | shifted | adaptmanip | 14 | 1.0000 | 80.00 | 12.500 |
| pick-place-v3 | shifted | method | 14 | 1.0000 | 80.00 | 12.500 |
| push-v3 | shifted | adaptmanip | 14 | 0.8571 | 80.00 | 10.714 |
| push-v3 | shifted | method | 14 | 0.9286 | 80.00 | 11.607 |
| push-wall-v3 | shifted | adaptmanip | 14 | 0.0000 | 80.00 | 0.000 |
| push-wall-v3 | shifted | method | 14 | 0.1429 | 80.00 | 1.786 |
| reach-v3 | shifted | adaptmanip | 14 | 0.9286 | 80.00 | 11.607 |
| reach-v3 | shifted | method | 14 | 0.9286 | 80.00 | 11.607 |
| soccer-v3 | shifted | adaptmanip | 14 | 0.2857 | 80.00 | 3.571 |
| soccer-v3 | shifted | method | 14 | 0.3571 | 80.00 | 4.464 |

## Notes

- Shift profile includes physics randomization: body-mass scale in [0.80, 1.20] and geom-friction scale in [0.80, 1.20] for shifted scenarios.
- Perturbation profiles model latency, dropout, and action corruption. CORE (`method`) adds an adaptive-hysteresis uncertainty gate with monitor/rollback blending.
- Budget parity: all variants use the same per-episode cap (`max_steps=80`); monitor mode does not allocate extra episodes.
- Bounded uncertainty proxy for gating: clamp range [0.0, 5.0].
- This slice is intended as a recognized-benchmark cross-check, not a full benchmark leaderboard run.
