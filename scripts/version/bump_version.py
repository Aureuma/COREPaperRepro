#!/usr/bin/env python3
"""Bump repository version and keep canonical version fields synchronized."""

from __future__ import annotations

import argparse
import pathlib
import re
import tomllib
from dataclasses import dataclass


ROOT = pathlib.Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class SemVer:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, value: str) -> "SemVer":
        m = re.fullmatch(r"\s*(\d+)\.(\d+)\.(\d+)\s*", value)
        if not m:
            raise ValueError(f"Invalid semantic version: {value!r}")
        return cls(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    def bump(self, part: str) -> "SemVer":
        if part == "major":
            return SemVer(self.major + 1, 0, 0)
        if part == "minor":
            return SemVer(self.major, self.minor + 1, 0)
        if part == "patch":
            return SemVer(self.major, self.minor, self.patch + 1)
        raise ValueError(f"Unknown bump part: {part}")

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


def ensure_pyproject_uses_version_file(root: pathlib.Path) -> None:
    pyproject_path = root / "pyproject.toml"
    payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
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


def read_version(root: pathlib.Path) -> SemVer:
    version_path = root / "VERSION"

    version_text = version_path.read_text(encoding="utf-8").strip()
    return SemVer.parse(version_text)


def write_versions(root: pathlib.Path, new_version: SemVer) -> None:
    version_path = root / "VERSION"

    version_path.write_text(f"{new_version}\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--part",
        choices=("major", "minor", "patch"),
        default="patch",
        help="Semantic-version part to bump.",
    )
    parser.add_argument(
        "--set-version",
        default="",
        help="Set an explicit version instead of incrementing one part.",
    )
    parser.add_argument(
        "--root",
        default=str(ROOT),
        help="Repository root (for testing or advanced workflows).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = pathlib.Path(args.root).resolve()
    ensure_pyproject_uses_version_file(root)
    version_file = read_version(root)

    if args.set_version:
        new_version = SemVer.parse(args.set_version)
    else:
        new_version = version_file.bump(args.part)

    write_versions(root, new_version)
    print(f"Bumped version: {version_file} -> {new_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
