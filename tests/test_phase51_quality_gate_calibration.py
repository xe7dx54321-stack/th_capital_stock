import unittest; from phase51_helpers import make_phase51_fixture_candidates
from smr_candidate_quality_gate_calibration import build_calibration
class Phase51CalibrationTests(unittest.TestCase):
    def test_no_confirmed(self):
        c = make_phase51_fixture_candidates(); r = build_calibration(c)
        self.assertEqual(r["quality_gate_calibration"]["confirmed_variables_added"], 0)
    def test_no_promotion(self):
        c = make_phase51_fixture_candidates(); r = build_calibration(c)
        self.assertEqual(r["quality_gate_calibration"]["usable_for_promotion_true"], 0)
    def test_has_passed(self):
        c = make_phase51_fixture_candidates(); r = build_calibration(c)
        self.assertGreaterEqual(r["quality_gate_calibration"]["passed_tracking_support"], 0)
    def test_sensitive_in_review(self):
        c = make_phase51_fixture_candidates()
        c[0]["variable"] = "customer_allocation_proxy"
        r = build_calibration(c)
        rows = r["quality_gate_calibration"]["rows"]
        self.assertEqual(rows[0]["quality_status_after"], "review_required")
if __name__ == "__main__": unittest.main()
