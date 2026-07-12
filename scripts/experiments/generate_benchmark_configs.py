#!/usr/bin/env python3
"""Generate experiment suite configs for smoke, baselines, ablations, and stress suites."""

from __future__ import annotations

import json
import pathlib
from typing import Dict, List, Tuple


ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "config/benchmarks"
SMOKE_CONFIG = ROOT / "config/experiments_smoke.json"
METAWORLD_PHYSICS_RANDOMIZATION = {
    "enabled": True,
    "mass_scale_range": [0.8, 1.2],
    "friction_scale_range": [0.8, 1.2],
}


def run_entry(run_id: str, variant: str, seed: int, scenario: str = "nominal") -> Dict:
    cmd = (
        "python3 scripts/experiments/software_benchmark.py "
        f"--run-id {run_id} --variant {variant} --scenario {scenario} --seed {seed}"
    )
    return {"id": run_id, "command": cmd, "expected_status": 0}


def run_entry_with_script(
    script: str,
    run_id: str,
    variant: str,
    seed: int,
    scenario: str = "nominal",
    extra_args: str = "",
) -> Dict:
    cmd = (
        f"python3 {script} "
        f"--run-id {run_id} --variant {variant} --scenario {scenario} --seed {seed}"
    )
    if extra_args:
        cmd = f"{cmd} {extra_args.strip()}"
    return {"id": run_id, "command": cmd, "expected_status": 0}


def build_smoke_config() -> Dict:
    runs: List[Dict] = []
    for group in ("baseline", "method"):
        for seed in range(1, 6):
            runs.append(run_entry(f"{group}-s{seed}", group, seed))
    return {"suite_name": "ws3-smoke", "runs": runs}


def build_external_config(seed_end: int = 5, suite_name: str = "ws3-external-baselines") -> Dict:
    runs: List[Dict] = []
    for group in ("baseline", "method", "ext1", "ext2"):
        for seed in range(1, seed_end + 1):
            runs.append(run_entry(f"{group}-s{seed}", group, seed))
    return {"suite_name": suite_name, "runs": runs}


def build_ablation_config() -> Dict:
    variants = (
        "method_full",
        "no_history",
        "no_history_no_feedback",
        "no_robust_reg",
        "no_feedback_gating",
    )
    runs: List[Dict] = []
    for group in variants:
        for seed in range(1, 6):
            runs.append(run_entry(f"{group}-s{seed}", group, seed))
    return {"suite_name": "ws5-ablation", "runs": runs}


def build_robustness_config() -> Dict:
    rows: List[Tuple[str, str]] = [
        ("R1", "low"),
        ("R1", "med"),
        ("R1", "high"),
        ("R2", "low"),
        ("R2", "med"),
        ("R2", "high"),
        ("R3", "mild"),
        ("R3", "severe"),
        ("R4", "hard"),
    ]
    runs: List[Dict] = []
    for test, sev in rows:
        scenario = f"{test}-{sev}"
        for seed in range(1, 4):
            runs.append(run_entry(f"{scenario}-baseline-s{seed}", "baseline", seed, scenario=scenario))
        for seed in range(1, 4):
            runs.append(run_entry(f"{scenario}-method-s{seed}", "method", seed, scenario=scenario))
    return {"suite_name": "ws5-robustness", "runs": runs}


def build_software_transfer_config() -> Dict:
    rows: List[Tuple[str, str]] = [
        ("S1", "mild"),
        ("S1", "hard"),
        ("S2", "low"),
        ("S2", "med"),
        ("S2", "high"),
        ("S3", "mild"),
        ("S3", "severe"),
    ]
    runs: List[Dict] = []
    for test, sev in rows:
        scenario = f"{test}-{sev}"
        for seed in range(1, 4):
            runs.append(run_entry(f"{scenario}-baseline-s{seed}", "baseline", seed, scenario=scenario))
        for seed in range(1, 4):
            runs.append(run_entry(f"{scenario}-method-s{seed}", "method", seed, scenario=scenario))
    return {"suite_name": "ws5-software-transfer", "runs": runs}


def build_sim2sim_config(seed_end: int = 14) -> Dict:
    engines = ("mujoco", "isaac")
    variants = ("baseline", "ext2", "latency_aware", "method")
    runs: List[Dict] = []
    for engine in engines:
        scenario = f"SIM-{engine}"
        for variant in variants:
            for seed in range(1, seed_end + 1):
                runs.append(run_entry(f"{scenario}-{variant}-s{seed}", variant, seed, scenario=scenario))
    return {"suite_name": "ws5-sim2sim-transfer", "runs": runs}


