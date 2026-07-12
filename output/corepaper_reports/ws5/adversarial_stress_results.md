# Adversarial Stress Results (Auto-generated)

- Config: `config/benchmarks/experiments_adversarial_stress_generated.json`
- Scenario count: `12`
- Seed count: `8`

## Stress Aggregate

| Variant | N | Mean | Worst | CVaR40 |
|---|---:|---:|---:|---:|
| baseline | 96 | 0.4547 | 0.4094 | 0.4365 |
| ext2 | 96 | 0.5122 | 0.4744 | 0.4961 |
| latency_aware | 96 | 0.5152 | 0.4730 | 0.4976 |
| adaptmanip | 96 | 0.5170 | 0.4751 | 0.5008 |
| robust_cp | 96 | 0.5222 | 0.4853 | 0.5069 |
| method | 96 | 0.5478 | 0.5085 | 0.5326 |

## Reference Comparisons

| Comparison | Delta Mean | Delta Worst | Delta CVaR40 | Delta CI95 | p-value |
|---|---:|---:|---:|---:|---:|
| method vs baseline | +0.0931 | +0.0992 | +0.0961 | ±0.0047 | 0.000000 |
| method vs ext2 | +0.0356 | +0.0341 | +0.0365 | ±0.0043 | 0.000000 |
| method vs latency_aware | +0.0326 | +0.0356 | +0.0350 | ±0.0045 | 0.000000 |
| method vs adaptmanip | +0.0308 | +0.0334 | +0.0318 | ±0.0044 | 0.000000 |
| method vs robust_cp | +0.0256 | +0.0233 | +0.0257 | ±0.0042 | 0.000000 |

## Stress Coverage Matrix

| Component | Zero | Mid | High |
|---|---:|---:|---:|
| contact | 0 | 3 | 9 |
| dropout | 0 | 2 | 10 |
| latency | 0 | 1 | 11 |
| physics | 1 | 3 | 8 |
| sensor | 1 | 4 | 7 |
