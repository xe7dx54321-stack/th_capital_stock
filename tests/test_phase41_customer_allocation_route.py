import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase41_customer_allocation_route import build_payload
from phase41_helpers import make_phase41_conn_with_followups


class Phase41CustomerAllocationRouteTests(unittest.TestCase):
    def test_customer_allocation_proxy_is_not_confirmed(self):
        payload = build_payload(make_phase41_conn_with_followups(), "300308.SZ")
        body = payload["customer_allocation_route"]
        self.assertEqual(body["status"], "proxy_only")
        self.assertFalse(body["confirmed_customer_allocation_available"])
        self.assertFalse(body["customer_allocation_confirmed"])
        self.assertEqual(body["proxy_allowed_usage"], "bear_case_context_or_scenario_support")
        self.assertIn("do not infer NVIDIA allocation from North America customer references", body["do_not_do"])


if __name__ == "__main__":
    unittest.main()
