import unittest; from phase51_helpers import make_phase51_fixture_candidates
from smr_quoted_span_validator import build_span_report
class Phase51SpanValidatorTests(unittest.TestCase):
    def test_all_checked(self):
        c = make_phase51_fixture_candidates(); r = build_span_report(c)
        self.assertEqual(r["quoted_span_validation"]["candidates_checked"], 9)
    def test_title_only_downgraded(self):
        c = make_phase51_fixture_candidates()
        c[8]["quoted_span"] = "关于公司日常经营合同的公告"; c[8]["chunk_id"] = ""
        r = build_span_report(c)
        rows = r["quoted_span_validation"]["rows"]
        self.assertIn(rows[8]["span_status"], ("downgraded", "rejected"))
    def test_span_score_range(self):
        c = make_phase51_fixture_candidates(); r = build_span_report(c)
        for row in r["quoted_span_validation"]["rows"]:
            self.assertGreaterEqual(row["span_score"], 0)
            self.assertLessEqual(row["span_score"], 1)
if __name__ == "__main__": unittest.main()
