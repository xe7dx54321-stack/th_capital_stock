import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestResearchPacket(unittest.TestCase):
    def test_build(self):from build_phase84_daily_research_packet import build;r=build();p=r["phase84_daily_research_packet"];self.assertGreater(p["tickers_checked"],0)
    def test_has_finding(self):from build_phase84_daily_research_packet import build;r=build();p=r["phase84_daily_research_packet"];self.assertIn("key_finding",p)
    def test_no_pending(self):from build_phase84_daily_research_packet import build;r=build();p=r["phase84_daily_research_packet"];self.assertEqual(p["pending_created"],0)
    def test_no_order(self):from build_phase84_daily_research_packet import build;r=build();p=r["phase84_daily_research_packet"];self.assertEqual(p["paper_order_created"],0)
if __name__=="__main__":unittest.main()
