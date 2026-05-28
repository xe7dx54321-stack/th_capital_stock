import phase52_helpers
import unittest; from build_phase52_tracking_support_evidence_summary import build
class Phase52TrackingEvidenceTests(unittest.TestCase):
    def test_output(self):
        r=build(None,"300308.SZ"); ts=r["tracking_support_evidence_summary"]
        self.assertGreaterEqual(ts["tracking_support_candidates"],1)
    def test_not_confirmed(self):
        r=build(None,"300308.SZ"); ts=r["tracking_support_evidence_summary"]
        for v in ts.get("supported_variables",[]):
            self.assertEqual(v["support_level"],"tracking_support")
if __name__=="__main__": unittest.main()
