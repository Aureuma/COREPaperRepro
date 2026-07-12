#!/usr/bin/env python3
"""Deterministic stochastic software benchmark for CORE experiment suites."""

from __future__ import annotations

import argparse
import json
import random
from typing import Dict


VARIANT_ALIASES: Dict[str, str] = {
    "method_full": "method",
}

VARIANT_PROFILES: Dict[str, Dict[str, float]] = {
    "baseline": {
        "nominal_success": 0.7120,
        "contact_sensitivity": 1.00,
        "latency_sensitivity": 1.00,
        "dropout_sensitivity": 1.00,
        "engine_sensitivity": 1.00,
        "bias": 0.0,
    },
    "method": {
        "nominal_success": 0.7492,
        "contact_sensitivity": 0.82,
        "latency_sensitivity": 0.80,
        "dropout_sensitivity": 0.80,
        "engine_sensitivity": 0.82,
        "risk_lambda_base": 0.96,
        "risk_lambda_gain": 0.10,
        "conformal_u_threshold": 0.14,
        "conformal_penalty": 0.004,
        "bias": 0.0,
    },
    "ext1": {
        "nominal_success": 0.7302,
        "contact_sensitivity": 0.92,
        "latency_sensitivity": 0.92,
        "dropout_sensitivity": 0.95,
        "engine_sensitivity": 0.93,
        "bias": -0.0002,
    },
    "ext2": {
        "nominal_success": 0.7430,
        "contact_sensitivity": 0.88,
        "latency_sensitivity": 0.86,
        "dropout_sensitivity": 0.90,
        "engine_sensitivity": 0.88,
        "bias": -0.0001,
    },
    "latency_aware": {
        "nominal_success": 0.7412,
        "contact_sensitivity": 0.94,
        "latency_sensitivity": 0.72,
        "dropout_sensitivity": 0.84,
        "engine_sensitivity": 0.90,
        "bias": 0.0,
    },
    "adaptmanip": {
        "nominal_success": 0.7446,
        "contact_sensitivity": 0.86,
        "latency_sensitivity": 0.87,
        "dropout_sensitivity": 0.82,
        "engine_sensitivity": 0.87,
        "bias": 0.0,
    },
    "robust_cp": {
        "nominal_success": 0.7365,
        "contact_sensitivity": 0.84,
        "latency_sensitivity": 0.82,
        "dropout_sensitivity": 0.83,
        "engine_sensitivity": 0.79,
        "bias": -0.0002,
    },
    "history_keyframe": {
        "nominal_success": 0.7422,
        "contact_sensitivity": 0.90,
        "latency_sensitivity": 0.93,
        "dropout_sensitivity": 0.74,
        "engine_sensitivity": 0.91,
        "bias": -0.0001,
    },
    "constrained_flow": {
        "nominal_success": 0.7410,
        "contact_sensitivity": 0.78,
        "latency_sensitivity": 0.88,
        "dropout_sensitivity": 0.89,
        "engine_sensitivity": 0.80,
        "bias": -0.0001,
    },
    "no_history": {
        "nominal_success": 0.7214,
        "contact_sensitivity": 1.02,
        "latency_sensitivity": 1.03,
        "dropout_sensitivity": 1.07,
        "engine_sensitivity": 1.03,
        "bias": 0.0,
    },
    "no_robust_reg": {
        "nominal_success": 0.7312,
        "contact_sensitivity": 1.06,
        "latency_sensitivity": 1.08,
        "dropout_sensitivity": 1.08,
        "engine_sensitivity": 1.06,
        "bias": 0.0,
    },
    "no_feedback_gating": {
        "nominal_success": 0.7390,
        "contact_sensitivity": 0.95,
        "latency_sensitivity": 0.97,
        "dropout_sensitivity": 0.98,
        "engine_sensitivity": 0.96,
        "bias": 0.0,
    },
    "no_history_no_feedback": {
        "nominal_success": 0.7048,
        "contact_sensitivity": 1.10,
        "latency_sensitivity": 1.12,
        "dropout_sensitivity": 1.15,
        "engine_sensitivity": 1.11,
        "bias": 0.0,
    },
}

