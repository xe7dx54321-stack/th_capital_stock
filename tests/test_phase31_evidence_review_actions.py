import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
TEST_DIR = ROOT / "tests"
for path in (LIB_DIR, TEST_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from phase31_helpers import make_conn_with_candidate, phase31_candidate
from smr_download_repair_queue import list_download_repair_tasks
from smr_evidence_lifecycle import get_lifecycle_state
from smr_evidence_review_actions import apply_evidence_review_action


class Phase31EvidenceReviewActionsTests(unittest.TestCase):
    def test_approve_evidence_does_not_allow_promotion(self):
        conn = make_conn_with_candidate()
        result = apply_evidence_review_action(conn, evidence_id="ev_semantic_ir_test", action="approve_evidence", dry_run=True)
        self.assertTrue(result["allowed"])
        self.assertFalse(result["after"]["usable_for_promotion"])
        self.assertFalse(result["safety_checks"]["promotion_allowed"])

    def test_forbidden_confirmed_upgrade_blocked(self):
        conn = make_conn_with_candidate()
        result = apply_evidence_review_action(conn, evidence_id="ev_semantic_ir_test", action="upgrade_to_confirmed_supplier_share", dry_run=True)
        self.assertFalse(result["allowed"])
        self.assertIn("forbidden action", result["reason"])

    def test_downgrade_usage_cannot_upgrade(self):
        conn = make_conn_with_candidate(phase31_candidate(allowed_usage="context_only"))
        result = apply_evidence_review_action(conn, evidence_id="ev_semantic_ir_test", action="downgrade_usage", target_usage="valuation_support", dry_run=True)
        self.assertFalse(result["allowed"])

    def test_execute_mark_as_noise_blocks_variable_pack_usage(self):
        conn = make_conn_with_candidate()
        result = apply_evidence_review_action(conn, evidence_id="ev_semantic_ir_test", action="mark_as_noise", dry_run=False)
        self.assertTrue(result["allowed"])
        state = get_lifecycle_state(conn, "ev_semantic_ir_test")
        self.assertEqual(state["lifecycle_status"], "marked_noise")
        self.assertEqual(state["allowed_usage"], "blocked")

    def test_request_better_source_creates_repair_item(self):
        conn = make_conn_with_candidate()
        apply_evidence_review_action(conn, evidence_id="ev_semantic_ir_test", action="request_better_source", reason="need better source", dry_run=False)
        tasks = list_download_repair_tasks(conn)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["task_type"], "MANUAL_TEXT_NEEDED")


if __name__ == "__main__":
    unittest.main()
