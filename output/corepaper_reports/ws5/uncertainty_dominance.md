# Uncertainty-Dominance Check (Auto-generated)

- Source logs: `output/corepaper_logs/experiments/external_latest, output/corepaper_logs/experiments/robustness_latest, output/corepaper_logs/experiments/software_transfer_latest, output/corepaper_logs/experiments/sim2sim_latest, output/corepaper_logs/experiments/recent_baselines_latest`
- Rows analyzed: 984
- Split: `seed-parity` (train=474, holdout=510)

## Fitted Dominance Envelope (Held-out Evaluation)

| c_u | c_0 | Holdout Coverage | Holdout Max Violation | Holdout MAE | Holdout RMSE |
|---:|---:|---:|---:|---:|---:|
| 1.0191 | 0.0041 | 0.945 | 0.0063 | 0.0049 | 0.0058 |

## Error-vs-Uncertainty Relationship

| Slope | Intercept | Pearson r |
|---:|---:|---:|
| 0.9904 | 0.0011 | 0.9973 |

## Variant Summary

| Variant | N | Mean U | Mean e | Max U | Max e |
|---|---:|---:|---:|---:|---:|
| adaptmanip | 84 | 0.0720 | 0.0723 | 0.1198 | 0.1272 |
| baseline | 165 | 0.0672 | 0.0673 | 0.1399 | 0.1446 |
| constrained_flow | 84 | 0.0707 | 0.0711 | 0.1139 | 0.1195 |
| ext1 | 89 | 0.0735 | 0.0731 | 0.1292 | 0.1351 |
| ext2 | 117 | 0.0620 | 0.0628 | 0.1229 | 0.1288 |
| history_keyframe | 84 | 0.0739 | 0.0742 | 0.1236 | 0.1317 |
| latency_aware | 112 | 0.0619 | 0.0622 | 0.1236 | 0.1276 |
| method | 165 | 0.0543 | 0.0559 | 0.1138 | 0.1240 |
| robust_cp | 84 | 0.0695 | 0.0701 | 0.1167 | 0.1214 |

## Binned Scatter Coordinates (for manuscript figure)

| Bin | Mean U | Mean e | Count |
|---:|---:|---:|---:|
| 1 | 0.000644 | 0.002291 | 211 |
| 2 | 0.024057 | 0.024389 | 27 |
| 3 | 0.044229 | 0.043356 | 32 |
| 4 | 0.060222 | 0.060077 | 172 |
| 5 | 0.076439 | 0.076559 | 275 |
| 6 | 0.101632 | 0.104155 | 20 |
| 7 | 0.112483 | 0.113484 | 157 |
| 8 | 0.128164 | 0.127677 | 90 |
