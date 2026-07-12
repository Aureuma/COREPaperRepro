# MetaWorld Slice Results (Auto-generated)

- Recognized benchmark: `MetaWorld MT1`
- Config: `config/benchmarks/experiments_metaworld_slice.json`
- JSON report: `output/corepaper_reports/ws3/metaworld_slice_results.json`
- Tasks: `reach-v3, push-v3, button-press-v3, button-press-topdown-v3, faucet-open-v3, hammer-v3, pick-place-v3, soccer-v3, peg-insert-side-v3, push-wall-v3`
- Scenarios: `nominal`, `shifted`

## Scenario-Level Summary

| Scenario | Variant | N | Mean Success | Worst-Seed | CVaR40 | Mean Steps | Success / 1k Steps |
|---|---|---:|---:|---:|---:|---:|---:|
| nominal | baseline | 50 | 0.8000 | 0.0000 | 0.5000 | 80.00 | 10.000 |
| nominal | ext1 | 50 | 0.8400 | 0.0000 | 0.6000 | 80.00 | 10.500 |
| nominal | ext2 | 50 | 0.7800 | 0.0000 | 0.4500 | 80.00 | 9.750 |
| nominal | method | 50 | 0.8200 | 0.0000 | 0.5500 | 80.00 | 10.250 |
| shifted | baseline | 50 | 0.1400 | 0.0000 | 0.0000 | 80.00 | 1.750 |
| shifted | ext1 | 50 | 0.2800 | 0.0000 | 0.0000 | 80.00 | 3.500 |
| shifted | ext2 | 50 | 0.4800 | 0.0000 | 0.0000 | 80.00 | 6.000 |
| shifted | method | 50 | 0.7000 | 0.0000 | 0.2500 | 80.00 | 8.750 |

## Shifted Sample-Efficiency Proxy

| Variant | Episodes | Tasks with Any Success | Mean Success | Mean Steps | Success / 1k Steps | Steps per Success |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 50 | 4/10 | 0.1400 | 80.00 | 1.750 | 571.43 |
| ext1 | 50 | 5/10 | 0.2800 | 80.00 | 3.500 | 285.71 |
| ext2 | 50 | 8/10 | 0.4800 | 80.00 | 6.000 | 166.67 |
| method | 50 | 8/10 | 0.7000 | 80.00 | 8.750 | 114.29 |

## Gate Diagnostics

| Scenario | Variant | Episodes | Mean Risk Lambda | Green / 1k | Yellow / 1k | Red / 1k | Conformal Red / 1k |
|---|---|---:|---:|---:|---:|---:|---:|
| nominal | baseline | 50 | 1.0000 | 0.000 | 0.000 | 0.000 | 0.000 |
| nominal | ext1 | 50 | 1.0000 | 0.000 | 0.000 | 0.000 | 0.000 |
| nominal | ext2 | 50 | 1.0000 | 0.000 | 0.000 | 0.000 | 0.000 |
| nominal | method | 50 | 1.0000 | 0.000 | 0.000 | 0.000 | 0.000 |
| shifted | baseline | 50 | 1.0000 | 0.000 | 0.000 | 0.000 | 0.000 |
| shifted | ext1 | 50 | 1.0000 | 0.000 | 0.000 | 0.000 | 0.000 |
| shifted | ext2 | 50 | 1.0000 | 0.000 | 0.000 | 0.000 | 0.000 |
| shifted | method | 50 | 0.9500 | 1000.000 | 0.000 | 0.000 | 0.000 |

## Task Breakdown

