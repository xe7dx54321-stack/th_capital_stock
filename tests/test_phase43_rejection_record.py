import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase43_manual_intake_rejection_report import build_payload
from phase42_helpers import make_phase42_conn
from phase43_helpers import make_phase43_conn_with_rejection


class Phase43RejectionRecordTests(unittest.TestCase):
    def test_rejection_report_includes_invalid_sample_fix(self):
        payload = build_payload(make_phase42_conn(), "300308.SZ")
        body = payload["manual_intake_rejection_report"]
        self.assertEqual(body["sample_rejection_records"], 1)
        record = body["records"][0]
        self.assertIn("internal_proxy_cannot_be_official_consensus", record["rejection_reasons"])
        self.assertEqual(record["recommended_fix"], "provide authorized consensus source metadata")

    def test_execute_invalid_sample_writes_rejection_record(self):
        payload = build_payload(make_phase43_conn_with_rejection(), "300308.SZ")
        body = payload["manual_intake_rejection_report"]
        self.assertEqual(body["persisted_rejection_records"], 1)
        self.assertEqual(body["pending_created"], 0)


if __name__ == "__main__":
    unittest.main()
