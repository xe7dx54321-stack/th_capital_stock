import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestRunState(unittest.TestCase):
    def test_schema(self):from build_phase84_daily_run_state_schema_report import build;r=build();s=r["phase84_daily_run_state_schema"];self.assertIn("run_state_fields",s)
    def test_ticker_fields(self):from build_phase84_daily_run_state_schema_report import build;r=build();s=r["phase84_daily_run_state_schema"];self.assertIn("ticker_result_fields",s)
if __name__=="__main__":unittest.main()
