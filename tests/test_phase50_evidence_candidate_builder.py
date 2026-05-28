import unittest; from phase50_helpers import make_phase50_conn; from build_phase50_real_source_evidence_candidates import build
class Phase50CandidateTests(unittest.TestCase):
    def test_candidates(self): conn=make_phase50_conn(); p=build(conn,'300308.SZ'); c=p['real_source_evidence_candidate_build']; self.assertGreater(c['candidates_created'],0)
    def test_not_confirmed(self): conn=make_phase50_conn(); p=build(conn,'300308.SZ'); c=p['real_source_evidence_candidate_build']; self.assertEqual(c['confirmed_variables_added'],0); self.assertEqual(c['usable_for_promotion_true'],0)
    def test_no_pending(self): conn=make_phase50_conn(); p=build(conn,'300308.SZ'); self.assertEqual(p['real_source_evidence_candidate_build']['pending_created'],0)
if __name__=='__main__': unittest.main()
