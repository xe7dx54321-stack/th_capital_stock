import phase54_helpers, unittest; from smr_investment_thesis_quality_checker import check_thesis_quality, build_report
class Phase54ThesisQualityTests(unittest.TestCase):
    def test_pass(self):
        r=check_thesis_quality("核心价值在于高端产品放量带来毛利率弹性")
        self.assertIn(r["overall_status"],["pass","warning"])
    def test_weak_tracking_fails(self):
        r=check_thesis_quality("继续跟踪")
        self.assertNotEqual(r["overall_status"],"pass")
    def test_report(self):
        r=build_report("测试thesis","300308.SZ")
        self.assertIn("investment_thesis_quality",r)
if __name__=="__main__": unittest.main()
