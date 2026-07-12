#!/usr/bin/env python3
"""Audit parity against official library codebases for library-lane comparators.

Workflow:
1) shallow-clone upstream repositories into a temporary workspace,
2) verify objective-family source symbols used as parity anchors,
3) compare against local comparator mapping,
4) emit JSON/Markdown reports, then delete temporary clones.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class RepoSpec:
    name: str
    url: str
    source_file: str
    objective_family: str
    required_symbols: tuple[str, ...]
    local_variant: str


REPO_SPECS: tuple[RepoSpec, ...] = (
    RepoSpec(
        name="stable-baselines3",
        url="https://github.com/DLR-RM/stable-baselines3.git",
        source_file="stable_baselines3/ppo/ppo.py",
        objective_family="PPO clipped surrogate objective",
        required_symbols=("class PPO", "clip_range", "target_kl"),
        local_variant="sb3_ppo",
    ),
    RepoSpec(
        name="ray-rllib",
        url="https://github.com/ray-project/ray.git",
        source_file="rllib/algorithms/sac/sac.py",
        objective_family="SAC entropy-regularized actor-critic objective",
        required_symbols=("class SACConfig", "actor_lr", "critic_lr", "alpha_lr"),
        local_variant="rllib_sac",
    ),
)


def _run(cmd: list[str], *, cwd: Path | None = None) -> str:
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return (proc.stdout or "").strip()


def _line_hits(text: str, symbols: tuple[str, ...]) -> list[dict[str, Any]]:
    lines = text.splitlines()
    hits: list[dict[str, Any]] = []
    for symbol in symbols:
        found = False
        for idx, line in enumerate(lines, start=1):
            if symbol in line:
                hits.append({"symbol": symbol, "line": idx, "excerpt": line.strip()[:180], "found": True})
                found = True
                break
        if not found:
            hits.append({"symbol": symbol, "line": None, "excerpt": "", "found": False})
    return hits


def _load_local_variant_mapping() -> dict[str, Any]:
    benchmark_path = ROOT / "scripts/experiments/library_lane_benchmark.py"
    text = benchmark_path.read_text(encoding="utf-8")
    mapping: dict[str, Any] = {
        "source_path": str(benchmark_path.relative_to(ROOT)),
        "declared_variants": [],
    }
    for name in ("method", "sb3_ppo", "rllib_sac"):
        mapping["declared_variants"].append({"variant": name, "present": f'"{name}"' in text})
    return mapping


def _probe_runtime_backends() -> dict[str, Any]:
    script = ROOT / "scripts/experiments/library_lane_benchmark.py"
    code = (
        "import importlib.util, json, pathlib, sys\n"
        f"spec=importlib.util.spec_from_file_location('llb', r'{script}')\n"
        "m=importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(m)\n"
        "print(json.dumps({'sb3': m.resolve_backend('auto','sb3_ppo'),"
        "'rllib': m.resolve_backend('auto','rllib_sac')}))\n"
    )
    out = _run(["python3", "-c", code], cwd=ROOT)
    return json.loads(out)


def _audit_one_repo(temp_root: Path, spec: RepoSpec) -> dict[str, Any]:
    clone_dir = temp_root / spec.name
    _run(
        [
            "git",
            "clone",
            "--depth",
            "1",
            "--filter=blob:none",
            spec.url,
            str(clone_dir),
        ]
    )
    head = _run(["git", "-C", str(clone_dir), "rev-parse", "HEAD"])
    source_path = clone_dir / spec.source_file
    if not source_path.exists():
        raise FileNotFoundError(f"Missing expected file in clone: {source_path}")
    text = source_path.read_text(encoding="utf-8", errors="replace")
    hits = _line_hits(text, spec.required_symbols)
    missing = [row["symbol"] for row in hits if not row["found"]]
    status = "pass" if not missing else "fail"
    return {
        "name": spec.name,
        "url": spec.url,
        "head_commit": head,
        "source_file": spec.source_file,
        "objective_family": spec.objective_family,
        "local_variant": spec.local_variant,
        "required_symbols": list(spec.required_symbols),
        "symbol_hits": hits,
        "status": status,
        "missing_symbols": missing,
    }


def _write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = [
        "# Official Library Parity Audit",
        "",
        f"- Generated (UTC): `{payload.get('generated_at_utc')}`",
        "- Policy: clone -> compare -> cleanup (temporary clones removed).",
        f"- Overall status: `{payload.get('parity_summary', {}).get('overall_status', 'unknown')}`",
        "",
        "## Repo Checks",
        "",
    ]
    for row in payload.get("repos", []):
        lines.append(
            f"- `{row.get('name')}` ({row.get('head_commit', '')[:12]}): "
            f"status=`{row.get('status')}` objective=`{row.get('objective_family')}`"
        )
        lines.append(f"  - Source: `{row.get('url')}` :: `{row.get('source_file')}`")
        missing = row.get("missing_symbols") or []
        if missing:
            lines.append(f"  - Missing symbols: {', '.join(str(x) for x in missing)}")
        else:
            lines.append("  - Required symbols all found.")
    lines.extend(["", "## Local Mapping", ""])
    local = payload.get("local_mapping", {})
    lines.append(f"- Source file: `{local.get('source_path', 'N/A')}`")
    declared = local.get("declared_variants", [])
    for row in declared:
        lines.append(f"- Variant `{row.get('variant')}` present: `{row.get('present')}`")
    lines.extend(["", "## Runtime Probe", ""])
    runtime = payload.get("runtime_probe", {})
    lines.append(f"- SB3 backend: `{runtime.get('sb3', {}).get('mode', 'unknown')}`")
    lines.append(f"- RLlib backend: `{runtime.get('rllib', {}).get('mode', 'unknown')}`")
    lines.append("")
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("output/corepaper_reports/ws5/library_parity_official.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("output/corepaper_reports/ws5/library_parity_official.md"),
    )
    parser.add_argument(
        "--allow-stale-fallback",
        action="store_true",
        help="On network failures, keep previous output if it exists.",
    )
    return parser.parse_args()


def _run_audit() -> dict[str, Any]:
    local_mapping = _load_local_variant_mapping()
    runtime_probe = _probe_runtime_backends()

    with tempfile.TemporaryDirectory(prefix="corepaper-parity-") as tmp:
        temp_root = Path(tmp)
        repo_rows = [_audit_one_repo(temp_root, spec) for spec in REPO_SPECS]

    missing: list[str] = []
    for row in repo_rows:
        if row.get("status") != "pass":
            missing.extend([f"{row.get('name')}::{sym}" for sym in row.get("missing_symbols", [])])

    declared = {
        str(row.get("variant")): bool(row.get("present"))
        for row in local_mapping.get("declared_variants", [])
        if isinstance(row, dict)
    }
    for spec in REPO_SPECS:
        if not declared.get(spec.local_variant, False):
            missing.append(f"local-variant-missing::{spec.local_variant}")

    overall_status = "pass" if not missing else "fail"
    return {
        "generated_at_utc": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "policy": "temporary_clone_compare_cleanup",
        "repos": repo_rows,
        "local_mapping": local_mapping,
        "runtime_probe": runtime_probe,
        "parity_summary": {
            "overall_status": overall_status,
            "checked_variants": [spec.local_variant for spec in REPO_SPECS],
            "missing_or_mismatch": missing,
            "temporary_clone_cleanup": "done",
        },
    }


def main() -> int:
    args = parse_args()
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)

    try:
        payload = _run_audit()
    except Exception as exc:  # noqa: BLE001
        if args.allow_stale_fallback and args.output_json.exists():
            fallback = json.loads(args.output_json.read_text(encoding="utf-8"))
            fallback["stale_fallback_reason"] = str(exc)
            _write_markdown(args.output_md, fallback)
            print(
                f"[parity] WARNING live audit failed; reused stale artifact: {args.output_json}",
            )
            return 0
        raise SystemExit(f"official parity audit failed: {exc}")

    args.output_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _write_markdown(args.output_md, payload)
    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
