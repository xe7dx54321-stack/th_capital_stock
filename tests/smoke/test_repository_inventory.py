from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.inventory_repository import (
    Classification,
    build_inventory,
    classify_path,
    write_manifests,
)


class RepositoryInventoryTests(unittest.TestCase):
    def test_classification_never_approves_deletion(self) -> None:
        classification = classify_path(
            "_debug_once.py",
            tracked=False,
            size=20,
            reference_count=0,
            runtime_evidence=None,
        )

        self.assertEqual(Classification.DELETE_CANDIDATE, classification.category)
        self.assertFalse(classification.approved)

    def test_secret_and_generated_paths_have_priority(self) -> None:
        secret = classify_path(
            "config/ifind_refresh_token.txt",
            tracked=False,
            size=0,
            reference_count=0,
            runtime_evidence=None,
        )
        generated = classify_path(
            "01_data/db/smr.db",
            tracked=False,
            size=100,
            reference_count=0,
            runtime_evidence=None,
        )

        self.assertEqual(Classification.SECRET, secret.category)
        self.assertEqual(Classification.GENERATED, generated.category)

    def test_dotfile_name_is_preserved_and_gitignore_is_kept(self) -> None:
        classification = classify_path(
            ".gitignore",
            tracked=True,
            size=100,
            reference_count=0,
            runtime_evidence=None,
        )

        self.assertEqual(Classification.KEEP, classification.category)

    def test_phase_contract_is_frozen_unless_runtime_evidence_exists(self) -> None:
        frozen = classify_path(
            "08_scripts/jobs/run_phase154_multi_agent_loop_pipeline.py",
            tracked=True,
            size=100,
            reference_count=0,
            runtime_evidence=None,
        )
        active = classify_path(
            "08_scripts/jobs/run_phase154_multi_agent_loop_pipeline.py",
            tracked=True,
            size=100,
            reference_count=1,
            runtime_evidence={"success_count": 2, "latest_status": "success"},
        )

        self.assertEqual(Classification.FREEZE, frozen.category)
        self.assertEqual(Classification.KEEP, active.category)

    def test_inventory_contains_required_fields_and_does_not_modify_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "api").mkdir()
            source = root / "api" / "server.js"
            source.write_text('import "../src/app.js";\n', encoding="utf-8")
            (root / "src").mkdir()
            target = root / "src" / "app.js"
            target.write_text("export const app = true;\n", encoding="utf-8")

            before = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            inventory = build_inventory(
                root,
                tracked_paths={"api/server.js", "src/app.js"},
                git_changes={},
                runtime_evidence={},
                baseline_untracked=[],
            )
            after = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}

            self.assertEqual(before, after)
            self.assertEqual(
                {"api/server.js", "src/app.js", "config/ifind_refresh_token.txt"},
                {row["path"] for row in inventory["files"]},
            )
            required = {
                "path",
                "present",
                "tracked",
                "size",
                "category",
                "approved",
                "rationale",
                "imports",
                "referenced_by",
                "last_git_change",
                "runtime_evidence",
            }
            self.assertTrue(required.issubset(inventory["files"][0]))

    def test_manifest_output_is_deterministic_except_generated_at(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
            inventory = build_inventory(
                root,
                tracked_paths={"module.py"},
                git_changes={"module.py": "2026-07-13T00:00:00+00:00"},
                runtime_evidence={},
                baseline_untracked=[],
            )
            output = root / "legacy_manifest"

            write_manifests(inventory, output)
            first_json = json.loads((output / "inventory.json").read_text(encoding="utf-8"))
            first_csv = (output / "classifications.csv").read_text(encoding="utf-8")
            write_manifests(inventory, output)
            second_json = json.loads((output / "inventory.json").read_text(encoding="utf-8"))
            second_csv = (output / "classifications.csv").read_text(encoding="utf-8")

            first_json.pop("generated_at", None)
            second_json.pop("generated_at", None)
            self.assertEqual(first_json, second_json)
            self.assertEqual(first_csv, second_csv)


if __name__ == "__main__":
    unittest.main()
