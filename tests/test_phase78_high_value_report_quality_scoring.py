import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestQualityScoring(unittest.TestCase):
    def test_build(self):
        from build_phase78_high_value_report_quality_scoring import build
        r=build();q=r["phase78_high_value_report_quality_scoring"]
        self.assertEqual(q["reports_scored"],3)
    def test_annual_high(self):
        from build_phase78_high_value_report_quality_scoring import build
        r=build();rows=r["phase78_high_value_report_quality_scoring"]["rows"]
        for row in rows:
            if row["document_type"]=="annual_report":
                self.assertGreater(row["reliability_score"],0.9)
    def test_all_allowed(self):
        from build_phase78_high_value_report_quality_scoring import build
        r=build();rows=r["phase78_high_value_report_quality_scoring"]["rows"]
        for row in rows:
            self.assertTrue(row["allowed_for_deep_extraction"])
if __name__=="__main__":unittest.main()