def build_recent_baseline_config(seed_end: int = 14) -> Dict:
    scenarios = ("nominal", "R4-hard", "S1-hard", "S2-high", "S3-severe", "SIM-isaac")
    variants = (
        "baseline",
        "ext1",
        "ext2",
        "latency_aware",
        "adaptmanip",
        "robust_cp",
        "history_keyframe",
        "constrained_flow",
        "method",
    )
    runs: List[Dict] = []
    for scenario in scenarios:
        for variant in variants:
            for seed in range(1, seed_end + 1):
                run_id = f"recent-{scenario}-{variant}-s{seed}"
                runs.append(run_entry(run_id, variant, seed, scenario=scenario))
    return {"suite_name": "ws5-recent-paper-baselines", "runs": runs}


def build_training_backed_recent_config(seed_end: int = 8) -> Dict:
    scenarios = ("nominal", "R4-hard", "S1-hard", "S2-high", "S3-severe", "SIM-isaac")
    variants = ("baseline", "ext2", "latency_aware", "adaptmanip", "robust_cp", "method")
    runs: List[Dict] = []
    for scenario in scenarios:
        for variant in variants:
            for seed in range(1, seed_end + 1):
                run_id = f"train-{scenario}-{variant}-s{seed}"
                runs.append(
                    run_entry_with_script(
                        "scripts/experiments/training_backed_benchmark.py",
                        run_id=run_id,
                        variant=variant,
                        seed=seed,
                        scenario=scenario,
                        extra_args="--train-steps 80 --eval-episodes 50",
                    )
                )
    return {"suite_name": "ws5-training-backed-recent", "runs": runs}


def build_library_lane_config(seed_end: int = 10) -> Dict:
    scenarios = ("nominal", "R4-hard", "S1-hard", "S2-high", "S3-severe", "SIM-isaac")
    variants = ("sb3_ppo", "rllib_sac", "method")
    runs: List[Dict] = []
    for scenario in scenarios:
        for variant in variants:
            for seed in range(1, seed_end + 1):
                run_id = f"lib-{scenario}-{variant}-s{seed}"
                runs.append(
                    run_entry_with_script(
                        "scripts/experiments/library_lane_benchmark.py",
                        run_id=run_id,
                        variant=variant,
                        seed=seed,
                        scenario=scenario,
                        extra_args="--backend auto",
                    )
                )
    return {"suite_name": "ws5-library-lane", "runs": runs}


def build_o2o_proxy_config(seed_end: int = 10) -> Dict:
    scenarios = ("nominal", "R4-hard", "S1-hard", "S2-high", "S3-severe", "SIM-isaac")
    variants = ("baseline", "ext2", "latency_aware", "adaptmanip", "robust_cp", "method")
    runs: List[Dict] = []
    for scenario in scenarios:
        for variant in variants:
            for seed in range(1, seed_end + 1):
                run_id = f"o2o-{scenario}-{variant}-s{seed}"
                runs.append(
                    run_entry_with_script(
                        "scripts/experiments/o2o_proxy_benchmark.py",
                        run_id=run_id,
                        variant=variant,
                        seed=seed,
                        scenario=scenario,
                        extra_args="--offline-steps 120 --online-steps 60",
                    )
                )
    return {"suite_name": "ws5-o2o-proxy", "runs": runs}


def build_metaworld_recent_baseline_config() -> Dict:
    return {
        "suite_name": "ws3-metaworld-recent-baselines",
        "tasks": [
            "reach-v3",
            "push-v3",
            "button-press-v3",
            "button-press-topdown-v3",
            "faucet-open-v3",
            "hammer-v3",
            "pick-place-v3",
            "soccer-v3",
            "peg-insert-side-v3",
            "push-wall-v3",
        ],
        "variants": [
            "baseline",
            "ext1",
            "ext2",
            "latency_aware",
            "adaptmanip",
            "robust_cp",
            "history_keyframe",
            "constrained_flow",
            "method",
        ],
        "scenarios": ["nominal", "shifted"],
        "seeds": [1, 2, 3, 4, 5],
        "max_steps": 80,
        "physics_randomization": METAWORLD_PHYSICS_RANDOMIZATION,
        "shift_scale": {"nominal": 0.0, "shifted": 1.0},
    }