| Task | Scenario | Variant | N | Mean Success | Mean Steps | Success / 1k Steps |
|---|---|---|---:|---:|---:|---:|
| button-press-topdown-v3 | nominal | baseline | 5 | 1.0000 | 80.00 | 12.500 |
| button-press-topdown-v3 | nominal | ext1 | 5 | 1.0000 | 80.00 | 12.500 |
| button-press-topdown-v3 | nominal | ext2 | 5 | 1.0000 | 80.00 | 12.500 |
| button-press-topdown-v3 | nominal | method | 5 | 1.0000 | 80.00 | 12.500 |
| button-press-topdown-v3 | shifted | baseline | 5 | 0.2000 | 80.00 | 2.500 |
| button-press-topdown-v3 | shifted | ext1 | 5 | 0.6000 | 80.00 | 7.500 |
| button-press-topdown-v3 | shifted | ext2 | 5 | 0.6000 | 80.00 | 7.500 |
| button-press-topdown-v3 | shifted | method | 5 | 1.0000 | 80.00 | 12.500 |
| button-press-v3 | nominal | baseline | 5 | 1.0000 | 80.00 | 12.500 |
| button-press-v3 | nominal | ext1 | 5 | 1.0000 | 80.00 | 12.500 |
| button-press-v3 | nominal | ext2 | 5 | 1.0000 | 80.00 | 12.500 |
| button-press-v3 | nominal | method | 5 | 1.0000 | 80.00 | 12.500 |
| button-press-v3 | shifted | baseline | 5 | 0.0000 | 80.00 | 0.000 |
| button-press-v3 | shifted | ext1 | 5 | 0.0000 | 80.00 | 0.000 |
| button-press-v3 | shifted | ext2 | 5 | 0.4000 | 80.00 | 5.000 |
| button-press-v3 | shifted | method | 5 | 1.0000 | 80.00 | 12.500 |
| faucet-open-v3 | nominal | baseline | 5 | 1.0000 | 80.00 | 12.500 |
| faucet-open-v3 | nominal | ext1 | 5 | 1.0000 | 80.00 | 12.500 |
| faucet-open-v3 | nominal | ext2 | 5 | 1.0000 | 80.00 | 12.500 |
| faucet-open-v3 | nominal | method | 5 | 1.0000 | 80.00 | 12.500 |
| faucet-open-v3 | shifted | baseline | 5 | 0.0000 | 80.00 | 0.000 |
| faucet-open-v3 | shifted | ext1 | 5 | 0.0000 | 80.00 | 0.000 |
| faucet-open-v3 | shifted | ext2 | 5 | 0.6000 | 80.00 | 7.500 |
| faucet-open-v3 | shifted | method | 5 | 1.0000 | 80.00 | 12.500 |
| hammer-v3 | nominal | baseline | 5 | 1.0000 | 80.00 | 12.500 |
| hammer-v3 | nominal | ext1 | 5 | 1.0000 | 80.00 | 12.500 |
| hammer-v3 | nominal | ext2 | 5 | 1.0000 | 80.00 | 12.500 |
| hammer-v3 | nominal | method | 5 | 1.0000 | 80.00 | 12.500 |
| hammer-v3 | shifted | baseline | 5 | 0.0000 | 80.00 | 0.000 |
| hammer-v3 | shifted | ext1 | 5 | 0.0000 | 80.00 | 0.000 |
| hammer-v3 | shifted | ext2 | 5 | 0.6000 | 80.00 | 7.500 |
| hammer-v3 | shifted | method | 5 | 0.6000 | 80.00 | 7.500 |
| peg-insert-side-v3 | nominal | baseline | 5 | 0.0000 | 80.00 | 0.000 |
| peg-insert-side-v3 | nominal | ext1 | 5 | 0.0000 | 80.00 | 0.000 |
| peg-insert-side-v3 | nominal | ext2 | 5 | 0.2000 | 80.00 | 2.500 |
| peg-insert-side-v3 | nominal | method | 5 | 0.4000 | 80.00 | 5.000 |
| peg-insert-side-v3 | shifted | baseline | 5 | 0.0000 | 80.00 | 0.000 |
| peg-insert-side-v3 | shifted | ext1 | 5 | 0.0000 | 80.00 | 0.000 |
| peg-insert-side-v3 | shifted | ext2 | 5 | 0.0000 | 80.00 | 0.000 |
| peg-insert-side-v3 | shifted | method | 5 | 0.0000 | 80.00 | 0.000 |
| pick-place-v3 | nominal | baseline | 5 | 1.0000 | 80.00 | 12.500 |
| pick-place-v3 | nominal | ext1 | 5 | 1.0000 | 80.00 | 12.500 |
| pick-place-v3 | nominal | ext2 | 5 | 1.0000 | 80.00 | 12.500 |
| pick-place-v3 | nominal | method | 5 | 1.0000 | 80.00 | 12.500 |
| pick-place-v3 | shifted | baseline | 5 | 0.2000 | 80.00 | 2.500 |
| pick-place-v3 | shifted | ext1 | 5 | 0.8000 | 80.00 | 10.000 |
| pick-place-v3 | shifted | ext2 | 5 | 0.8000 | 80.00 | 10.000 |
| pick-place-v3 | shifted | method | 5 | 1.0000 | 80.00 | 12.500 |
| push-v3 | nominal | baseline | 5 | 1.0000 | 80.00 | 12.500 |
| push-v3 | nominal | ext1 | 5 | 1.0000 | 80.00 | 12.500 |
| push-v3 | nominal | ext2 | 5 | 1.0000 | 80.00 | 12.500 |
| push-v3 | nominal | method | 5 | 1.0000 | 80.00 | 12.500 |
| push-v3 | shifted | baseline | 5 | 0.6000 | 80.00 | 7.500 |
| push-v3 | shifted | ext1 | 5 | 0.6000 | 80.00 | 7.500 |
| push-v3 | shifted | ext2 | 5 | 0.8000 | 80.00 | 10.000 |
| push-v3 | shifted | method | 5 | 1.0000 | 80.00 | 12.500 |
| push-wall-v3 | nominal | baseline | 5 | 0.4000 | 80.00 | 5.000 |
| push-wall-v3 | nominal | ext1 | 5 | 0.8000 | 80.00 | 10.000 |
| push-wall-v3 | nominal | ext2 | 5 | 0.4000 | 80.00 | 5.000 |
| push-wall-v3 | nominal | method | 5 | 0.4000 | 80.00 | 5.000 |
| push-wall-v3 | shifted | baseline | 5 | 0.0000 | 80.00 | 0.000 |
| push-wall-v3 | shifted | ext1 | 5 | 0.0000 | 80.00 | 0.000 |
| push-wall-v3 | shifted | ext2 | 5 | 0.0000 | 80.00 | 0.000 |
| push-wall-v3 | shifted | method | 5 | 0.0000 | 80.00 | 0.000 |
| reach-v3 | nominal | baseline | 5 | 1.0000 | 80.00 | 12.500 |
| reach-v3 | nominal | ext1 | 5 | 1.0000 | 80.00 | 12.500 |
| reach-v3 | nominal | ext2 | 5 | 1.0000 | 80.00 | 12.500 |
| reach-v3 | nominal | method | 5 | 1.0000 | 80.00 | 12.500 |
| reach-v3 | shifted | baseline | 5 | 0.4000 | 80.00 | 5.000 |
| reach-v3 | shifted | ext1 | 5 | 0.6000 | 80.00 | 7.500 |
| reach-v3 | shifted | ext2 | 5 | 0.8000 | 80.00 | 10.000 |
| reach-v3 | shifted | method | 5 | 0.8000 | 80.00 | 10.000 |
| soccer-v3 | nominal | baseline | 5 | 0.6000 | 80.00 | 7.500 |
| soccer-v3 | nominal | ext1 | 5 | 0.6000 | 80.00 | 7.500 |
| soccer-v3 | nominal | ext2 | 5 | 0.2000 | 80.00 | 2.500 |
| soccer-v3 | nominal | method | 5 | 0.4000 | 80.00 | 5.000 |
| soccer-v3 | shifted | baseline | 5 | 0.0000 | 80.00 | 0.000 |
| soccer-v3 | shifted | ext1 | 5 | 0.2000 | 80.00 | 2.500 |
| soccer-v3 | shifted | ext2 | 5 | 0.2000 | 80.00 | 2.500 |
| soccer-v3 | shifted | method | 5 | 0.6000 | 80.00 | 7.500 |

## Notes

- Shift profile includes physics randomization: body-mass scale in [0.80, 1.20] and geom-friction scale in [0.80, 1.20] for shifted scenarios.
- Perturbation profiles model latency, dropout, and action corruption. CORE (`method`) adds an adaptive-hysteresis uncertainty gate with monitor/rollback blending.
- Budget parity: all variants use the same per-episode cap (`max_steps=80`); monitor mode does not allocate extra episodes.
- Bounded uncertainty proxy for gating: clamp range [0.0, 5.0].
- This slice is intended as a recognized-benchmark cross-check, not a full benchmark leaderboard run.
