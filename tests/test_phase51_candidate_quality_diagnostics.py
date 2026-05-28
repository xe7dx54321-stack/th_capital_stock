import unittest; from phase51_helpers import make_phase51_fixture_candidates
from smr_candidate_quality_diagnostics import build_diagnostics
class Phase51DiagnosticsTests(unittest.TestCase):
    def test_all_checked(self):
        c = make_phase51_fixture_candidates(); r = build_diagnostics(c)
        self.assertEqual(r["candidate_quality_diagnostics"]["candidates_checked"], 9)
    def test_downgraded(self):
        c = make_phase51_fixture_candidates(); r = build_diagnostics(c)
        self.assertGreater(r["candidate_quality_diagnostics"]["downgraded_before"], 0)
    def test_reasons_present(self):
        c = make_phase51_fixture_candidates(); r = build_diagnostics(c)
        rows = r["candidate_quality_diagnostics"]["rows"]
        self.assertTrue(all(len(row["downgrade_reasons"]) > 0 for row in rows))
    def test_no_pending(self):
        c = make_phase51_fixture_candidates(); r = build_diagnostics(c)
        self.assertEqual(r["candidate_quality_diagnostics"]["pending_created"], 0)
if __name__ == "__main__": unittest.main()
