import phase52_helpers
import unittest; from build_phase52_sensitive_variable_gap_summary import build
class Phase52SensitiveGapTests(unittest.TestCase):
    def test_gaps(self):
        r=build(None,"300308.SZ"); g=r["sensitive_variable_gap_summary"]
        self.assertGreaterEqual(len(g["pending_blocking_gaps"]),3)
        self.assertFalse(g["pending_allowed"])
    def test_gap_variables(self):
        r=build(None,"300308.SZ"); g=r["sensitive_variable_gap_summary"]
        vars=[gap["variable"] for gap in g["pending_blocking_gaps"]]
        for v in ["official_consensus","supplier_share","customer_allocation"]:
            self.assertIn(v,vars)
if __name__=="__main__": unittest.main()
