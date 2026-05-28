import phase53_helpers, unittest; from build_phase53_brief_dashboard import build
class Phase53DashboardTests(unittest.TestCase):
    def test_dashboard(self):
        r=build(None,"300308.SZ"); s=r["summary"]
        self.assertEqual(s["pending_created"],0)
        self.assertEqual(s["paper_order_created"],0)
    def test_style_pass(self):
        r=build(None,"300308.SZ"); s=r["summary"]
        self.assertIn(s["style_status"],["pass","pass_with_warnings"])
if __name__=="__main__": unittest.main()
