import unittest; from phase51_helpers import make_phase51_fixture_candidates
from smr_source_traceability_scoring import build_traceability_report
class Phase51TraceabilityTests(unittest.TestCase):
    def test_all_checked(self):
        c = make_phase51_fixture_candidates(); r = build_traceability_report(c)
        self.assertEqual(r["source_traceability_score"]["candidates_checked"], 9)
    def test_score_range(self):
        c = make_phase51_fixture_candidates(); r = build_traceability_report(c)
        for row in r["source_traceability_score"]["rows"]:
            self.assertGreaterEqual(row["traceability_score"], 0)
            self.assertLessEqual(row["traceability_score"], 1)
    def test_missing_source_downgraded(self):
        c = make_phase51_fixture_candidates()
        c[0]["source_id"] = ""; c[0]["chunk_id"] = ""
        r = build_traceability_report(c)
        self.assertEqual(r["source_traceability_score"]["rows"][0]["traceability_bucket"], "low")
if __name__ == "__main__": unittest.main()
