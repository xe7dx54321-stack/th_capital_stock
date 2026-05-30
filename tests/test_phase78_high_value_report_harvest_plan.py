import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestHarvestPlan(unittest.TestCase):
    def test_build(self):
        from build_phase78_688041_high_value_report_harvest_plan import build
        r=build();p=r["phase78_688041_high_value_report_harvest_plan"]
        self.assertEqual(p["ticker"],"688041.SH")
        self.assertGreater(p["p0_targets"],0)
    def test_has_annual_report(self):
        from build_phase78_688041_high_value_report_harvest_plan import build
        r=build();rows=r["phase78_688041_high_value_report_harvest_plan"]["rows"]
        types=[row["report_type"] for row in rows]
        self.assertIn("annual_report",types)
    def test_has_prospectus(self):
        from build_phase78_688041_high_value_report_harvest_plan import build
        r=build();rows=r["phase78_688041_high_value_report_harvest_plan"]["rows"]
        types=[row["report_type"] for row in rows]
        self.assertIn("prospectus",types)
if __name__=="__main__":unittest.main()
