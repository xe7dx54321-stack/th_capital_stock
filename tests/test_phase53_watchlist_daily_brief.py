import phase53_helpers, unittest, json
from build_phase53_watchlist_daily_brief import build, _md
class Phase53DailyBriefTests(unittest.TestCase):
    def test_brief_keys(self):
        r=build(None,"300308.SZ"); db=r["watchlist_daily_brief"]
        for k in ["executive_brief","analyst_detail","style_lint","forbidden_phrase_report","boundary"]:
            self.assertIn(k,db)
    def test_boundary_zero(self):
        r=build(None,"300308.SZ"); b=r["watchlist_daily_brief"]["boundary"]
        for k in ["pending_created","paper_order_created","real_trade_created"]:
            self.assertEqual(b[k],0)
    def test_markdown(self):
        r=build(None,"300308.SZ"); md=_md(r)
        self.assertIn("内部投研跟踪简报",md)
        self.assertIn("研究员详情",md)
        self.assertIn("边界",md)
    def test_no_target_price(self):
        r=build(None,"300308.SZ"); md=_md(r)
        self.assertNotIn("目标价",md)
    def test_no_buy(self):
        r=build(None,"300308.SZ"); md=_md(r)
        self.assertNotIn("建议买入",md)
if __name__=="__main__": unittest.main()
