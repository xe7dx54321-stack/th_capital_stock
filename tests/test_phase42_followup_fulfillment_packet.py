import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase42_followup_fulfillment_packet import build_payload
from phase42_helpers import make_phase42_conn


class Phase42FollowupFulfillmentPacketTests(unittest.TestCase):
    def test_packet_keeps_pending_disabled_and_no_confirmed_variables(self):
        payload = build_payload(make_phase42_conn(), "300308.SZ")
        packet = payload["followup_fulfillment_packet"]
        self.assertFalse(packet["pending_allowed"])
        self.assertEqual(packet["research_impact"], "no_confirmed_variable_added")
        self.assertFalse(packet["official_consensus"]["fulfilled"])
        self.assertFalse(packet["supplier_share"]["confirmed"])
        self.assertFalse(packet["confirmed_customer_allocation"]["confirmed"])
        self.assertEqual(payload["safety"]["pending_created"], 0)


if __name__ == "__main__":
    unittest.main()
