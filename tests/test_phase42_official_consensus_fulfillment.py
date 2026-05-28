import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase42_official_consensus_fulfillment import build_payload
from phase42_helpers import make_phase42_conn


class Phase42OfficialConsensusFulfillmentTests(unittest.TestCase):
    def test_authorized_source_required_and_internal_proxy_not_allowed(self):
        payload = build_payload(make_phase42_conn(), "300308.SZ")
        body = payload["official_consensus_fulfillment"]
        self.assertEqual(body["fulfillment_status"], "authorized_source_required")
        self.assertTrue(body["authorized_source_required"])
        self.assertFalse(body["internal_proxy_allowed"])
        self.assertFalse(body["fulfilled"])
        self.assertFalse(payload["safety"]["official_consensus_added"])


if __name__ == "__main__":
    unittest.main()
