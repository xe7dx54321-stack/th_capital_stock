import unittest; from phase50_helpers import make_phase50_conn; from build_phase50_candidate_quality_gate import build
class Phase50QualityGateTests(unittest.TestCase):
    def test_gate_reports(self): conn=make_phase50_conn(); p=build(conn,'300308.SZ'); g=p['candidate_quality_gate']; self.assertGreater(g['candidates_checked'],0)
    def test_no_promotion(self): conn=make_phase50_conn(); p=build(conn,'300308.SZ'); g=p['candidate_quality_gate']; self.assertEqual(g['usable_for_promotion_true'],0)
    def test_safety(self): conn=make_phase50_conn(); p=build(conn,'300308.SZ'); self.assertFalse(p['safety']['quality_gate_allows_promotion'])
if __name__=='__main__': unittest.main()
