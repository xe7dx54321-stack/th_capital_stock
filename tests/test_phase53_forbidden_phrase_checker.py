import phase53_helpers, unittest; from smr_brief_forbidden_phrase_checker import check_phrases, build_report
class Phase53ForbiddenTests(unittest.TestCase):
    def test_blocks_buy(self):
        r=check_phrases("建议买入"); self.assertGreater(len(r["violations"]),0)
    def test_warns_fluff(self):
        r=check_phrases("有望受益"); self.assertGreater(len(r["warnings"]),0)
    def test_clean_pass(self):
        r=check_phrases("继续跟踪，thesis正向"); self.assertEqual(len(r["violations"]),0)
    def test_report(self):
        r=build_report({"test":"继续跟踪"}, "300308.SZ"); fpr=r.get("forbidden_phrase_report",{})
        self.assertIn(fpr.get("style_status",""),["pass","pass_with_warnings"])
if __name__=="__main__": unittest.main()
