import phase53_helpers, unittest; from smr_brief_style_lint import lint_brief
class Phase53LintTests(unittest.TestCase):
    def test_pass(self):
        r=lint_brief("继续跟踪",True,True,True,True,True)
        self.assertEqual(r["style_status"],"pass")
    def test_no_conclusion_fail(self):
        r=lint_brief("text",False,True,True,True,True)
        self.assertNotEqual(r["style_status"],"pass")
    def test_target_price_detected(self):
        r=lint_brief("目标价 100",True,True,True,True,True)
        self.assertTrue(r["checks"]["target_price_detected"])
if __name__=="__main__": unittest.main()
