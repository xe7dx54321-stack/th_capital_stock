import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestIntegration(unittest.TestCase):
    def test_build(self):from build_phase85_valuation_daily_integration_report import build;r=build();i=r["phase85_valuation_daily_integration"];self.assertGreater(i["integrated_signals"],0)
    def test_has_valuation_note(self):from build_phase85_valuation_daily_integration_report import build;r=build();rows=r["phase85_valuation_daily_integration"]["rows"];self.assertTrue(all(len(row["valuation_note"])>0 for row in rows))
if __name__=="__main__":unittest.main()
