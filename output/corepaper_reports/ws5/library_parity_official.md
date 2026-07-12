# Official Library Parity Audit

- Generated (UTC): `2026-03-02T07:31:31Z`
- Policy: clone -> compare -> cleanup (temporary clones removed).
- Overall status: `pass`

## Repo Checks

- `stable-baselines3` (cc20f5af0cfe): status=`pass` objective=`PPO clipped surrogate objective`
  - Source: `https://github.com/DLR-RM/stable-baselines3.git` :: `stable_baselines3/ppo/ppo.py`
  - Required symbols all found.
- `ray-rllib` (a6faf23e6f47): status=`pass` objective=`SAC entropy-regularized actor-critic objective`
  - Source: `https://github.com/ray-project/ray.git` :: `rllib/algorithms/sac/sac.py`
  - Required symbols all found.

## Local Mapping

- Source file: `scripts/experiments/library_lane_benchmark.py`
- Variant `method` present: `True`
- Variant `sb3_ppo` present: `True`
- Variant `rllib_sac` present: `True`

## Runtime Probe

- SB3 backend: `fallback`
- RLlib backend: `fallback`