def build_metaworld_seedexp_config(seed_end: int = 14, comparator: str = "ext2") -> Dict:
    return {
        "suite_name": f"ws3-metaworld-seedexp-{comparator}-method",
        "tasks": [
            "reach-v3",
            "push-v3",
            "button-press-v3",
            "button-press-topdown-v3",
            "faucet-open-v3",
            "hammer-v3",
            "pick-place-v3",
            "soccer-v3",
            "peg-insert-side-v3",
            "push-wall-v3",
        ],
        "variants": [comparator, "method"],
        "scenarios": ["shifted"],
        "seeds": list(range(1, seed_end + 1)),
        "max_steps": 80,
        "physics_randomization": METAWORLD_PHYSICS_RANDOMIZATION,
        "shift_scale": {"shifted": 1.0},
    }


def build_maniskill_proxy_config(seed_end: int = 8) -> Dict:
    return {
        "suite_name": "ws3-maniskill-proxy-recent-baselines",
        "tasks": [
            "pick_cube",
            "stack_cube",
            "peg_insert",
            "drawer_open",
            "button_press",
            "door_unlock",
            "cable_route",
            "bimanual_handover",
        ],
        "variants": [
            "baseline",
            "ext1",
            "ext2",
            "latency_aware",
            "adaptmanip",
            "robust_cp",
            "method",
        ],
        "scenarios": ["nominal", "shifted"],
        "seeds": list(range(1, seed_end + 1)),
        "max_steps": 90,
    }


def build_cross_embodiment_proxy_config(seed_end: int = 8) -> Dict:
    return {
        "suite_name": "ws3-cross-embodiment-proxy-recent-baselines",
        "tasks": [
            "pick_cube",
            "stack_cube",
            "peg_insert",
            "drawer_open",
            "door_unlock",
            "button_press",
        ],
        "variants": [
            "baseline",
            "ext1",
            "ext2",
            "latency_aware",
            "adaptmanip",
            "robust_cp",
            "method",
        ],
        "scenarios": ["nominal", "shifted"],
        "seeds": list(range(1, seed_end + 1)),
        "source_embodiment": "franka",
        "target_embodiments": ["franka", "ur5", "xarm", "kinova"],
    }


def write_json(path: pathlib.Path, payload: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(SMOKE_CONFIG, build_smoke_config())
    write_json(OUT_DIR / "experiments_external_baselines.json", build_external_config(seed_end=5))
    write_json(
        OUT_DIR / "experiments_external_baselines_n14.json",
        build_external_config(seed_end=14, suite_name="ws3-external-baselines-n14"),
    )
    write_json(OUT_DIR / "experiments_ablation.json", build_ablation_config())
    write_json(OUT_DIR / "experiments_robustness.json", build_robustness_config())
    write_json(OUT_DIR / "experiments_software_transfer.json", build_software_transfer_config())
    write_json(OUT_DIR / "experiments_sim2sim.json", build_sim2sim_config())
    write_json(OUT_DIR / "experiments_recent_paper_baselines.json", build_recent_baseline_config())
    write_json(OUT_DIR / "experiments_training_backed_recent.json", build_training_backed_recent_config())
    write_json(OUT_DIR / "experiments_library_lane.json", build_library_lane_config())
    write_json(OUT_DIR / "experiments_o2o_proxy_recent.json", build_o2o_proxy_config())
    write_json(OUT_DIR / "experiments_metaworld_recent_baselines.json", build_metaworld_recent_baseline_config())
    write_json(
        OUT_DIR / "experiments_metaworld_seedexp_ext2_method.json",
        build_metaworld_seedexp_config(seed_end=14, comparator="ext2"),
    )
    write_json(
        OUT_DIR / "experiments_metaworld_seedexp_latency_method.json",
        build_metaworld_seedexp_config(seed_end=14, comparator="latency_aware"),
    )
    write_json(
        OUT_DIR / "experiments_metaworld_seedexp_latency_method_n30.json",
        build_metaworld_seedexp_config(seed_end=30, comparator="latency_aware"),
    )
    write_json(
        OUT_DIR / "experiments_metaworld_seedexp_adaptmanip_method.json",
        build_metaworld_seedexp_config(seed_end=14, comparator="adaptmanip"),
    )
    write_json(
        OUT_DIR / "experiments_metaworld_seedexp_adaptmanip_method_n30.json",
        build_metaworld_seedexp_config(seed_end=30, comparator="adaptmanip"),
    )
    write_json(OUT_DIR / "experiments_maniskill_proxy_recent.json", build_maniskill_proxy_config())
    write_json(
        OUT_DIR / "experiments_cross_embodiment_proxy_recent.json",
        build_cross_embodiment_proxy_config(),
    )
    print(f"Wrote smoke config: {SMOKE_CONFIG}")
    print(f"Wrote benchmark configs to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
