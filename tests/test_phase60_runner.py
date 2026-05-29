import unittest, sys; sys.path.insert(0,'08_scripts/lib'); sys.path.insert(0,'08_scripts/jobs'); from run_phase60_business_evidence_integration import run_loop
class T(unittest.TestCase):
    def test_dry(self): r=run_loop('300308.SZ','dry-run'); self.assertEqual(r['phase60_business_evidence_integration']['mode'],'dry-run')
    def test_pending_zero(self): r=run_loop('300308.SZ','dry-run'); self.assertEqual(r['phase60_business_evidence_integration']['pending_created'],0)
if __name__=='__main__': unittest.main()
