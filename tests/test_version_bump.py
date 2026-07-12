from __future__ import annotations

import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts/version/bump_version.py"


class VersionBumpScriptTests(unittest.TestCase):
    def _write_repo_files(self, root: Path, version: str) -> None:
        (root / "VERSION").write_text(f"{version}\n", encoding="utf-8")
        (root / "pyproject.toml").write_text(
            textwrap.dedent(
                f"""
                [project]
                name = "corepaper"
                dynamic = ["version"]

                [tool.setuptools.dynamic]
                version = {{file = ["VERSION"]}}
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )

    def test_patch_bump_updates_version_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_repo_files(root, "1.2.3")
            subprocess.run(
                ["python3", str(SCRIPT), "--root", str(root), "--part", "patch"],
                check=True,
            )
            self.assertEqual((root / "VERSION").read_text(encoding="utf-8").strip(), "1.2.4")
            pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
            self.assertIn('version = {file = ["VERSION"]}', pyproject)

    def test_set_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_repo_files(root, "2.0.0")
            subprocess.run(
                ["python3", str(SCRIPT), "--root", str(root), "--set-version", "2.5.9"],
                check=True,
            )
            self.assertEqual((root / "VERSION").read_text(encoding="utf-8").strip(), "2.5.9")


if __name__ == "__main__":
    unittest.main()
