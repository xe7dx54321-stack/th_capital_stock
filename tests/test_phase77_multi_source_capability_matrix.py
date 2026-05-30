import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestMatrix(unittest.TestCase):
    def test_build(self):
        from build_phase77_multi_source_capability_matrix import build
        r=build();m=r["phase77_multi_source_capability_matrix"]
        self.assertEqual(m["tickers_checked"],3)
if __name__=="__main__":unittest.main()
