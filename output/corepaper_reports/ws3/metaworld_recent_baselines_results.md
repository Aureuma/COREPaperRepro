# MetaWorld Slice Results (Auto-generated)

- Recognized benchmark: `MetaWorld MT1`
- Config: `config/benchmarks/experiments_metaworld_recent_baselines.json`
- JSON report: `output/corepaper_reports/ws3/metaworld_recent_baselines_results.json`
- Tasks: `reach-v3, push-v3, button-press-v3, button-press-topdown-v3, faucet-open-v3, hammer-v3, pick-place-v3, soccer-v3, peg-insert-side-v3, push-wall-v3`
- Scenarios: `nominal`, `shifted`

## Scenario-Level Summary

| Scenario | Variant | N | Mean Success | Worst-Seed | CVaR40 | Mean Steps | Success / 1k Steps |
|---|---|---:|---:|---:|---:|---:|---:|
| nominal | baseline | 50 | 0.8200 | 0.0000 | 0.5500 | 80.00 | 10.250 |
| nominal | ext1 | 50 | 0.8000 | 0.0000 | 0.5000 | 80.00 | 10.000 |
| nominal | ext2 | 50 | 0.7800 | 0.0000 | 0.4500 | 80.00 | 9.750 |
| nominal | latency_aware | 50 | 0.8400 | 0.0000 | 0.6000 | 80.00 | 10.500 |
| nominal | adaptmanip | 50 | 0.7800 | 0.0000 | 0.4500 | 80.00 | 9.750 |
| nominal | robust_cp | 50 | 0.7600 | 0.0000 | 0.4000 | 80.00 | 9.500 |
| nominal | history_keyframe | 50 | 0.8000 | 0.0000 | 0.5000 | 80.00 | 10.000 |
| nominal | constrained_flow | 50 | 0.8800 | 0.0000 | 0.7000 | 80.00 | 11.000 |
| nominal | method | 50 | 0.7600 | 0.0000 | 0.4000 | 80.00 | 9.500 |
| shifted | baseline | 50 | 0.1400 | 0.0000 | 0.0000 | 80.00 | 1.750 |
| shifted | ext1 | 50 | 0.3000 | 0.0000 | 0.0000 | 80.00 | 3.750 |
| shifted | ext2 | 50 | 0.4800 | 0.0000 | 0.0000 | 80.00 | 6.000 |
| shifted | latency_aware | 50 | 0.7000 | 0.0000 | 0.2500 | 80.00 | 8.750 |
| shifted | adaptmanip | 50 | 0.6200 | 0.0000 | 0.0500 | 80.00 | 7.750 |
| shifted | robust_cp | 50 | 0.6000 | 0.0000 | 0.0000 | 80.00 | 7.500 |
| shifted | history_keyframe | 50 | 0.4600 | 0.0000 | 0.0000 | 80.00 | 5.750 |
| shifted | constrained_flow | 50 | 0.6800 | 0.0000 | 0.2000 | 80.00 | 8.500 |
| shifted | method | 50 | 0.7200 | 0.0000 | 0.3000 | 80.00 | 9.000 |

## Shifted Sample-Efficiency Proxy

| Variant | Episodes | Tasks with Any Success | Mean Success | Mean Steps | Success / 1k Steps | Steps per Success |
|---|---:|---:|---:|---:|---:|---:|
| adaptmanip | 50 | 9/10 | 0.6200 | 80.00 | 7.750 | 129.03 |
| baseline | 50 | 4/10 | 0.1400 | 80.00 | 1.750 | 571.43 |
| constrained_flow | 50 | 8/10 | 0.6800 | 80.00 | 8.500 | 117.65 |
| ext1 | 50 | 6/10 | 0.3000 | 80.00 | 3.750 | 266.67 |
| ext2 | 50 | 8/10 | 0.4800 | 80.00 | 6.000 | 166.67 |
| history_keyframe | 50 | 8/10 | 0.4600 | 80.00 | 5.750 | 173.91 |
| latency_aware | 50 | 9/10 | 0.7000 | 80.00 | 8.750 | 114.29 |
| method | 50 | 9/10 | 0.7200 | 80.00 | 9.000 | 111.11 |
| robust_cp | 50 | 9/10 | 0.6000 | 80.00 | 7.500 | 133.33 |

## Gate Diagnostics

