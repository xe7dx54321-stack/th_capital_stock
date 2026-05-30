import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestUSAdapter(unittest.TestCase):
    def test_run(self):from smr_phase83_us_financial_adapter import run_us_adapter;r=run_us_adapter();us=r["phase83_us_financial_adapter"];self.assertGreater(us["tickers_checked"],0)
    def test_no_mock(self):from smr_phase83_us_financial_adapter import run_us_adapter;r=run_us_adapter();self.assertFalse(r["phase83_us_financial_adapter"]["mock_used"])
if __name__=="__main__":unittest.main()
