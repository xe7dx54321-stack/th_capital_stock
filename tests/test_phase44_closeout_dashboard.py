import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "verification", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase44_closeout_dashboard import build_payload
from phase44_helpers import make_phase44_closeout_conn


class Phase44CloseoutDashboardTests(unittest.TestCase):
    def test_dashboard_reports_branch_closed_without_trade_advice(self):
        payload = build_payload(make_phase44_closeout_conn())
        summary = payload["summary"]
        self.assertEqual(summary["manual_candidates_reviewed"], 3)
        self.assertEqual(summary["manual_intake_branch_status"], "closed")
        self.assertEqual(summary["next_mainline_step"], "phase45_final_research_packet_review")
        self.assertEqual(summary["pending_created"], 0)
        text = json.dumps(payload, ensure_ascii=False).lower()
        self.assertNotIn('"buy"', text)
        self.assertNotIn('"sell"', text)
        self.assertNotIn("target price", text)


if __name__ == "__main__":
    unittest.main()