| Scenario | Variant | Episodes | Mean Risk Lambda | Green / 1k | Yellow / 1k | Red / 1k | Conformal Red / 1k |
|---|---|---:|---:|---:|---:|---:|---:|
| nominal | adaptmanip | 50 | 1.0000 | 0.000 | 0.000 | 0.000 | 0.000 |
| nominal | baseline | 50 | 1.0000 | 0.000 | 0.000 | 0.000 | 0.000 |
| nominal | constrained_flow | 50 | 1.0000 | 0.000 | 0.000 | 0.000 | 0.000 |
| nominal | ext1 | 50 | 1.0000 | 0.000 | 0.000 | 0.000 | 0.000 |
| nominal | ext2 | 50 | 1.0000 | 0.000 | 0.000 | 0.000 | 0.000 |
| nominal | history_keyframe | 50 | 1.0000 | 0.000 | 0.000 | 0.000 | 0.000 |
| nominal | latency_aware | 50 | 1.0000 | 0.000 | 0.000 | 0.000 | 0.000 |
| nominal | method | 50 | 1.0000 | 0.000 | 0.000 | 0.000 | 0.000 |
| nominal | robust_cp | 50 | 1.0000 | 0.000 | 0.000 | 0.000 | 0.000 |
| shifted | adaptmanip | 50 | 1.0000 | 0.000 | 0.000 | 0.000 | 0.000 |
| shifted | baseline | 50 | 1.0000 | 0.000 | 0.000 | 0.000 | 0.000 |
| shifted | constrained_flow | 50 | 1.0000 | 0.000 | 0.000 | 0.000 | 0.000 |
| shifted | ext1 | 50 | 1.0000 | 0.000 | 0.000 | 0.000 | 0.000 |
| shifted | ext2 | 50 | 1.0000 | 0.000 | 0.000 | 0.000 | 0.000 |
| shifted | history_keyframe | 50 | 1.0000 | 0.000 | 0.000 | 0.000 | 0.000 |
| shifted | latency_aware | 50 | 1.0000 | 0.000 | 0.000 | 0.000 | 0.000 |
| shifted | method | 50 | 0.9500 | 1000.000 | 0.000 | 0.000 | 0.000 |
| shifted | robust_cp | 50 | 1.0000 | 0.000 | 0.000 | 0.000 | 0.000 |

## Task Breakdown

