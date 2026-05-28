import phase52_helpers
import unittest; from build_phase52_review_required_candidate_summary import build
class Phase52ReviewRequiredTests(unittest.TestCase):
    def test_review_count(self):
        r=build(None,"300308.SZ"); rr=r["review_required_candidate_summary"]
        self.assertGreaterEqual(rr["review_required_candidates"],1)
    def test_forbidden_actions(self):
        r=build(None,"300308.SZ"); rr=r["review_required_candidate_summary"]
        for row in rr["rows"]:
            self.assertIn("create_pending",row["forbidden_review_actions"])
            self.assertIn("create_order",row["forbidden_review_actions"])
if __name__=="__main__": unittest.main()
