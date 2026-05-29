import unittest, sys; sys.path.insert(0,'08_scripts/lib'); sys.path.insert(0,'08_scripts/reporting'); from build_phase60_business_evidence_watchlist_review import build
class T(unittest.TestCase):
    def test_review(self): r=build(None,'300308.SZ'); d=r['business_evidence_watchlist_review']; self.assertIn('decision_reason',d)
    def test_no_pending(self): r=build(None,'300308.SZ'); d=r['business_evidence_watchlist_review']; self.assertEqual(d['pending_created'],0)
if __name__=='__main__': unittest.main()
