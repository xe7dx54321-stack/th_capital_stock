import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestInventory(unittest.TestCase):
    def test_build(self):
        from build_phase78_688041_high_value_report_inventory import build
        r=build();inv=r["phase78_688041_high_value_report_inventory"]
        self.assertEqual(inv["ticker"],"688041.SH")
        self.assertGreater(inv["high_value_candidates_found"],0)
    def test_no_legal(self):
        from build_phase78_688041_high_value_report_inventory import build
        r=build();rows=r["phase78_688041_high_value_report_inventory"]["rows"]
        for row in rows:
            self.assertNotIn(row["report_type"],["legal_opinion","shareholder_meeting_resolution","governance_policy"])
    def test_annual_quarterly(self):
        from build_phase78_688041_high_value_report_inventory import build
        r=build();inv=r["phase78_688041_high_value_report_inventory"]
        self.assertGreater(inv["annual_reports_found"],0)
        self.assertGreater(inv["quarterly_reports_found"],0)
if __name__=="__main__":unittest.main()
