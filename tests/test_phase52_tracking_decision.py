import phase52_helpers
import unittest; from smr_tracking_decision_classifier import build_decision, classify_decision
class Phase52DecisionTests(unittest.TestCase):
    def test_continue_tracking(self):
        d=classify_decision(6,3); self.assertEqual(d["decision"],"continue_tracking")
    def test_forbidden_actions(self):
        d=build_decision("300308.SZ",6,3); td=d["tracking_decision"]
        self.assertIn("create_pending",td["forbidden_next_actions"])
    def test_no_buy(self):
        d=build_decision("300308.SZ",6,3); td=d["tracking_decision"]
        self.assertNotEqual(td["decision"],"buy")
    def test_request_more_text(self):
        d=classify_decision(0,3); self.assertEqual(d["decision"],"request_more_real_source_text")
if __name__=="__main__": unittest.main()
