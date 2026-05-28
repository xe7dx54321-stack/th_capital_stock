import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "verification", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase37_300308_refreshed_research_packet import build_payload, render_markdown
from phase37_helpers import make_phase37_conn


class Phase37300308RefreshedPacketTests(unittest.TestCase):
    def test_refreshed_packet_has_before_after_and_no_trade_advice(self):
        payload = build_payload(make_phase37_conn())
        packet = payload["refreshed_research_packet"]
        self.assertIn("research_quality_before", packet)
        self.assertIn("research_quality_after", packet)
        self.assertFalse(packet["promotion_boundary"]["promotion_allowed"])
        text = json.dumps(payload, ensure_ascii=False).lower() + render_markdown(payload).lower()
        self.assertNotIn("buy recommendation", text)
        self.assertNotIn("sell recommendation", text)
        self.assertFalse(payload["safety"]["target_price_generated"])


if __name__ == "__main__":
    unittest.main()
