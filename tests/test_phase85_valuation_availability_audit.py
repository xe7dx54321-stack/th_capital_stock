import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestAvailabilityAudit(unittest.TestCase):
    def test_build(self):from build_phase85_valuation_availability_audit import build;r=build();a=r["phase85_valuation_availability_audit"];self.assertGreater(a["tickers_checked"],0)
    def test_known_blocked(self):from build_phase85_valuation_availability_audit import build;r=build();a=r["phase85_valuation_availability_audit"];self.assertGreaterEqual(a["known_blocked"],1)
    def test_not_wrap_unavailable(self):from build_phase85_valuation_availability_audit import build;r=build();rows=r["phase85_valuation_availability_audit"]["rows"];self.assertTrue(all(r["valuation_status"]!="available" or r["valuation_available"]==True for r in rows if r["valuation_status"]!="known_blocked"))
if __name__=="__main__":unittest.main()