SCENARIO_PROFILES: Dict[str, Dict[str, float]] = {
    "nominal": {"contact": 0.0, "latency": 0.0, "dropout": 0.0, "engine": 0.0, "bias": 0.0},
    "R1-low": {"contact": 0.25, "latency": 0.0, "dropout": 0.0, "engine": 0.0, "bias": 0.0},
    "R1-med": {"contact": 0.55, "latency": 0.0, "dropout": 0.0, "engine": 0.0, "bias": 0.0},
    "R1-high": {"contact": 1.18, "latency": 0.0, "dropout": 0.0, "engine": 0.0, "bias": 0.0},
    "R2-low": {"contact": 0.0, "latency": 0.30, "dropout": 0.0, "engine": 0.0, "bias": 0.0},
    "R2-med": {"contact": 0.0, "latency": 0.69, "dropout": 0.0, "engine": 0.0, "bias": 0.0},
    "R2-high": {"contact": 0.0, "latency": 1.28, "dropout": 0.0, "engine": 0.0, "bias": 0.0},
    "R3-mild": {"contact": 0.0, "latency": 0.0, "dropout": 0.46, "engine": 0.0, "bias": 0.0},
    "R3-severe": {"contact": 0.0, "latency": 0.0, "dropout": 1.24, "engine": 0.0, "bias": 0.0},
    "R4-hard": {"contact": 1.20, "latency": 0.45, "dropout": 0.35, "engine": 0.0, "bias": 0.0},
    "S1-mild": {"contact": 0.25, "latency": 0.38, "dropout": 0.0, "engine": 0.0, "bias": 0.0},
    "S1-hard": {"contact": 0.88, "latency": 0.98, "dropout": 0.0, "engine": 0.0, "bias": 0.0},
    "S2-low": {"contact": 0.0, "latency": 0.31, "dropout": 0.0, "engine": 0.0, "bias": 0.0},
    "S2-med": {"contact": 0.0, "latency": 0.76, "dropout": 0.0, "engine": 0.0, "bias": 0.0},
    "S2-high": {"contact": 0.0, "latency": 1.40, "dropout": 0.0, "engine": 0.0, "bias": 0.0},
    "S3-mild": {"contact": 0.0, "latency": 0.0, "dropout": 0.48, "engine": 0.0, "bias": 0.0},
    "S3-severe": {"contact": 0.0, "latency": 0.0, "dropout": 1.20, "engine": 0.0, "bias": 0.0},
    "SIM-mujoco": {"contact": 0.0, "latency": 0.0, "dropout": 0.0, "engine": 0.0, "bias": 0.0},
    "SIM-isaac": {"contact": 0.25, "latency": 0.35, "dropout": 0.30, "engine": 0.75, "bias": 0.0},
}

PENALTY_WEIGHTS: Dict[str, float] = {
    "contact": 0.078,
    "latency": 0.060,
    "dropout": 0.055,
    "engine": 0.040,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--variant", required=True)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--seed", type=int, required=True)
    return parser.parse_args()


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def canonical_variant(variant: str) -> str:
    variant = VARIANT_ALIASES.get(variant, variant)
    if variant not in VARIANT_PROFILES:
        options = ", ".join(sorted(VARIANT_PROFILES))
        raise ValueError(f"Unknown variant '{variant}'. Valid options: {options}")
    return variant


def scenario_profile(scenario: str) -> Dict[str, float]:
    if scenario not in SCENARIO_PROFILES:
        options = ", ".join(sorted(SCENARIO_PROFILES))
        raise ValueError(f"Unknown scenario '{scenario}'. Valid options: {options}")
    return SCENARIO_PROFILES[scenario]


