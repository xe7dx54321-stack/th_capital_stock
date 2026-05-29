import unittest, sys; sys.path.insert(0,'08_scripts/lib'); sys.path.insert(0,'08_scripts/reporting'); from build_phase60_business_evidence_brief import build
class T(unittest.TestCase):
    def test_brief(self): r=build(None,'300308.SZ'); d=r['business_evidence_brief']; self.assertGreater(len(d['what_we_see']),0)
    def test_no_backend(self):
        r=build(None,'300308.SZ'); text=str(r).lower()
        for t in ['candidate','pending_human','validator','quality gate','下一步重点','建议关注']: self.assertNotIn(t,text)
    def test_no_trade(self): r=build(None,'300308.SZ'); d=r['business_evidence_brief']; self.assertEqual(d['pending_created'],0)
if __name__=='__main__': unittest.main()
