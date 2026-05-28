import phase53_helpers, unittest; from smr_analyst_detail_brief_builder import build_analyst_detail
class Phase53AnalystDetailTests(unittest.TestCase):
    def test_has_sections(self):
        r=build_analyst_detail("300308.SZ"); ad=r["analyst_detail"]
        for k in ["supported_variables","unconfirmed_variables","review_required","next_events","boundary"]:
            self.assertIn(k,ad)
    def test_boundary_content(self):
        r=build_analyst_detail("300308.SZ"); ad=r["analyst_detail"]
        self.assertIn("tracking_decision",ad)
if __name__=="__main__": unittest.main()
