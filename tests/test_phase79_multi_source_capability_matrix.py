import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestMatrix(unittest.TestCase):
    def test_build(self):
        from build_phase79_multi_source_capability_matrix import build
        r=build();m=r["phase79_multi_source_capability_matrix"]
        self.assertEqual(m["tickers_checked"],3)
    def test_quant_extraction(self):
        from build_phase79_multi_source_capability_matrix import build
        r=build();m=r["phase79_multi_source_capability_matrix"]
        self.assertGreater(m["tickers_with_quantitative_extraction"],0)
    def test_300394_blocked(self):
        from build_phase79_multi_source_capability_matrix import build
        r=build();rows=r["phase79_multi_source_capability_matrix"]["rows"]
        f394=[r for r in rows if r["ticker"]=="300394.SZ"]
        self.assertIn("blocked",f394[0]["overall"])
if __name__=="__main__":unittest.main()
