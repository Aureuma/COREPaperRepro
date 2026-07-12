# Statistical Power Report (Auto-generated)

- Source effects: `output/corepaper_reports/ws5/statistical_effects.json`
- Target power: 0.80
- Alpha: 0.05 (two-sided)
- Conservative sigma floor: 0.0050

| Comparison | Delta Mean | Cohen's d | Pooled Sigma (est) | N current | Power@N (est) | N rec. (est) | Power@N (conservative) | N rec. (conservative) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| method vs baseline | +0.0375 | 16.059 | 0.0023 | 5 | 1.000 | 2 | 1.000 | 2 |
| method vs ext1 | +0.0186 | 13.082 | 0.0014 | 5 | 1.000 | 2 | 1.000 | 2 |
| method vs ext2 | +0.0054 | 2.488 | 0.0022 | 5 | 0.976 | 3 | 0.400 | 14 |

## Interpretation

- Use this as planning guidance for seed budget. Small deltas with lower effect size need larger `N` even when point estimates are positive.
- Current estimates are model-based approximations and should be treated as conservative planning signals, not definitive guarantees.
