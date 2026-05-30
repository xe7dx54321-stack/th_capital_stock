import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestCapabilityMatrix(unittest.TestCase):
    def test_build(self):from build_phase83_multi_source_capability_matrix import build;r=build();m=r["phase83_multi_source_capability_matrix"];self.assertGreater(m["tickers_checked"],0)
    def test_markets_separate(self):from build_phase83_multi_source_capability_matrix import build;r=build();m=r["phase83_multi_source_capability_matrix"];self.assertGreaterEqual(m["cn_a_covered"],0);self.assertGreaterEqual(m["hk_covered"],0);self.assertGreaterEqual(m["us_covered"],0)
    def test_no_pending(self):from build_phase83_multi_source_capability_matrix import build;r=build();m=r["phase83_multi_source_capability_matrix"];self.assertEqual(m["pending_created"],0)
    def test_no_order(self):from build_phase83_multi_source_capability_matrix import build;r=build();m=r["phase83_multi_source_capability_matrix"];self.assertEqual(m["paper_order_created"],0)
if __name__=="__main__":unittest.main()
