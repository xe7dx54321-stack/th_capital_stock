import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase34_research_revalidation_packet import build_payload, render_markdown
from phase34_helpers import make_phase34_conn


class Phase34ResearchRevalidationPacketTests(unittest.TestCase):
    def test_packet_has_promotion_boundary_and_no_trade_recommendation(self):
        payload = build_payload(make_phase34_conn(), ticker="300394.SZ")
        packet = payload["research_revalidation_packet"]
        self.assertFalse(packet["promotion_status"]["promotion_allowed"])
        markdown = render_markdown(payload).lower()
        self.assertNotIn("buy", markdown)
        self.assertNotIn("sell", markdown)
        self.assertIn("promotion boundary", markdown)


if __name__ == "__main__":
    unittest.main()
