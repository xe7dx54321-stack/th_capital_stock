import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestSignalLoader(unittest.TestCase):
    def test_load(self):from smr_phase81_time_series_signal_loader import load_signals;r=load_signals();rr=r["phase81_signal_loader"];self.assertGreater(rr["signals_loaded"],0)
    def test_has_confidence(self):from smr_phase81_time_series_signal_loader import load_signals;r=load_signals();rows=r["phase81_signal_loader"]["rows"];self.assertTrue(all("signal_confidence" in row and "consistency_status" in row and "cannot_conclude" in row for row in rows))
    def test_has_revenue(self):from smr_phase81_time_series_signal_loader import load_signals;r=load_signals();by=r["phase81_signal_loader"]["signals_by_metric"];self.assertIn("revenue",by)
if __name__=="__main__":unittest.main()
