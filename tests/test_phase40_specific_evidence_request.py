import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase40_specific_evidence_requests import build_payload
from phase40_helpers import make_phase40_conn_with_action
from smr_specific_evidence_request import build_specific_evidence_request


class Phase40SpecificEvidenceRequestTests(unittest.TestCase):
    def test_official_consensus_requires_authorized_source(self):
        request = build_specific_evidence_request("300308.SZ", "official_consensus")
        self.assertEqual(request["allowed_source_route"], "authorized_source_required")
        self.assertIn("do not treat internal proxy as official consensus", request["do_not_do"])

    def test_specific_request_report_after_action(self):
        conn = make_phase40_conn_with_action(action="request_specific_evidence", evidence_type="official_consensus")
        payload = build_payload(conn, "300308.SZ")
        self.assertEqual(payload["summary"]["requests_total"], 1)
        self.assertEqual(payload["summary"]["open_requests"], 1)
        self.assertEqual(payload["summary"]["pending_created"], 0)


if __name__ == "__main__":
    unittest.main()
