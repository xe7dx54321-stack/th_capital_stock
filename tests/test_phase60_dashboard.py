import unittest, sys; sys.path.insert(0,'08_scripts/lib'); sys.path.insert(0,'08_scripts/reporting'); from build_phase60_business_evidence_dashboard import build
class T(unittest.TestCase):
    def test_dash(self): r=build(None); d=r['summary']; self.assertGreater(d['business_variables_defined'],0)
    def test_pending_zero(self): r=build(None); self.assertEqual(r['summary']['pending_created'],0)
if __name__=='__main__': unittest.main()
