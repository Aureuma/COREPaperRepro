#!/usr/bin/env python3
"""Toy training-backed comparator benchmark for method-fidelity stress checks.

This benchmark replaces fixed profile scoring with a lightweight train/eval loop
that applies variant-specific optimization rules under scenario stress.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import deque
from typing import Dict


VARIANT_CFG: Dict[str, Dict[str, float | bool]] = {
    "baseline": {"lr": 0.050, "grad_clip": 0.0, "delay": 0, "adapt": 0.0, "robust_margin": 0.0, "risk_gain": 0.0, "gate": False},
    "ext2": {"lr": 0.048, "grad_clip": 0.22, "delay": 0, "adapt": 0.0, "robust_margin": 0.0, "risk_gain": 0.0, "gate": False},
    "latency_aware": {"lr": 0.046, "grad_clip": 0.20, "delay": 2, "adapt": 0.0, "robust_margin": 0.0, "risk_gain": 0.0, "gate": False},
    "adaptmanip": {"lr": 0.046, "grad_clip": 0.20, "delay": 1, "adapt": 0.35, "robust_margin": 0.0, "risk_gain": 0.0, "gate": False},
    "robust_cp": {"lr": 0.044, "grad_clip": 0.20, "delay": 1, "adapt": 0.0, "robust_margin": 0.045, "risk_gain": 0.0, "gate": False},
    "method": {"lr": 0.051, "grad_clip": 0.18, "delay": 1, "adapt": 0.25, "robust_margin": 0.02, "risk_gain": 0.28, "gate": True},
}

SCENARIO_STRESS: Dict[str, Dict[str, float]] = {
    "nominal": {"contact": 0.0, "latency": 0.0, "dropout": 0.0, "engine": 0.0},
    "R4-hard": {"contact": 1.2, "latency": 0.45, "dropout": 0.35, "engine": 0.0},
    "S1-hard": {"contact": 0.88, "latency": 0.98, "dropout": 0.0, "engine": 0.0},
    "S2-high": {"contact": 0.0, "latency": 1.40, "dropout": 0.0, "engine": 0.0},
    "S3-severe": {"contact": 0.0, "latency": 0.0, "dropout": 1.20, "engine": 0.0},
    "SIM-isaac": {"contact": 0.25, "latency": 0.35, "dropout": 0.30, "engine": 0.75},
}

PENALTY = {"contact": 0.10, "latency": 0.08, "dropout": 0.07, "engine": 0.05}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--variant", required=True, choices=tuple(sorted(VARIANT_CFG)))
    parser.add_argument("--scenario", required=True, choices=tuple(sorted(SCENARIO_STRESS)))
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--train-steps", type=int, default=80)
    parser.add_argument("--eval-episodes", type=int, default=50)
    return parser.parse_args()


def clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


def tanh(v: float) -> float:
    return math.tanh(v)


def run_train_eval(variant: str, scenario: str, seed: int, run_id: str, train_steps: int, eval_episodes: int) -> Dict[str, float]:
    cfg = VARIANT_CFG[variant]
    stress = SCENARIO_STRESS[scenario]
    stress_total = stress["contact"] + stress["latency"] + stress["dropout"] + stress["engine"]
    stress_norm = min(1.0, stress_total / 2.5)

    rng = random.Random(f"tb:{variant}:{scenario}:{seed}:{run_id}:v1")
    w = [rng.uniform(-0.5, 0.5) for _ in range(3)]
    target_vec = [0.55 - 0.12 * stress["contact"], -0.35 + 0.08 * stress["latency"], 0.20 - 0.10 * stress["dropout"]]
    desired_action = 0.65 - 0.06 * stress_total

    delay = int(cfg["delay"])
    obs_queue: deque[list[float]] = deque([[0.0, 0.0, 0.0] for _ in range(delay + 1)], maxlen=delay + 1)
    prev_err2 = 0.20
    promoted_steps = 0
    rollback_steps = 0
    loss_trace: list[float] = []

    for step in range(train_steps):
        obs = [
            target_vec[0] + rng.gauss(0.0, 0.05 + 0.02 * stress["engine"]),
            target_vec[1] + rng.gauss(0.0, 0.05 + 0.02 * stress["latency"]),
            target_vec[2] + rng.gauss(0.0, 0.05 + 0.02 * stress["dropout"]),
        ]
        if rng.random() < 0.06 * stress["dropout"]:
            obs = list(obs_queue[-1])

        obs_queue.append(obs)
        used_obs = list(obs_queue[0])
        act = tanh(sum(wi * oi for wi, oi in zip(w, used_obs)))

        robust_margin = float(cfg["robust_margin"]) * stress_norm
        err = (act - desired_action) + math.copysign(robust_margin, act - desired_action if act != desired_action else 1.0)
        err2 = err * err

        lr = float(cfg["lr"])
        adapt = float(cfg["adapt"])
        if adapt > 0.0:
            lr *= (1.0 + adapt * min(1.5, math.sqrt(err2)))
        risk_lambda = 1.0 + (float(cfg["risk_gain"]) * stress_norm)

        grad = [risk_lambda * err * oi for oi in used_obs]
        clip = float(cfg["grad_clip"])
        if clip > 0.0:
            grad = [max(-clip, min(clip, g)) for g in grad]

        cand_w = [wi - lr * gi for wi, gi in zip(w, grad)]
        if bool(cfg["gate"]):
            predicted_gain = (prev_err2 - err2) - 0.15 * abs(err)
            if predicted_gain < -0.0015:
                rollback_steps += 1
            else:
                w = cand_w
                promoted_steps += 1
                prev_err2 = err2
        else:
            w = cand_w
            promoted_steps += 1
            prev_err2 = err2

        loss_trace.append(err2)

    eval_scores: list[float] = []
    for _ in range(eval_episodes):
        obs = [
            target_vec[0] + rng.gauss(0.0, 0.05 + 0.02 * stress["engine"]),
            target_vec[1] + rng.gauss(0.0, 0.05 + 0.02 * stress["latency"]),
            target_vec[2] + rng.gauss(0.0, 0.05 + 0.02 * stress["dropout"]),
        ]
        act = tanh(sum(wi * oi for wi, oi in zip(w, obs)))
        err = abs(act - desired_action)
        disturbance_penalty = (
            PENALTY["contact"] * stress["contact"]
            + PENALTY["latency"] * stress["latency"]
            + PENALTY["dropout"] * stress["dropout"]
            + PENALTY["engine"] * stress["engine"]
        )
        score = clamp01(0.86 - 0.55 * err - 0.10 * disturbance_penalty + rng.gauss(0.0, 0.008))
        eval_scores.append(score)

    return {
        "score": sum(eval_scores) / len(eval_scores),
        "train_loss_mean": sum(loss_trace) / len(loss_trace) if loss_trace else 0.0,
        "train_loss_last": loss_trace[-1] if loss_trace else 0.0,
        "stress_norm": stress_norm,
        "risk_lambda": 1.0 + (float(cfg["risk_gain"]) * stress_norm),
        "promoted_steps": float(promoted_steps),
        "rollback_steps": float(rollback_steps),
    }


def main() -> int:
    args = parse_args()
    payload = run_train_eval(
        variant=args.variant,
        scenario=args.scenario,
        seed=args.seed,
        run_id=args.run_id,
        train_steps=args.train_steps,
        eval_episodes=args.eval_episodes,
    )
    print(
        json.dumps(
            {
                "run_id": args.run_id,
                "seed": args.seed,
                "variant": args.variant,
                "resolved_variant": args.variant,
                "scenario": args.scenario,
                "implementation": "training_backed_toy_optimizer_v1",
                "primary_metric": round(payload["score"], 4),
                "score_components": {
                    "train_loss_mean": round(payload["train_loss_mean"], 6),
                    "train_loss_last": round(payload["train_loss_last"], 6),
                    "stress_norm": round(payload["stress_norm"], 6),
                    "risk_lambda": round(payload["risk_lambda"], 6),
                    "promoted_steps": int(payload["promoted_steps"]),
                    "rollback_steps": int(payload["rollback_steps"]),
                },
                "status": "ok",
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

