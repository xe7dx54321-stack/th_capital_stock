import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase32_review_action_audit_summary import build_payload, render_markdown
from phase31_helpers import make_conn_with_candidate


class Phase32ReviewActionAuditSummaryTests(unittest.TestCase):
    def test_audit_records_zero_outputs_cleanly(self):
        conn = make_conn_with_candidate()
        payload = build_payload(conn)
        self.assertEqual(payload["summary"]["audit_records"], 0)
        self.assertEqual(payload["summary"]["promotion_allowed_after_action_true"], 0)
        self.assertIn("Phase 32 Review Action Audit Summary", render_markdown(payload))


if __name__ == "__main__":
    unittest.main()
