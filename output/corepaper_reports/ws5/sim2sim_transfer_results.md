# Sim-to-Sim Transfer Results (Auto-generated)

- Source logs: `output/corepaper_logs/experiments/sim2sim_latest`
- Nominal baseline mean: 0.7119
- Nominal ext2 mean: N/A
- Nominal latency_aware mean: N/A
- Nominal method mean: 0.7494
- Source engine: `mujoco`
- Thresholds: method drop <= 12.0%, gap retention >= 0.70

| Engine | N | Baseline Mean | ext2 Mean | latency_aware Mean | Method Mean | Method-Baseline | Method-ext2 | Method-latency_aware | Baseline Drop % | ext2 Drop % | latency_aware Drop % | Method Drop % | Method > Baseline | Method > ext2 | Method > latency_aware |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| isaac | 14 | 0.6258 | 0.6659 | 0.6666 | 0.6767 | +0.0509 | +0.0108 | +0.0101 | 12.10% | N/A | N/A | 9.70% | YES | YES | YES |
| mujoco | 14 | 0.7122 | 0.7432 | 0.7417 | 0.7487 | +0.0365 | +0.0055 | +0.0070 | -0.03% | N/A | N/A | 0.09% | YES | YES | YES |

| Engine | Method>Baseline | Method>ext2 | Method>latency_aware | Drop<=Limit | GapRet(base) | GapRet(ext2) | GapRet(latency_aware) | Status |
|---|---|---|---|---|---|---|---|---|
| isaac | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| mujoco | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |

- Required sim-to-sim criteria pass: YES
