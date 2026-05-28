import phase54_helpers, unittest; from build_phase54_research_brief_quality_dashboard import build
class Phase54QDashboardTests(unittest.TestCase):
    def test_dashboard(self):
        r=build(None,"300308.SZ"); s=r["summary"]
        self.assertEqual(s["pending_created"],0)
        self.assertEqual(s["system_status_terms_found"],0)
    def test_depth_pass(self):
        r=build(None,"300308.SZ"); s=r["summary"]
        self.assertIn(s["depth_status"],["pass","warning"])
if __name__=="__main__": unittest.main()
