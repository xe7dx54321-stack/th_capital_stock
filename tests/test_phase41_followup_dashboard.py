import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase41_followup_dashboard import build_payload
from phase41_helpers import make_phase41_conn_with_followups


class Phase41FollowupDashboardTests(unittest.TestCase):
    def test_dashboard_reports_three_route_statuses_without_trade_advice(self):
        payload = build_payload(make_phase41_conn_with_followups())
        summary = payload["summary"]
        self.assertEqual(summary["followup_queue_items"], 3)
        self.assertEqual(summary["official_consensus_status"], "commercial_source_required")
        self.assertEqual(summary["supplier_share_status"], "not_publicly_confirmable")
        self.assertEqual(summary["customer_allocation_status"], "proxy_only")
        self.assertEqual(summary["pending_created"], 0)
        self.assertEqual(summary["paper_order_created"], 0)
        text = json.dumps(payload, ensure_ascii=False).lower()
        self.assertNotIn('"buy"', text)
        self.assertNotIn("target price", text)


if __name__ == "__main__":
    unittest.main()
