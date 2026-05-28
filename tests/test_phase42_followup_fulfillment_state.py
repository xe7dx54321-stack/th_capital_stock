import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase42_followup_fulfillment_state import build_payload
from phase42_helpers import make_phase42_conn


class Phase42FollowupFulfillmentStateTests(unittest.TestCase):
    def test_three_core_request_states_are_bounded(self):
        payload = build_payload(make_phase42_conn(), "300308.SZ")
        body = payload["followup_fulfillment_state"]
        self.assertEqual(body["requests_total"], 3)
        self.assertEqual(body["authorized_source_required"], 1)
        self.assertEqual(body["scenario_only"], 1)
        self.assertEqual(body["proxy_only"], 1)
        statuses = {row["request_type"]: row["status"] for row in body["request_rows"]}
        self.assertEqual(statuses["official_consensus"], "authorized_source_required")
        self.assertEqual(statuses["supplier_share"], "scenario_only")
        self.assertEqual(statuses["confirmed_customer_allocation"], "proxy_only")
        self.assertFalse(payload["safety"]["confirmed_variable_added"])
        self.assertEqual(payload["safety"]["pending_created"], 0)


if __name__ == "__main__":
    unittest.main()
