import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestHKAdapter(unittest.TestCase):
    def test_build(self):from build_phase85_hk_valuation_adapter_report import build;r=build();a=r["phase85_hk_valuation_adapter"];self.assertGreater(a["tickers_checked"],0)
    def test_no_mock(self):from build_phase85_hk_valuation_adapter_report import build;r=build();a=r["phase85_hk_valuation_adapter"];self.assertFalse(a["mock_used"])
if __name__=="__main__":unittest.main()
