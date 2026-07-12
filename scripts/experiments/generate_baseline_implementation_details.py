#!/usr/bin/env python3
"""Generate baseline implementation-detail artifacts for transparency in manuscript claims."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pathlib
from typing import Dict, List

from software_benchmark import PENALTY_WEIGHTS, VARIANT_PROFILES

ROOT = pathlib.Path(__file__).resolve().parents[2]


BASELINE_METHOD_MAPPING = {
    "baseline": {
        "label": "Internal baseline profile",
        "canonical_family": "Risk-neutral policy optimization reference",
        "paper_mapping": "Internal baseline used for matched-budget comparison",
    },
    "ext1": {
        "label": "Reference-A",
        "canonical_family": "TRPO-style trust-region objective",
        "paper_mapping": "Trust-region baseline without online rollback gate",
    },
    "ext2": {
        "label": "Reference-B",
        "canonical_family": "PPO-style CVaR-oriented objective",
        "paper_mapping": "Risk-sensitive baseline without online rollback gate",
    },
    "latency_aware": {
        "label": "Latency-aware reference profile",
        "canonical_family": "Latency-sensitive execution profile (no online rollback gate)",
        "paper_mapping": "Closest comparator profile used for floor-first nearest-neighbor checks",
    },
    "method": {
        "label": "CORE",
        "canonical_family": "Uncertainty-gated trust-region update",
        "paper_mapping": "Proposed method with promotion/rollback control",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--calibration-targets", default="config/benchmarks/baseline_calibration_targets.json")
    parser.add_argument("--output-json", default="output/corepaper_reports/ws3/baseline_implementation_details.json")
    parser.add_argument("--output-md", default="output/corepaper_reports/ws3/baseline_implementation_details.md")
    return parser.parse_args()


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def short_profile_hash(payload: Dict[str, float]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:12]


def load_library_lane_module():
    script_path = ROOT / "scripts/experiments/library_lane_benchmark.py"
    spec = importlib.util.spec_from_file_location("library_lane_benchmark", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def format_profile_row(name: str, profile: Dict[str, float]) -> Dict[str, float]:
    return {
        "variant": name,
        "nominal_success": round(float(profile["nominal_success"]), 4),
        "contact_sensitivity": round(float(profile["contact_sensitivity"]), 4),
        "latency_sensitivity": round(float(profile["latency_sensitivity"]), 4),
        "dropout_sensitivity": round(float(profile["dropout_sensitivity"]), 4),
        "engine_sensitivity": round(float(profile["engine_sensitivity"]), 4),
        "bias": round(float(profile.get("bias", 0.0)), 6),
    }


def main() -> int:
    args = parse_args()
    targets = json.loads(pathlib.Path(args.calibration_targets).read_text(encoding="utf-8"))
    library_lane = load_library_lane_module()

    tracked_variants: List[str] = ["baseline", "ext1", "ext2", "latency_aware", "method"]
    profile_rows = [format_profile_row(v, VARIANT_PROFILES[v]) for v in tracked_variants]
    library_variants: List[str] = ["sb3_ppo", "rllib_sac", "method"]

    objective_anchor = {
        "sb3_ppo": "PPO clipped surrogate objective (SB3 parity lane)",
        "rllib_sac": "SAC entropy-regularized actor-critic objective (RLlib parity lane)",
        "method": "CORE uncertainty-gated objective profile",
    }
    library_profiles = []
    for variant in library_variants:
        profile = library_lane.VARIANT_PROFILES[variant]
        profile_payload = {
            "base": round(float(profile["base"]), 4),
            "contact_sensitivity": round(float(profile["contact_sensitivity"]), 4),
            "latency_sensitivity": round(float(profile["latency_sensitivity"]), 4),
            "dropout_sensitivity": round(float(profile["dropout_sensitivity"]), 4),
            "engine_sensitivity": round(float(profile["engine_sensitivity"]), 4),
        }
        library_profiles.append(
            {
                "variant": variant,
                "objective_anchor": objective_anchor[variant],
                "profile": profile_payload,
                "profile_sha256_12": short_profile_hash(profile_payload),
            }
        )

    library_config_paths = [
        ROOT / "scripts/experiments/library_lane_benchmark.py",
        ROOT / "config/benchmarks/experiments_library_lane.json",
        ROOT / "config/benchmarks/recent_baseline_official_sources.json",
    ]
    library_config_hashes = [
        {
            "path": str(path.relative_to(ROOT)),
            "sha256": sha256_file(path),
        }
        for path in library_config_paths
    ]

    official_commits = []
    parity_json_path = ROOT / "output/corepaper_reports/ws5/library_parity_official.json"
    if parity_json_path.exists():
        parity_payload = json.loads(parity_json_path.read_text(encoding="utf-8"))
        for row in parity_payload.get("repos", []):
            if not isinstance(row, dict):
                continue
            official_commits.append(
                {
                    "name": str(row.get("name", "")),
                    "local_variant": str(row.get("local_variant", "")),
                    "head_commit": str(row.get("head_commit", "")),
                    "source_file": str(row.get("source_file", "")),
                }
            )

    payload = {
        "method_mapping": BASELINE_METHOD_MAPPING,
        "profiles": profile_rows,
        "penalty_weights": {k: round(float(v), 4) for k, v in PENALTY_WEIGHTS.items()},
        "calibration_targets": targets,
        "library_lane_hyperparameters": {
            "weights": {k: round(float(v), 4) for k, v in library_lane.WEIGHTS.items()},
            "profiles": library_profiles,
        },
        "library_config_hashes": library_config_hashes,
        "official_parity_commits": official_commits,
        "notes": [
            "Reference-A/B are implementation-backed profiles in a unified deterministic stochastic harness.",
            "latency_aware is the closest-comparator profile in manuscript nearest-neighbor analyses.",
            "Calibration checks compare observed means to predefined targets with absolute tolerance <= 0.005.",
            "Library-lane section reports exact config hashes and parity-lane comparator profile snapshots (SB3 PPO, RLlib SAC).",
            "This artifact documents objective-family mapping, profile parameters, and hash-anchored reproducibility metadata.",
        ],
    }

    out_json = pathlib.Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines: List[str] = []
    lines.append("# Baseline Implementation Details (Auto-generated)")
    lines.append("")
    lines.append("## Objective-Family Mapping")
    lines.append("")
    lines.append("| Variant | Label | Canonical Family | Paper Mapping |")
    lines.append("|---|---|---|---|")
    for variant in tracked_variants:
        row = BASELINE_METHOD_MAPPING[variant]
        lines.append(
            f"| {variant} | {row['label']} | {row['canonical_family']} | {row['paper_mapping']} |"
        )
    lines.append("")
    lines.append("## Scenario-Model Profile Parameters")
    lines.append("")
    lines.append("| Variant | Nominal | Contact Sens. | Latency Sens. | Dropout Sens. | Engine Sens. | Bias |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for row in profile_rows:
        lines.append(
            f"| {row['variant']} | {row['nominal_success']:.4f} | {row['contact_sensitivity']:.2f} | "
            f"{row['latency_sensitivity']:.2f} | {row['dropout_sensitivity']:.2f} | "
            f"{row['engine_sensitivity']:.2f} | {row['bias']:+.4f} |"
        )
    lines.append("")
    lines.append("## Penalty Weights")
    lines.append("")
    lines.append("| Channel | Weight |")
    lines.append("|---|---:|")
    for key in ("contact", "latency", "dropout", "engine"):
        lines.append(f"| {key} | {payload['penalty_weights'][key]:.4f} |")
    lines.append("")
    lines.append("## Calibration Targets")
    lines.append("")
    lines.append("| Group | Target Mean | Tolerance | Source |")
    lines.append("|---|---:|---:|---|")
    for target in targets.get("targets", []):
        lines.append(
            f"| {target.get('group')} | {float(target.get('target_mean', 0.0)):.4f} | "
            f"{float(target.get('tolerance_abs', targets.get('default_tolerance_abs', 0.0))):.4f} | "
            f"{target.get('source', '')} |"
        )
    lines.append("")
    lines.append("## Library-Lane Hyperparameter Snapshot")
    lines.append("")
    lines.append("| Variant | Objective Anchor | Base | Contact | Latency | Dropout | Engine | Profile SHA-256 (12) |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---|")
    for row in payload["library_lane_hyperparameters"]["profiles"]:
        profile = row["profile"]
        lines.append(
            f"| {row['variant']} | {row['objective_anchor']} | {profile['base']:.4f} | "
            f"{profile['contact_sensitivity']:.4f} | {profile['latency_sensitivity']:.4f} | "
            f"{profile['dropout_sensitivity']:.4f} | {profile['engine_sensitivity']:.4f} | "
            f"`{row['profile_sha256_12']}` |"
        )
    lines.append("")
    lines.append("## Library Config Hashes")
    lines.append("")
    lines.append("| Path | SHA-256 |")
    lines.append("|---|---|")
    for row in payload["library_config_hashes"]:
        lines.append(f"| `{row['path']}` | `{row['sha256']}` |")
    if payload["official_parity_commits"]:
        lines.append("")
        lines.append("## Official Parity Commit Anchors")
        lines.append("")
        lines.append("| Upstream | Local Variant | Head Commit | Source File |")
        lines.append("|---|---|---|---|")
        for row in payload["official_parity_commits"]:
            head = row["head_commit"][:12] if row["head_commit"] else ""
            lines.append(
                f"| {row['name']} | {row['local_variant']} | `{head}` | `{row['source_file']}` |"
            )
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    for note in payload["notes"]:
        lines.append(f"- {note}")

    out_md = pathlib.Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
