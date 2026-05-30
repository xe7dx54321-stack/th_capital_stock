import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestSignalLoader(unittest.TestCase):
    def test_build(self):from build_phase84_daily_signal_loader_report import build;r=build();s=r["phase84_daily_signal_loader"];self.assertGreater(s["signals_loaded"],0)
    def test_has_currency(self):from build_phase84_daily_signal_loader_report import build;r=build();rows=r["phase84_daily_signal_loader"]["rows"];self.assertTrue(all("currency" in row for row in rows))
    def test_has_cannot_conclude(self):from build_phase84_daily_signal_loader_report import build;r=build();rows=r["phase84_daily_signal_loader"]["rows"];self.assertTrue(all(len(row["cannot_conclude"])>0 for row in rows))
if __name__=="__main__":unittest.main()
