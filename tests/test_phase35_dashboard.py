import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase35_research_packet_dashboard import build_payload, render_markdown
from phase34_helpers import make_phase34_conn


class Phase35DashboardTests(unittest.TestCase):
    def test_dashboard_defaults_to_two_packets_without_pending(self):
        payload = build_payload(make_phase34_conn())
        self.assertEqual(payload["summary"]["research_packets"], 2)
        self.assertEqual(payload["summary"]["new_pending_created"], 0)
        self.assertEqual(payload["summary"]["paper_order_created"], 0)
        tickers = {row["ticker"] for row in payload["ticker_rows"]}
        self.assertEqual(tickers, {"300394.SZ", "300308.SZ"})
        self.assertIn("Phase 35 Research Packet Dashboard", render_markdown(payload))


if __name__ == "__main__":
    unittest.main()