| Task | Scenario | Variant | N | Mean Success | Mean Steps | Success / 1k Steps |
|---|---|---|---:|---:|---:|---:|
| button-press-topdown-v3 | nominal | adaptmanip | 5 | 1.0000 | 80.00 | 12.500 |
| button-press-topdown-v3 | nominal | baseline | 5 | 1.0000 | 80.00 | 12.500 |
| button-press-topdown-v3 | nominal | constrained_flow | 5 | 1.0000 | 80.00 | 12.500 |
| button-press-topdown-v3 | nominal | ext1 | 5 | 1.0000 | 80.00 | 12.500 |
| button-press-topdown-v3 | nominal | ext2 | 5 | 1.0000 | 80.00 | 12.500 |
| button-press-topdown-v3 | nominal | history_keyframe | 5 | 1.0000 | 80.00 | 12.500 |
| button-press-topdown-v3 | nominal | latency_aware | 5 | 1.0000 | 80.00 | 12.500 |
| button-press-topdown-v3 | nominal | method | 5 | 1.0000 | 80.00 | 12.500 |
| button-press-topdown-v3 | nominal | robust_cp | 5 | 1.0000 | 80.00 | 12.500 |
| button-press-topdown-v3 | shifted | adaptmanip | 5 | 0.2000 | 80.00 | 2.500 |
| button-press-topdown-v3 | shifted | baseline | 5 | 0.2000 | 80.00 | 2.500 |
| button-press-topdown-v3 | shifted | constrained_flow | 5 | 1.0000 | 80.00 | 12.500 |
| button-press-topdown-v3 | shifted | ext1 | 5 | 0.4000 | 80.00 | 5.000 |
| button-press-topdown-v3 | shifted | ext2 | 5 | 0.8000 | 80.00 | 10.000 |
| button-press-topdown-v3 | shifted | history_keyframe | 5 | 0.6000 | 80.00 | 7.500 |
| button-press-topdown-v3 | shifted | latency_aware | 5 | 0.6000 | 80.00 | 7.500 |
| button-press-topdown-v3 | shifted | method | 5 | 0.8000 | 80.00 | 10.000 |
| button-press-topdown-v3 | shifted | robust_cp | 5 | 0.6000 | 80.00 | 7.500 |
| button-press-v3 | nominal | adaptmanip | 5 | 1.0000 | 80.00 | 12.500 |
| button-press-v3 | nominal | baseline | 5 | 1.0000 | 80.00 | 12.500 |
| button-press-v3 | nominal | constrained_flow | 5 | 1.0000 | 80.00 | 12.500 |
| button-press-v3 | nominal | ext1 | 5 | 1.0000 | 80.00 | 12.500 |
| button-press-v3 | nominal | ext2 | 5 | 1.0000 | 80.00 | 12.500 |
| button-press-v3 | nominal | history_keyframe | 5 | 1.0000 | 80.00 | 12.500 |
| button-press-v3 | nominal | latency_aware | 5 | 1.0000 | 80.00 | 12.500 |
| button-press-v3 | nominal | method | 5 | 1.0000 | 80.00 | 12.500 |
| button-press-v3 | nominal | robust_cp | 5 | 1.0000 | 80.00 | 12.500 |
| button-press-v3 | shifted | adaptmanip | 5 | 1.0000 | 80.00 | 12.500 |
| button-press-v3 | shifted | baseline | 5 | 0.0000 | 80.00 | 0.000 |
| button-press-v3 | shifted | constrained_flow | 5 | 1.0000 | 80.00 | 12.500 |
| button-press-v3 | shifted | ext1 | 5 | 0.4000 | 80.00 | 5.000 |
| button-press-v3 | shifted | ext2 | 5 | 0.6000 | 80.00 | 7.500 |
| button-press-v3 | shifted | history_keyframe | 5 | 0.6000 | 80.00 | 7.500 |
| button-press-v3 | shifted | latency_aware | 5 | 1.0000 | 80.00 | 12.500 |
| button-press-v3 | shifted | method | 5 | 1.0000 | 80.00 | 12.500 |
| button-press-v3 | shifted | robust_cp | 5 | 0.8000 | 80.00 | 10.000 |
| faucet-open-v3 | nominal | adaptmanip | 5 | 1.0000 | 80.00 | 12.500 |
| faucet-open-v3 | nominal | baseline | 5 | 1.0000 | 80.00 | 12.500 |
| faucet-open-v3 | nominal | constrained_flow | 5 | 1.0000 | 80.00 | 12.500 |
| faucet-open-v3 | nominal | ext1 | 5 | 1.0000 | 80.00 | 12.500 |
| faucet-open-v3 | nominal | ext2 | 5 | 0.8000 | 80.00 | 10.000 |
| faucet-open-v3 | nominal | history_keyframe | 5 | 0.8000 | 80.00 | 10.000 |
| faucet-open-v3 | nominal | latency_aware | 5 | 1.0000 | 80.00 | 12.500 |
| faucet-open-v3 | nominal | method | 5 | 1.0000 | 80.00 | 12.500 |
| faucet-open-v3 | nominal | robust_cp | 5 | 1.0000 | 80.00 | 12.500 |
| faucet-open-v3 | shifted | adaptmanip | 5 | 1.0000 | 80.00 | 12.500 |
| faucet-open-v3 | shifted | baseline | 5 | 0.0000 | 80.00 | 0.000 |
| faucet-open-v3 | shifted | constrained_flow | 5 | 0.6000 | 80.00 | 7.500 |
| faucet-open-v3 | shifted | ext1 | 5 | 0.0000 | 80.00 | 0.000 |
| faucet-open-v3 | shifted | ext2 | 5 | 0.6000 | 80.00 | 7.500 |
| faucet-open-v3 | shifted | history_keyframe | 5 | 0.4000 | 80.00 | 5.000 |
| faucet-open-v3 | shifted | latency_aware | 5 | 1.0000 | 80.00 | 12.500 |
| faucet-open-v3 | shifted | method | 5 | 1.0000 | 80.00 | 12.500 |
| faucet-open-v3 | shifted | robust_cp | 5 | 0.8000 | 80.00 | 10.000 |
| hammer-v3 | nominal | adaptmanip | 5 | 1.0000 | 80.00 | 12.500 |
| hammer-v3 | nominal | baseline | 5 | 1.0000 | 80.00 | 12.500 |
| hammer-v3 | nominal | constrained_flow | 5 | 1.0000 | 80.00 | 12.500 |
| hammer-v3 | nominal | ext1 | 5 | 1.0000 | 80.00 | 12.500 |
| hammer-v3 | nominal | ext2 | 5 | 1.0000 | 80.00 | 12.500 |
| hammer-v3 | nominal | history_keyframe | 5 | 1.0000 | 80.00 | 12.500 |
| hammer-v3 | nominal | latency_aware | 5 | 1.0000 | 80.00 | 12.500 |
| hammer-v3 | nominal | method | 5 | 1.0000 | 80.00 | 12.500 |
| hammer-v3 | nominal | robust_cp | 5 | 1.0000 | 80.00 | 12.500 |
| hammer-v3 | shifted | adaptmanip | 5 | 1.0000 | 80.00 | 12.500 |
| hammer-v3 | shifted | baseline | 5 | 0.0000 | 80.00 | 0.000 |
| hammer-v3 | shifted | constrained_flow | 5 | 1.0000 | 80.00 | 12.500 |
| hammer-v3 | shifted | ext1 | 5 | 0.0000 | 80.00 | 0.000 |
| hammer-v3 | shifted | ext2 | 5 | 0.6000 | 80.00 | 7.500 |
| hammer-v3 | shifted | history_keyframe | 5 | 0.2000 | 80.00 | 2.500 |
| hammer-v3 | shifted | latency_aware | 5 | 0.6000 | 80.00 | 7.500 |
| hammer-v3 | shifted | method | 5 | 0.8000 | 80.00 | 10.000 |
| hammer-v3 | shifted | robust_cp | 5 | 0.4000 | 80.00 | 5.000 |
| peg-insert-side-v3 | nominal | adaptmanip | 5 | 0.0000 | 80.00 | 0.000 |
| peg-insert-side-v3 | nominal | baseline | 5 | 0.2000 | 80.00 | 2.500 |
| peg-insert-side-v3 | nominal | constrained_flow | 5 | 0.4000 | 80.00 | 5.000 |
| peg-insert-side-v3 | nominal | ext1 | 5 | 0.2000 | 80.00 | 2.500 |
| peg-insert-side-v3 | nominal | ext2 | 5 | 0.0000 | 80.00 | 0.000 |
| peg-insert-side-v3 | nominal | history_keyframe | 5 | 0.0000 | 80.00 | 0.000 |
| peg-insert-side-v3 | nominal | latency_aware | 5 | 0.4000 | 80.00 | 5.000 |
| peg-insert-side-v3 | nominal | method | 5 | 0.0000 | 80.00 | 0.000 |
| peg-insert-side-v3 | nominal | robust_cp | 5 | 0.0000 | 80.00 | 0.000 |
| peg-insert-side-v3 | shifted | adaptmanip | 5 | 0.0000 | 80.00 | 0.000 |
| peg-insert-side-v3 | shifted | baseline | 5 | 0.0000 | 80.00 | 0.000 |
| peg-insert-side-v3 | shifted | constrained_flow | 5 | 0.0000 | 80.00 | 0.000 |
| peg-insert-side-v3 | shifted | ext1 | 5 | 0.0000 | 80.00 | 0.000 |
| peg-insert-side-v3 | shifted | ext2 | 5 | 0.0000 | 80.00 | 0.000 |
| peg-insert-side-v3 | shifted | history_keyframe | 5 | 0.0000 | 80.00 | 0.000 |
| peg-insert-side-v3 | shifted | latency_aware | 5 | 0.0000 | 80.00 | 0.000 |
| peg-insert-side-v3 | shifted | method | 5 | 0.0000 | 80.00 | 0.000 |
| peg-insert-side-v3 | shifted | robust_cp | 5 | 0.0000 | 80.00 | 0.000 |
| pick-place-v3 | nominal | adaptmanip | 5 | 1.0000 | 80.00 | 12.500 |
| pick-place-v3 | nominal | baseline | 5 | 1.0000 | 80.00 | 12.500 |
| pick-place-v3 | nominal | constrained_flow | 5 | 1.0000 | 80.00 | 12.500 |
| pick-place-v3 | nominal | ext1 | 5 | 1.0000 | 80.00 | 12.500 |
| pick-place-v3 | nominal | ext2 | 5 | 1.0000 | 80.00 | 12.500 |
| pick-place-v3 | nominal | history_keyframe | 5 | 1.0000 | 80.00 | 12.500 |
| pick-place-v3 | nominal | latency_aware | 5 | 1.0000 | 80.00 | 12.500 |
| pick-place-v3 | nominal | method | 5 | 1.0000 | 80.00 | 12.500 |
| pick-place-v3 | nominal | robust_cp | 5 | 1.0000 | 80.00 | 12.500 |
| pick-place-v3 | shifted | adaptmanip | 5 | 1.0000 | 80.00 | 12.500 |
| pick-place-v3 | shifted | baseline | 5 | 0.6000 | 80.00 | 7.500 |
| pick-place-v3 | shifted | constrained_flow | 5 | 1.0000 | 80.00 | 12.500 |
| pick-place-v3 | shifted | ext1 | 5 | 0.8000 | 80.00 | 10.000 |
| pick-place-v3 | shifted | ext2 | 5 | 1.0000 | 80.00 | 12.500 |
| pick-place-v3 | shifted | history_keyframe | 5 | 1.0000 | 80.00 | 12.500 |
| pick-place-v3 | shifted | latency_aware | 5 | 1.0000 | 80.00 | 12.500 |
| pick-place-v3 | shifted | method | 5 | 1.0000 | 80.00 | 12.500 |
| pick-place-v3 | shifted | robust_cp | 5 | 1.0000 | 80.00 | 12.500 |
| push-v3 | nominal | adaptmanip | 5 | 1.0000 | 80.00 | 12.500 |
| push-v3 | nominal | baseline | 5 | 1.0000 | 80.00 | 12.500 |
| push-v3 | nominal | constrained_flow | 5 | 1.0000 | 80.00 | 12.500 |
| push-v3 | nominal | ext1 | 5 | 0.8000 | 80.00 | 10.000 |
| push-v3 | nominal | ext2 | 5 | 1.0000 | 80.00 | 12.500 |
| push-v3 | nominal | history_keyframe | 5 | 1.0000 | 80.00 | 12.500 |
| push-v3 | nominal | latency_aware | 5 | 1.0000 | 80.00 | 12.500 |
| push-v3 | nominal | method | 5 | 1.0000 | 80.00 | 12.500 |
| push-v3 | nominal | robust_cp | 5 | 1.0000 | 80.00 | 12.500 |
| push-v3 | shifted | adaptmanip | 5 | 0.6000 | 80.00 | 7.500 |
| push-v3 | shifted | baseline | 5 | 0.2000 | 80.00 | 2.500 |
| push-v3 | shifted | constrained_flow | 5 | 1.0000 | 80.00 | 12.500 |
| push-v3 | shifted | ext1 | 5 | 0.2000 | 80.00 | 2.500 |
| push-v3 | shifted | ext2 | 5 | 0.2000 | 80.00 | 2.500 |
| push-v3 | shifted | history_keyframe | 5 | 0.8000 | 80.00 | 10.000 |
| push-v3 | shifted | latency_aware | 5 | 1.0000 | 80.00 | 12.500 |
| push-v3 | shifted | method | 5 | 1.0000 | 80.00 | 12.500 |
| push-v3 | shifted | robust_cp | 5 | 1.0000 | 80.00 | 12.500 |
| push-wall-v3 | nominal | adaptmanip | 5 | 0.2000 | 80.00 | 2.500 |
| push-wall-v3 | nominal | baseline | 5 | 0.4000 | 80.00 | 5.000 |
| push-wall-v3 | nominal | constrained_flow | 5 | 0.8000 | 80.00 | 10.000 |
| push-wall-v3 | nominal | ext1 | 5 | 0.4000 | 80.00 | 5.000 |
| push-wall-v3 | nominal | ext2 | 5 | 0.6000 | 80.00 | 7.500 |
| push-wall-v3 | nominal | history_keyframe | 5 | 0.8000 | 80.00 | 10.000 |
| push-wall-v3 | nominal | latency_aware | 5 | 0.6000 | 80.00 | 7.500 |
| push-wall-v3 | nominal | method | 5 | 0.4000 | 80.00 | 5.000 |
| push-wall-v3 | nominal | robust_cp | 5 | 0.0000 | 80.00 | 0.000 |
| push-wall-v3 | shifted | adaptmanip | 5 | 0.2000 | 80.00 | 2.500 |
| push-wall-v3 | shifted | baseline | 5 | 0.0000 | 80.00 | 0.000 |
| push-wall-v3 | shifted | constrained_flow | 5 | 0.0000 | 80.00 | 0.000 |
| push-wall-v3 | shifted | ext1 | 5 | 0.2000 | 80.00 | 2.500 |
| push-wall-v3 | shifted | ext2 | 5 | 0.0000 | 80.00 | 0.000 |
| push-wall-v3 | shifted | history_keyframe | 5 | 0.0000 | 80.00 | 0.000 |
| push-wall-v3 | shifted | latency_aware | 5 | 0.2000 | 80.00 | 2.500 |
| push-wall-v3 | shifted | method | 5 | 0.2000 | 80.00 | 2.500 |
| push-wall-v3 | shifted | robust_cp | 5 | 0.2000 | 80.00 | 2.500 |
| reach-v3 | nominal | adaptmanip | 5 | 1.0000 | 80.00 | 12.500 |
| reach-v3 | nominal | baseline | 5 | 1.0000 | 80.00 | 12.500 |
| reach-v3 | nominal | constrained_flow | 5 | 1.0000 | 80.00 | 12.500 |
| reach-v3 | nominal | ext1 | 5 | 1.0000 | 80.00 | 12.500 |
| reach-v3 | nominal | ext2 | 5 | 1.0000 | 80.00 | 12.500 |
| reach-v3 | nominal | history_keyframe | 5 | 1.0000 | 80.00 | 12.500 |
| reach-v3 | nominal | latency_aware | 5 | 1.0000 | 80.00 | 12.500 |
| reach-v3 | nominal | method | 5 | 1.0000 | 80.00 | 12.500 |
| reach-v3 | nominal | robust_cp | 5 | 1.0000 | 80.00 | 12.500 |
| reach-v3 | shifted | adaptmanip | 5 | 1.0000 | 80.00 | 12.500 |
| reach-v3 | shifted | baseline | 5 | 0.4000 | 80.00 | 5.000 |
| reach-v3 | shifted | constrained_flow | 5 | 0.8000 | 80.00 | 10.000 |
| reach-v3 | shifted | ext1 | 5 | 1.0000 | 80.00 | 12.500 |
| reach-v3 | shifted | ext2 | 5 | 0.8000 | 80.00 | 10.000 |
| reach-v3 | shifted | history_keyframe | 5 | 0.6000 | 80.00 | 7.500 |
| reach-v3 | shifted | latency_aware | 5 | 1.0000 | 80.00 | 12.500 |
| reach-v3 | shifted | method | 5 | 0.8000 | 80.00 | 10.000 |
| reach-v3 | shifted | robust_cp | 5 | 1.0000 | 80.00 | 12.500 |
| soccer-v3 | nominal | adaptmanip | 5 | 0.6000 | 80.00 | 7.500 |
| soccer-v3 | nominal | baseline | 5 | 0.6000 | 80.00 | 7.500 |
| soccer-v3 | nominal | constrained_flow | 5 | 0.6000 | 80.00 | 7.500 |
| soccer-v3 | nominal | ext1 | 5 | 0.6000 | 80.00 | 7.500 |
| soccer-v3 | nominal | ext2 | 5 | 0.4000 | 80.00 | 5.000 |
| soccer-v3 | nominal | history_keyframe | 5 | 0.4000 | 80.00 | 5.000 |
| soccer-v3 | nominal | latency_aware | 5 | 0.4000 | 80.00 | 5.000 |
| soccer-v3 | nominal | method | 5 | 0.2000 | 80.00 | 2.500 |
| soccer-v3 | nominal | robust_cp | 5 | 0.6000 | 80.00 | 7.500 |
| soccer-v3 | shifted | adaptmanip | 5 | 0.2000 | 80.00 | 2.500 |
| soccer-v3 | shifted | baseline | 5 | 0.0000 | 80.00 | 0.000 |
| soccer-v3 | shifted | constrained_flow | 5 | 0.4000 | 80.00 | 5.000 |
| soccer-v3 | shifted | ext1 | 5 | 0.0000 | 80.00 | 0.000 |
| soccer-v3 | shifted | ext2 | 5 | 0.2000 | 80.00 | 2.500 |
| soccer-v3 | shifted | history_keyframe | 5 | 0.4000 | 80.00 | 5.000 |
| soccer-v3 | shifted | latency_aware | 5 | 0.6000 | 80.00 | 7.500 |
| soccer-v3 | shifted | method | 5 | 0.6000 | 80.00 | 7.500 |
| soccer-v3 | shifted | robust_cp | 5 | 0.2000 | 80.00 | 2.500 |

## Notes

- Shift profile includes physics randomization: body-mass scale in [0.80, 1.20] and geom-friction scale in [0.80, 1.20] for shifted scenarios.
- Perturbation profiles model latency, dropout, and action corruption. CORE (`method`) adds an adaptive-hysteresis uncertainty gate with monitor/rollback blending.
- Budget parity: all variants use the same per-episode cap (`max_steps=80`); monitor mode does not allocate extra episodes.
- Bounded uncertainty proxy for gating: clamp range [0.0, 5.0].
- This slice is intended as a recognized-benchmark cross-check, not a full benchmark leaderboard run.
