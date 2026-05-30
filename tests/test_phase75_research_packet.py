import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))

class TestPhase75ResearchPacket(unittest.TestCase):
    def test_build(self):
        from build_phase75_research_packet import build
        r = build()
        pkt = r["phase75_research_packet"]
        self.assertEqual(pkt["tickers_checked"], 3)
        self.assertEqual(pkt["fallback_texts_usable"], 0)
    def test_key_finding_present(self):
        from build_phase75_research_packet import build
        r = build()
        pkt = r["phase75_research_packet"]
        self.assertIn("key_finding", pkt)

if __name__ == "__main__":
    unittest.main()
