# MetaWorld Slice Results (Auto-generated)

- Recognized benchmark: `MetaWorld MT1`
- Config: `config/benchmarks/experiments_metaworld_seedexp_latency_method_n30.json`
- JSON report: `output/corepaper_reports/ws3/metaworld_seedexp_latency_method_n30_results.json`
- Tasks: `reach-v3, push-v3, button-press-v3, button-press-topdown-v3, faucet-open-v3, hammer-v3, pick-place-v3, soccer-v3, peg-insert-side-v3, push-wall-v3`
- Scenarios: `nominal`, `shifted`

## Scenario-Level Summary

| Scenario | Variant | N | Mean Success | Worst-Seed | CVaR40 | Mean Steps | Success / 1k Steps |
|---|---|---:|---:|---:|---:|---:|---:|
| shifted | latency_aware | 300 | 0.6600 | 0.0000 | 0.1500 | 80.00 | 8.250 |
| shifted | method | 300 | 0.7133 | 0.0000 | 0.2833 | 80.00 | 8.917 |

## Shifted Sample-Efficiency Proxy

| Variant | Episodes | Tasks with Any Success | Mean Success | Mean Steps | Success / 1k Steps | Steps per Success |
|---|---:|---:|---:|---:|---:|---:|
| latency_aware | 300 | 9/10 | 0.6600 | 80.00 | 8.250 | 121.21 |
| method | 300 | 10/10 | 0.7133 | 80.00 | 8.917 | 112.15 |

## Gate Diagnostics

| Scenario | Variant | Episodes | Mean Risk Lambda | Green / 1k | Yellow / 1k | Red / 1k | Conformal Red / 1k |
|---|---|---:|---:|---:|---:|---:|---:|
| shifted | latency_aware | 300 | 1.0000 | 0.000 | 0.000 | 0.000 | 0.000 |
| shifted | method | 300 | 0.9500 | 1000.000 | 0.000 | 0.000 | 0.000 |

## Task Breakdown

| Task | Scenario | Variant | N | Mean Success | Mean Steps | Success / 1k Steps |
|---|---|---|---:|---:|---:|---:|
| button-press-topdown-v3 | shifted | latency_aware | 30 | 0.8000 | 80.00 | 10.000 |
| button-press-topdown-v3 | shifted | method | 30 | 0.9000 | 80.00 | 11.250 |
| button-press-v3 | shifted | latency_aware | 30 | 0.9667 | 80.00 | 12.083 |
| button-press-v3 | shifted | method | 30 | 1.0000 | 80.00 | 12.500 |
| faucet-open-v3 | shifted | latency_aware | 30 | 1.0000 | 80.00 | 12.500 |
| faucet-open-v3 | shifted | method | 30 | 0.9333 | 80.00 | 11.667 |
| hammer-v3 | shifted | latency_aware | 30 | 0.7000 | 80.00 | 8.750 |
| hammer-v3 | shifted | method | 30 | 0.8000 | 80.00 | 10.000 |
| peg-insert-side-v3 | shifted | latency_aware | 30 | 0.0000 | 80.00 | 0.000 |
| peg-insert-side-v3 | shifted | method | 30 | 0.1000 | 80.00 | 1.250 |
| pick-place-v3 | shifted | latency_aware | 30 | 1.0000 | 80.00 | 12.500 |
| pick-place-v3 | shifted | method | 30 | 1.0000 | 80.00 | 12.500 |
| push-v3 | shifted | latency_aware | 30 | 0.8000 | 80.00 | 10.000 |
| push-v3 | shifted | method | 30 | 0.9000 | 80.00 | 11.250 |
| push-wall-v3 | shifted | latency_aware | 30 | 0.2000 | 80.00 | 2.500 |
| push-wall-v3 | shifted | method | 30 | 0.1667 | 80.00 | 2.083 |
| reach-v3 | shifted | latency_aware | 30 | 0.8333 | 80.00 | 10.417 |
| reach-v3 | shifted | method | 30 | 0.9333 | 80.00 | 11.667 |
| soccer-v3 | shifted | latency_aware | 30 | 0.3000 | 80.00 | 3.750 |
| soccer-v3 | shifted | method | 30 | 0.4000 | 80.00 | 5.000 |

## Notes

- Shift profile includes physics randomization: body-mass scale in [0.80, 1.20] and geom-friction scale in [0.80, 1.20] for shifted scenarios.
- Perturbation profiles model latency, dropout, and action corruption. CORE (`method`) adds an adaptive-hysteresis uncertainty gate with monitor/rollback blending.
- Budget parity: all variants use the same per-episode cap (`max_steps=80`); monitor mode does not allocate extra episodes.
- Bounded uncertainty proxy for gating: clamp range [0.0, 5.0].
- This slice is intended as a recognized-benchmark cross-check, not a full benchmark leaderboard run.
