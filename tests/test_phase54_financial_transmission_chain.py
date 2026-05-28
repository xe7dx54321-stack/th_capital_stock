import phase54_helpers, unittest; from smr_financial_transmission_chain import build_transmission_chain
class Phase54FinChainTests(unittest.TestCase):
    def test_chains(self):
        r=build_transmission_chain("300308.SZ"); tc=r["financial_transmission_chain"]
        self.assertGreater(len(tc["chains"]),2)
    def test_biz_to_fin(self):
        r=build_transmission_chain("300308.SZ"); tc=r["financial_transmission_chain"]
        for c in tc["chains"]:
            self.assertIn("business_driver",c); self.assertIn("financial_metric",c)
if __name__=="__main__": unittest.main()
