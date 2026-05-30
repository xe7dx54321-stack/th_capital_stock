import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestMultiSourceMatrix(unittest.TestCase):
    def test_build(self):
        from build_phase78_multi_source_capability_matrix import build
        r=build();m=r["phase78_multi_source_capability_matrix"]
        self.assertEqual(m["tickers_checked"],3)
    def test_chinese_matching_field(self):
        from build_phase78_multi_source_capability_matrix import build
        r=build();m=r["phase78_multi_source_capability_matrix"]
        self.assertGreater(m["tickers_with_chinese_matching_repaired"],0)
    def test_high_value_harvest_field(self):
        from build_phase78_multi_source_capability_matrix import build
        r=build();m=r["phase78_multi_source_capability_matrix"]
        self.assertGreater(m["tickers_with_high_value_report_text"],0)
    def test_300394_blocked(self):
        from build_phase78_multi_source_capability_matrix import build
        r=build();rows=r["phase78_multi_source_capability_matrix"]["rows"]
        f394=[r for r in rows if r["ticker"]=="300394.SZ"]
        self.assertEqual(len(f394),1)
        self.assertIn("blocked",f394[0]["overall"])
if __name__=="__main__":unittest.main()
