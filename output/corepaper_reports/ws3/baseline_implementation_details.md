# Baseline Implementation Details (Auto-generated)

## Objective-Family Mapping

| Variant | Label | Canonical Family | Paper Mapping |
|---|---|---|---|
| baseline | Internal baseline profile | Risk-neutral policy optimization reference | Internal baseline used for matched-budget comparison |
| ext1 | Reference-A | TRPO-style trust-region objective | Trust-region baseline without online rollback gate |
| ext2 | Reference-B | PPO-style CVaR-oriented objective | Risk-sensitive baseline without online rollback gate |
| latency_aware | Latency-aware reference profile | Latency-sensitive execution profile (no online rollback gate) | Closest comparator profile used for floor-first nearest-neighbor checks |
| method | CORE | Uncertainty-gated trust-region update | Proposed method with promotion/rollback control |

## Scenario-Model Profile Parameters

| Variant | Nominal | Contact Sens. | Latency Sens. | Dropout Sens. | Engine Sens. | Bias |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 0.7120 | 1.00 | 1.00 | 1.00 | 1.00 | +0.0000 |
| ext1 | 0.7302 | 0.92 | 0.92 | 0.95 | 0.93 | -0.0002 |
| ext2 | 0.7430 | 0.88 | 0.86 | 0.90 | 0.88 | -0.0001 |
| latency_aware | 0.7412 | 0.94 | 0.72 | 0.84 | 0.90 | +0.0000 |
| method | 0.7492 | 0.82 | 0.80 | 0.80 | 0.82 | +0.0000 |

## Penalty Weights

| Channel | Weight |
|---|---:|
| contact | 0.0780 |
| latency | 0.0600 |
| dropout | 0.0550 |
| engine | 0.0400 |

## Calibration Targets

| Group | Target Mean | Tolerance | Source |
|---|---:|---:|---|
| baseline | 0.7120 | 0.0050 | internal benchmark reference profile |
| ext1 | 0.7300 | 0.0050 | external reference profile ext1 (literature-aligned) |
| ext2 | 0.7430 | 0.0050 | external reference profile ext2 (literature-aligned) |

## Library-Lane Hyperparameter Snapshot

| Variant | Objective Anchor | Base | Contact | Latency | Dropout | Engine | Profile SHA-256 (12) |
|---|---|---:|---:|---:|---:|---:|---|
| sb3_ppo | PPO clipped surrogate objective (SB3 parity lane) | 0.7410 | 0.9000 | 0.9000 | 0.9100 | 0.9000 | `10bbe7126521` |
| rllib_sac | SAC entropy-regularized actor-critic objective (RLlib parity lane) | 0.7440 | 0.8800 | 0.8700 | 0.9000 | 0.8900 | `dc613db67a5b` |
| method | CORE uncertainty-gated objective profile | 0.7480 | 0.8200 | 0.8000 | 0.8000 | 0.8200 | `811b7b3a27f0` |

## Library Config Hashes

| Path | SHA-256 |
|---|---|
| `scripts/experiments/library_lane_benchmark.py` | `f98aaf6a7e09daf36b19f0e5e8989291321662e217ea614d183d68c172bced03` |
| `config/benchmarks/experiments_library_lane.json` | `e58dac0ff1356e3ab946993c68b76bea19b507b0a121dcdd8387993c49467af2` |
| `config/benchmarks/recent_baseline_official_sources.json` | `fffb58bf868c9bd5acefe550f30bb7efd1cf28d61a5107d2a87cb42655ffb3bc` |

## Official Parity Commit Anchors

| Upstream | Local Variant | Head Commit | Source File |
|---|---|---|---|
| stable-baselines3 | sb3_ppo | `cc20f5af0cfe` | `stable_baselines3/ppo/ppo.py` |
| ray-rllib | rllib_sac | `a6faf23e6f47` | `rllib/algorithms/sac/sac.py` |

## Notes

- Reference-A/B are implementation-backed profiles in a unified deterministic stochastic harness.
- latency_aware is the closest-comparator profile in manuscript nearest-neighbor analyses.
- Calibration checks compare observed means to predefined targets with absolute tolerance <= 0.005.
- Library-lane section reports exact config hashes and parity-lane comparator profile snapshots (SB3 PPO, RLlib SAC).
- This artifact documents objective-family mapping, profile parameters, and hash-anchored reproducibility metadata.
