import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestRunHistory(unittest.TestCase):
    def test_build(self):from build_phase84_daily_run_history_report import build;r=build();h=r["phase84_daily_run_history"];self.assertTrue(h["history_enabled"])
    def test_path_ignored(self):from build_phase84_daily_run_history_report import build;r=build();h=r["phase84_daily_run_history"];self.assertTrue(h["history_path_ignored"])
    def test_no_mock(self):from build_phase84_daily_run_history_report import build;r=build();h=r["phase84_daily_run_history"];self.assertFalse(h["mock_used"])
if __name__=="__main__":unittest.main()
