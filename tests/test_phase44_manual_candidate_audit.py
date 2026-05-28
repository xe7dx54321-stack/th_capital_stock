import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase44_manual_candidate_review_audit import build_payload
from phase44_helpers import make_phase44_closeout_conn


class Phase44ManualCandidateAuditTests(unittest.TestCase):
    def test_audit_report_records_three_execute_actions(self):
        payload = build_payload(make_phase44_closeout_conn(), "300308.SZ")
        body = payload["manual_candidate_review_audit"]
        self.assertGreaterEqual(body["audit_records"], 3)
        self.assertEqual(body["usable_for_promotion_true"], 0)
        self.assertEqual(body["pending_created"], 0)
        for record in body["records"]:
            self.assertTrue(record["before_status"])
            self.assertTrue(record["after_status"])
            self.assertFalse(record["usable_for_promotion"])


if __name__ == "__main__":
    unittest.main()
