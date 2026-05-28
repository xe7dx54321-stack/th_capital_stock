import phase54_helpers, unittest; from smr_research_brief_depth_lint import lint_depth
class Phase54DepthLintTests(unittest.TestCase):
    def test_pass(self):
        r=lint_depth("核心价值判断关于光模块"); self.assertEqual(r["depth_status"],"pass")
    def test_system_terms_detected(self):
        r=lint_depth("pending candidate dashboard"); self.assertGreater(r["system_status_terms_found"],0)
    def test_no_thesis_fails(self):
        r=lint_depth("",has_thesis=False)
        self.assertNotEqual(r["depth_status"],"pass")
if __name__=="__main__": unittest.main()
