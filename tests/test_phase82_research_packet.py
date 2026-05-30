import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestResearchPacket(unittest.TestCase):
    def test_build(self):from build_phase82_research_packet import build;r=build();rp=r["phase82_research_packet"];self.assertGreater(rp["tickers_checked"],0)
    def test_has_keyfinding(self):from build_phase82_research_packet import build;r=build();self.assertIn("key_finding",r["phase82_research_packet"])
    def test_no_pending(self):from build_phase82_research_packet import build;r=build();rp=r["phase82_research_packet"];self.assertEqual(rp["pending_created"],0)
if __name__=="__main__":unittest.main()
