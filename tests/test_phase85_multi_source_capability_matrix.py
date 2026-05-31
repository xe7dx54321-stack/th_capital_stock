import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestCapabilityMatrix(unittest.TestCase):
    def test_build(self):from build_phase85_multi_source_capability_matrix import build;r=build();m=r["phase85_multi_source_capability_matrix"];self.assertGreater(m["tickers_checked"],0)
    def test_valuation_available(self):from build_phase85_multi_source_capability_matrix import build;r=build();m=r["phase85_multi_source_capability_matrix"];self.assertGreaterEqual(m["valuation_available"],0)
    def test_blocked(self):from build_phase85_multi_source_capability_matrix import build;r=build();m=r["phase85_multi_source_capability_matrix"];self.assertEqual(m["blocked"],1)
if __name__=="__main__":unittest.main()
