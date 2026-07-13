from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class DevelopmentContractTests(unittest.TestCase):
    def test_package_exposes_reproducible_check_commands(self) -> None:
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        scripts = package["scripts"]

        for name in ("check:quick", "check:full", "check:types", "check:api", "test:smoke"):
            self.assertIn(name, scripts)

    def test_check_script_and_dev_requirements_exist(self) -> None:
        self.assertTrue((ROOT / "scripts" / "check.ps1").is_file())
        self.assertTrue((ROOT / "requirements-dev.txt").is_file())

    def test_readme_documents_single_install_start_and_check_path(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("npm ci", readme)
        self.assertIn("scripts\\check.ps1", readme)
        self.assertIn("npm run dev:api", readme)
        self.assertIn("npm run dev", readme)
        self.assertIn("IFIND_REFRESH_TOKEN", readme)


if __name__ == "__main__":
    unittest.main()
