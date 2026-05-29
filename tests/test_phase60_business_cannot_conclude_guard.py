import unittest, sys; sys.path.insert(0,'08_scripts/lib'); from smr_business_cannot_conclude_guard import check_business_cannot_conclude, build_business_guard_report, BUSINESS_FORBIDDEN
class T(unittest.TestCase):
    def test_detects(self): v=check_business_cannot_conclude(BUSINESS_FORBIDDEN); self.assertGreater(len(v),0)
    def test_guard(self): r=build_business_guard_report(); self.assertEqual(r['business_cannot_conclude_guard']['guard_status'],'pass')
    def test_block_800g(self): v=check_business_cannot_conclude(['800G提及=800G收入占比确认']); self.assertGreater(len(v),0)
if __name__=='__main__': unittest.main()
