import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase40_research_review_audit_report import build_payload
from phase40_helpers import make_phase40_conn_with_action


class Phase40ResearchReviewAuditTests(unittest.TestCase):
    def test_audit_report_records_before_after(self):
        payload = build_payload(make_phase40_conn_with_action())
        body = payload["research_review_audit_report"]
        self.assertEqual(body["audit_records"], 1)
        self.assertEqual(body["pending_created"], 0)
        self.assertEqual(body["paper_order_created"], 0)
        self.assertEqual(body["records"][0]["before_status"], "research_review_candidate")
        self.assertEqual(body["records"][0]["after_status"], "reviewed_request_deeper_research")


if __name__ == "__main__":
    unittest.main()
