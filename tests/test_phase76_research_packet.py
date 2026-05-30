import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))

class TestResearchPacket(unittest.TestCase):
    def test_build(self):
        from build_phase76_research_packet import build
        r = build()
        pkt = r["phase76_research_packet"]
        self.assertEqual(pkt["tickers_checked"], 3)
    def test_key_finding(self):
        from build_phase76_research_packet import build
        r = build()
        self.assertIn("key_finding", r["phase76_research_packet"])

if __name__ == "__main__": unittest.main()
