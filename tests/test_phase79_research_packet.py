import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestResearchPacket(unittest.TestCase):
    def test_build(self):
        from build_phase79_research_packet import build
        r=build();p=r["phase79_research_packet"]
        self.assertEqual(p["tickers_checked"],3)
    def test_key_finding(self):
        from build_phase79_research_packet import build
        r=build();p=r["phase79_research_packet"]
        self.assertIn("688041",p["key_finding"])
    def test_no_pending(self):
        from build_phase79_research_packet import build
        r=build();p=r["phase79_research_packet"]
        self.assertEqual(p["pending_created"],0)
if __name__=="__main__":unittest.main()
