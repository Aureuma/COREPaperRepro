#!/usr/bin/env python3
"""Validate that all canonical version fields are synchronized."""

from __future__ import annotations

import pathlib
import tomllib


ROOT = pathlib.Path(__file__).resolve().parents[2]


def read_version_file() -> str:
    return (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def read_pyproject_version() -> str:
    payload = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = payload.get("project", {})
    if "version" in project:
        raise SystemExit("pyproject.toml must derive version from VERSION, not [project].version.")

    dynamic = project.get("dynamic", [])
    version_source = (
        payload.get("tool", {})
        .get("setuptools", {})
        .get("dynamic", {})
        .get("version", {})
        .get("file", [])
    )
    if "version" not in dynamic or version_source != ["VERSION"]:
        raise SystemExit("pyproject.toml version source must be tool.setuptools.dynamic.version.file = [\"VERSION\"].")
    return "VERSION"


def main() -> int:
    version_file = read_version_file()
    pyproject_version = read_pyproject_version()

    if not version_file:
        raise SystemExit("VERSION file is empty.")

    print(f"Version sync check passed: {version_file} ({pyproject_version})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
