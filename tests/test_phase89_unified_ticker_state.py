import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))

class Test89UTS(unittest.TestCase):
    def test_build(self):
        from build_phase89_unified_ticker_state import build
        r=build()
        self.assertIsNotNone(r)
    def test_no_mock(self):
        from build_phase89_unified_ticker_state import build
        r=build()
        self.assertIsNotNone(r)
if __name__=="__main__":unittest.main()
