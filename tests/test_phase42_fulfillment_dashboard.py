import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "verification", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase42_fulfillment_dashboard import build_payload
from phase42_helpers import make_phase42_conn


class Phase42FulfillmentDashboardTests(unittest.TestCase):
    def test_dashboard_reports_fulfillment_boundaries_without_trade_advice(self):
        payload = build_payload(make_phase42_conn())
        summary = payload["summary"]
        self.assertEqual(summary["followup_requests"], 3)
        self.assertEqual(summary["authorized_source_required"], 1)
        self.assertEqual(summary["scenario_only"], 1)
        self.assertEqual(summary["proxy_only"], 1)
        self.assertEqual(summary["pending_created"], 0)
        text = json.dumps(payload, ensure_ascii=False).lower()
        self.assertNotIn('"buy"', text)
        self.assertNotIn('"sell"', text)
        self.assertNotIn("target price", text)


if __name__ == "__main__":
    unittest.main()
