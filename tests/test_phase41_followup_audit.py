import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase41_followup_audit_report import build_payload
from phase41_helpers import make_phase41_conn_with_followups


class Phase41FollowupAuditTests(unittest.TestCase):
    def test_followup_audit_records_request_creation(self):
        payload = build_payload(make_phase41_conn_with_followups())
        body = payload["followup_audit_report"]
        self.assertEqual(body["audit_records"], 3)
        self.assertEqual(body["pending_created"], 0)
        self.assertEqual(body["paper_order_created"], 0)
        self.assertEqual({row["action"] for row in body["records"]}, {"create_specific_evidence_request"})


if __name__ == "__main__":
    unittest.main()