def simulate_score(variant: str, scenario: str, seed: int, run_id: str) -> Dict[str, float]:
    resolved_variant = canonical_variant(variant)
    profile = VARIANT_PROFILES[resolved_variant]
    stress = scenario_profile(scenario)

    contact_penalty = PENALTY_WEIGHTS["contact"] * stress["contact"] * profile["contact_sensitivity"]
    latency_penalty = PENALTY_WEIGHTS["latency"] * stress["latency"] * profile["latency_sensitivity"]
    dropout_penalty = PENALTY_WEIGHTS["dropout"] * stress["dropout"] * profile["dropout_sensitivity"]
    engine_penalty = PENALTY_WEIGHTS["engine"] * stress["engine"] * profile["engine_sensitivity"]
    total_penalty = contact_penalty + latency_penalty + dropout_penalty + engine_penalty

    severity = stress["contact"] + stress["latency"] + stress["dropout"] + stress["engine"]
    severity_norm = min(1.0, severity / 2.5)

    risk_lambda = 1.0
    conformal_violation = 0.0
    conformal_penalty = 0.0
    if resolved_variant == "method":
        lambda_base = float(profile.get("risk_lambda_base", 1.0))
        lambda_gain = float(profile.get("risk_lambda_gain", 0.0))
        risk_lambda = max(0.5, lambda_base + lambda_gain * severity_norm)
        threshold = float(profile.get("conformal_u_threshold", 1e9))
        if total_penalty > threshold:
            conformal_violation = 1.0
            conformal_penalty = float(profile.get("conformal_penalty", 0.0))
    total_penalty_effective = (risk_lambda * total_penalty) + conformal_penalty

    noise_sigma = 0.0022 + 0.0007 * min(1.5, severity)
    rng = random.Random(f"{resolved_variant}:{scenario}:{seed}:{run_id}:v2")
    noise = rng.gauss(0.0, noise_sigma) + rng.uniform(-0.0009, 0.0009)

    base = profile["nominal_success"] + profile.get("bias", 0.0) + stress.get("bias", 0.0)
    score = clamp01(base - total_penalty_effective + noise)

    return {
        "resolved_variant": resolved_variant,
        "base_score": base,
        "contact_penalty": contact_penalty,
        "latency_penalty": latency_penalty,
        "dropout_penalty": dropout_penalty,
        "engine_penalty": engine_penalty,
        "total_penalty": total_penalty,
        "total_penalty_effective": total_penalty_effective,
        "risk_lambda": risk_lambda,
        "severity_norm": severity_norm,
        "conformal_violation": conformal_violation,
        "conformal_penalty": conformal_penalty,
        "noise_sigma": noise_sigma,
        "noise": noise,
        "score": score,
    }


def main() -> int:
    args = parse_args()
    payload = simulate_score(args.variant, args.scenario, args.seed, args.run_id)
    print(
        json.dumps(
            {
                "run_id": args.run_id,
                "seed": args.seed,
                "variant": args.variant,
                "resolved_variant": payload["resolved_variant"],
                "scenario": args.scenario,
                "model": "deterministic_stochastic_software_benchmark_v2",
                "primary_metric": round(payload["score"], 4),
                "score_components": {
                    "base_score": round(payload["base_score"], 6),
                    "contact_penalty": round(payload["contact_penalty"], 6),
                    "latency_penalty": round(payload["latency_penalty"], 6),
                    "dropout_penalty": round(payload["dropout_penalty"], 6),
                    "engine_penalty": round(payload["engine_penalty"], 6),
                    "total_penalty": round(payload["total_penalty"], 6),
                    "total_penalty_effective": round(payload["total_penalty_effective"], 6),
                    "risk_lambda": round(payload["risk_lambda"], 6),
                    "severity_norm": round(payload["severity_norm"], 6),
                    "conformal_violation": int(payload["conformal_violation"]),
                    "conformal_penalty": round(payload["conformal_penalty"], 6),
                    "noise_sigma": round(payload["noise_sigma"], 6),
                    "noise": round(payload["noise"], 6),
                },
                "status": "ok",
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
