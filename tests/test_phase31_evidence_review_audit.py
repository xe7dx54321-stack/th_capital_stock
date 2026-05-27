import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
TEST_DIR = ROOT / "tests"
for path in (LIB_DIR, REPORTING_DIR, TEST_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase31_evidence_review_audit_report import build_payload, render_markdown
from phase31_helpers import make_conn_with_candidate
from smr_evidence_review_actions import apply_evidence_review_action


class Phase31EvidenceReviewAuditTests(unittest.TestCase):
    def test_execute_action_writes_audit_log(self):
        conn = make_conn_with_candidate()
        apply_evidence_review_action(conn, evidence_id="ev_semantic_ir_test", action="approve_evidence", dry_run=False)
        payload = build_payload(conn)
        self.assertEqual(payload["summary"]["audit_records"], 1)
        self.assertEqual(payload["summary"]["promotion_allowed_true"], 0)
        self.assertIn("Phase 31 Evidence Review Audit Report", render_markdown(payload))


if __name__ == "__main__":
    unittest.main()
