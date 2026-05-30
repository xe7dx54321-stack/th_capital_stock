import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestComparison(unittest.TestCase):
    def test_build(self):from build_phase84_previous_run_comparison import build;r=build();c=r["phase84_previous_run_comparison"];self.assertIn("has_previous_run",c)
    def test_first_run_ok(self):from build_phase84_previous_run_comparison import build;r=build();c=r["phase84_previous_run_comparison"];self.assertIn(c.get("comparison_status",""),["first_run_baseline","status_unchanged","status_strengthened","compared"])
    def test_no_mock(self):from build_phase84_previous_run_comparison import build;r=build();c=r["phase84_previous_run_comparison"];self.assertFalse(c["mock_used"])
if __name__=="__main__":unittest.main()
