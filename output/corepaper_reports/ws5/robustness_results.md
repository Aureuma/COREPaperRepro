# Robustness Results (Auto-generated)

- Source: `output/corepaper_logs/experiments/robustness_latest`
- Nominal baseline mean: 0.7119
- Nominal method mean: 0.7494

| Test | Severity | Baseline Mean | Method Mean | Baseline Drop % | Method Drop % | Criterion | Status |
|---|---|---:|---:|---:|---:|---|---|
| R1 | high | 0.6187 | 0.6762 | 13.09% | 9.76% | informational | N/A |
| R1 | low | 0.6927 | 0.7340 | 2.70% | 2.05% | informational | N/A |
| R1 | med | 0.6683 | 0.7151 | 6.13% | 4.57% | method drop <= 10% at med | PASS |
| R2 | high | 0.6311 | 0.6871 | 11.36% | 8.32% | informational | N/A |
| R2 | low | 0.6915 | 0.7341 | 2.87% | 2.04% | informational | N/A |
| R2 | med | 0.6689 | 0.7138 | 6.05% | 4.75% | method drop <= 12% at med | PASS |
| R3 | mild | 0.6885 | 0.7277 | 3.29% | 2.90% | method > baseline | PASS |
| R3 | severe | 0.6453 | 0.6950 | 9.37% | 7.25% | method > baseline | PASS |
| R4 | hard | 0.5724 | 0.6300 | 19.60% | 15.94% | method >= baseline | PASS |

- Required robustness criteria pass: YES
