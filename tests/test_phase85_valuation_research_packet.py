import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestResearchPacket(unittest.TestCase):
    def test_build(self):from build_phase85_valuation_research_packet import build;r=build();p=r["phase85_valuation_research_packet"];self.assertGreater(p["tickers_checked"],0)
    def test_no_pending(self):from build_phase85_valuation_research_packet import build;r=build();p=r["phase85_valuation_research_packet"];self.assertEqual(p["pending_created"],0)
    def test_no_target_price(self):from build_phase85_valuation_research_packet import build;r=build();p=r["phase85_valuation_research_packet"];self.assertEqual(p["target_price_created"],0)
if __name__=="__main__":unittest.main()
