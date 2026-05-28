import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase41_supplier_share_route import build_payload
from phase41_helpers import make_phase41_conn_with_followups


class Phase41SupplierShareRouteTests(unittest.TestCase):
    def test_supplier_share_keeps_low_public_availability_caveat(self):
        payload = build_payload(make_phase41_conn_with_followups(), "300308.SZ")
        body = payload["supplier_share_route"]
        self.assertEqual(body["status"], "not_publicly_confirmable")
        self.assertFalse(body["confirmed_supplier_share_available"])
        self.assertFalse(body["supplier_share_confirmed"])
        self.assertEqual(body["recommended_usage"], "scenario_analysis_only")
        self.assertIn("do not mark scenario assumption as confirmed", body["do_not_do"])


if __name__ == "__main__":
    unittest.main()
