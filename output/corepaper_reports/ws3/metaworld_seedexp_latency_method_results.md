# MetaWorld Slice Results (Auto-generated)

- Recognized benchmark: `MetaWorld MT1`
- Config: `config/benchmarks/experiments_metaworld_seedexp_latency_method.json`
- JSON report: `output/corepaper_reports/ws3/metaworld_seedexp_latency_method_results.json`
- Tasks: `reach-v3, push-v3, button-press-v3, button-press-topdown-v3, faucet-open-v3, hammer-v3, pick-place-v3, soccer-v3, peg-insert-side-v3, push-wall-v3`
- Scenarios: `nominal`, `shifted`

## Scenario-Level Summary

| Scenario | Variant | N | Mean Success | Worst-Seed | CVaR40 | Mean Steps | Success / 1k Steps |
|---|---|---:|---:|---:|---:|---:|---:|
| shifted | latency_aware | 140 | 0.6429 | 0.0000 | 0.1071 | 80.00 | 8.036 |
| shifted | method | 140 | 0.7286 | 0.0000 | 0.3214 | 80.00 | 9.107 |

## Shifted Sample-Efficiency Proxy

| Variant | Episodes | Tasks with Any Success | Mean Success | Mean Steps | Success / 1k Steps | Steps per Success |
|---|---:|---:|---:|---:|---:|---:|
| latency_aware | 140 | 9/10 | 0.6429 | 80.00 | 8.036 | 124.44 |
| method | 140 | 9/10 | 0.7286 | 80.00 | 9.107 | 109.80 |

## Gate Diagnostics

| Scenario | Variant | Episodes | Mean Risk Lambda | Green / 1k | Yellow / 1k | Red / 1k | Conformal Red / 1k |
|---|---|---:|---:|---:|---:|---:|---:|
| shifted | latency_aware | 140 | 1.0000 | 0.000 | 0.000 | 0.000 | 0.000 |
| shifted | method | 140 | 0.9500 | 1000.000 | 0.000 | 0.000 | 0.000 |

## Task Breakdown

| Task | Scenario | Variant | N | Mean Success | Mean Steps | Success / 1k Steps |
|---|---|---|---:|---:|---:|---:|
| button-press-topdown-v3 | shifted | latency_aware | 14 | 0.7143 | 80.00 | 8.929 |
| button-press-topdown-v3 | shifted | method | 14 | 0.9286 | 80.00 | 11.607 |
| button-press-v3 | shifted | latency_aware | 14 | 1.0000 | 80.00 | 12.500 |
| button-press-v3 | shifted | method | 14 | 1.0000 | 80.00 | 12.500 |
| faucet-open-v3 | shifted | latency_aware | 14 | 1.0000 | 80.00 | 12.500 |
| faucet-open-v3 | shifted | method | 14 | 1.0000 | 80.00 | 12.500 |
| hammer-v3 | shifted | latency_aware | 14 | 0.6429 | 80.00 | 8.036 |
| hammer-v3 | shifted | method | 14 | 0.9286 | 80.00 | 11.607 |
| peg-insert-side-v3 | shifted | latency_aware | 14 | 0.0000 | 80.00 | 0.000 |
| peg-insert-side-v3 | shifted | method | 14 | 0.0000 | 80.00 | 0.000 |
| pick-place-v3 | shifted | latency_aware | 14 | 1.0000 | 80.00 | 12.500 |
| pick-place-v3 | shifted | method | 14 | 1.0000 | 80.00 | 12.500 |
| push-v3 | shifted | latency_aware | 14 | 0.7857 | 80.00 | 9.821 |
| push-v3 | shifted | method | 14 | 0.8571 | 80.00 | 10.714 |
| push-wall-v3 | shifted | latency_aware | 14 | 0.1429 | 80.00 | 1.786 |
| push-wall-v3 | shifted | method | 14 | 0.2857 | 80.00 | 3.571 |
| reach-v3 | shifted | latency_aware | 14 | 0.8571 | 80.00 | 10.714 |
| reach-v3 | shifted | method | 14 | 0.9286 | 80.00 | 11.607 |
| soccer-v3 | shifted | latency_aware | 14 | 0.2857 | 80.00 | 3.571 |
| soccer-v3 | shifted | method | 14 | 0.3571 | 80.00 | 4.464 |

## Notes

- Shift profile includes physics randomization: body-mass scale in [0.80, 1.20] and geom-friction scale in [0.80, 1.20] for shifted scenarios.
- Perturbation profiles model latency, dropout, and action corruption. CORE (`method`) adds an adaptive-hysteresis uncertainty gate with monitor/rollback blending.
- Budget parity: all variants use the same per-episode cap (`max_steps=80`); monitor mode does not allocate extra episodes.
- Bounded uncertainty proxy for gating: clamp range [0.0, 5.0].
- This slice is intended as a recognized-benchmark cross-check, not a full benchmark leaderboard run.
