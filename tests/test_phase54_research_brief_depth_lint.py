import phase54_helpers, unittest
from smr_research_brief_depth_lint import lint_depth

class Phase54DepthLintTests(unittest.TestCase):
    def test_pass(self):
        text = '现有材料显示需求强劲。这说明行业景气。不能确认利润弹性。当前未取得客户份额。'
        r = lint_depth(text)
        self.assertEqual(r['depth_status'], 'pass')

    def test_system_terms_detected(self):
        r = lint_depth('pending candidate dashboard')
        self.assertGreater(r['system_status_terms_found'], 0)

    def test_no_thesis_fails(self):
        r = lint_depth('', has_thesis=False)
        self.assertNotEqual(r['depth_status'], 'pass')

    def test_observed_first_check_present(self):
        r = lint_depth('现有材料显示需求。这说明判断成立。')
        self.assertTrue(r['checks']['has_current_observations'])
        self.assertTrue(r['checks']['has_implications_from_observations'])

if __name__ == '__main__':
    unittest.main()
