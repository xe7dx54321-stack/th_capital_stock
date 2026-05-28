import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "jobs", ROOT / "08_scripts" / "verification", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase43_manual_intake_dashboard import build_payload
from phase43_helpers import make_phase43_conn_with_persisted


class Phase43DashboardTests(unittest.TestCase):
    def test_dashboard_distinguishes_candidates_from_confirmed_without_trade_terms(self):
        payload = build_payload(make_phase43_conn_with_persisted())
        summary = payload["summary"]
        self.assertEqual(summary["payloads_checked"], 3)
        self.assertEqual(summary["candidates_created"], 3)
        self.assertEqual(summary["candidates_written"], 3)
        self.assertFalse(summary["official_consensus_confirmed"])
        self.assertFalse(summary["supplier_share_confirmed"])
        self.assertFalse(summary["customer_allocation_confirmed"])
        self.assertEqual(summary["pending_created"], 0)
        text = json.dumps(payload, ensure_ascii=False).lower()
        self.assertNotIn('"buy"', text)
        self.assertNotIn('"sell"', text)
        self.assertNotIn("target price", text)


if __name__ == "__main__":
    unittest.main()
