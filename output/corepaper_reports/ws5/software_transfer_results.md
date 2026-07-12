# Software Transfer Results (Auto-generated)

- Source: `output/corepaper_logs/experiments/software_transfer_latest`
- Nominal baseline mean: 0.7119
- Nominal method mean: 0.7494

| Test | Severity | Baseline Mean | Method Mean | Baseline Drop % | Method Drop % | Criterion | Status |
|---|---|---:|---:|---:|---:|---|---|
| S1 | hard | 0.5884 | 0.6436 | 17.35% | 14.12% | method > baseline under hard long-horizon shift | PASS |
| S1 | mild | 0.6683 | 0.7149 | 6.13% | 4.61% | informational | N/A |
| S2 | high | 0.6259 | 0.6828 | 12.08% | 8.89% | informational | N/A |
| S2 | low | 0.6938 | 0.7349 | 2.55% | 1.94% | informational | N/A |
| S2 | med | 0.6696 | 0.7125 | 5.95% | 4.93% | method drop <= 12% at med temporal jitter | PASS |
| S3 | mild | 0.6852 | 0.7291 | 3.76% | 2.70% | informational | N/A |
| S3 | severe | 0.6444 | 0.6959 | 9.49% | 7.13% | method > baseline and drop <= 18% under severe observation dropout | PASS |

- Required software-transfer criteria pass: YES
