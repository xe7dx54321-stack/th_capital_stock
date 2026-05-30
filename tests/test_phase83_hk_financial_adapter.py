import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestHKAdapter(unittest.TestCase):
    def test_run(self):from smr_phase83_hk_financial_adapter import run_hk_adapter;r=run_hk_adapter();hk=r["phase83_hk_financial_adapter"];self.assertGreater(hk["tickers_checked"],0)
    def test_no_mock(self):from smr_phase83_hk_financial_adapter import run_hk_adapter;r=run_hk_adapter();self.assertFalse(r["phase83_hk_financial_adapter"]["mock_used"])
    def test_not_wrap_unavailable(self):from smr_phase83_hk_financial_adapter import run_hk_adapter;r=run_hk_adapter();rows=r["phase83_hk_financial_adapter"]["rows"];self.assertFalse(any(r["structured_data_available"]==False and len(r["metrics_available"])>0 for r in rows))
if __name__=="__main__":unittest.main()
