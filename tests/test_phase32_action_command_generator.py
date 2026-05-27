import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
for path in (LIB_DIR,):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from smr_evidence_action_command_generator import build_dry_run_command, recommended_action_for_item


class Phase32ActionCommandGeneratorTests(unittest.TestCase):
    def test_dry_run_command_generated_without_execute(self):
        item = {"evidence_id": "ev_semantic_ir_test", "variable_type": "capacity_signal", "recommended_action": "approve_evidence"}
        command = build_dry_run_command(item)
        self.assertIn("--dry-run --json", command["dry_run_command"])
        self.assertNotIn("--execute", command["dry_run_command"])
        self.assertFalse(command["execute_command_available"])

    def test_sensitive_item_recommendation_is_conservative(self):
        item = {"evidence_id": "ev_semantic_ir_test", "variable_type": "customer_allocation_signal", "recommended_action": "approve_evidence"}
        self.assertEqual(build_dry_run_command(item)["recommended_action"], "downgrade_usage")
        self.assertEqual(recommended_action_for_item(item), "downgrade_usage")

    def test_mark_noise_requires_reason(self):
        item = {"evidence_id": "ev_semantic_ir_test", "variable_type": "capacity_signal", "recommended_action": "mark_as_noise"}
        command = build_dry_run_command(item)
        self.assertIn("--reason", command["dry_run_command"])

    def test_download_repair_item_gets_repair_dry_run_command(self):
        item = {"item_type": "download_repair", "repair_task_id": "repair_download_ir_test", "recommended_action": "manual_text_needed"}
        command = build_dry_run_command(item)
        self.assertIn("upsert_download_unavailable_repair_tasks.py", command["dry_run_command"])
        self.assertIn("--dry-run --json", command["dry_run_command"])

    def test_non_persisted_item_gets_batch_dry_run_command(self):
        item = {"evidence_id": "ev_semantic_ir_review_only", "persisted_in_evidence_store": False, "recommended_action": "mark_as_noise"}
        command = build_dry_run_command(item)
        self.assertIn("run_phase32_batch_review_dry_run.py", command["dry_run_command"])
        self.assertIn("--evidence-id ev_semantic_ir_review_only", command["dry_run_command"])
        self.assertIn("--dry-run --json", command["dry_run_command"])


if __name__ == "__main__":
    unittest.main()
