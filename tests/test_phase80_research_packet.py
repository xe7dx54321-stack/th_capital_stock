import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestResearchPacket(unittest.TestCase):
    def test_build(self):from build_phase80_research_packet import build;r=build();rp=r["phase80_research_packet"];self.assertGreater(rp["tickers_checked"],0)
    def test_has_keyfinding(self):from build_phase80_research_packet import build;r=build();self.assertIn("key_finding",r["phase80_research_packet"])
    def test_no_pending(self):from build_phase80_research_packet import build;r=build();rp=r["phase80_research_packet"];self.assertEqual(rp["pending_created"],0);self.assertEqual(rp["paper_order_created"],0);self.assertEqual(rp["real_trade_created"],0)
    def test_300394_blocker(self):from build_phase80_research_packet import build;r=build();rows=r["phase80_research_packet"]["rows"];row=[x for x in rows if x["ticker"]=="300394.SZ"];self.assertEqual(len(row),1);self.assertIn("blocker",row[0]["baseline_status"])
    def test_no_mock(self):from build_phase80_research_packet import build;r=build();self.assertFalse(r["phase80_research_packet"]["mock_used"]);self.assertFalse(r["phase80_research_packet"]["fixture_used"])
if __name__=="__main__":unittest.main()
