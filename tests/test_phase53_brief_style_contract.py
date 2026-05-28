import phase53_helpers, unittest; from smr_brief_style_contract import build_contract, load_rules
class Phase53ContractTests(unittest.TestCase):
    def test_not_sell_side(self):
        c=build_contract(); r=c.get("note","")
        self.assertIn("NOT",r.upper())
    def test_contract_type(self):
        c=build_contract(); ct=c.get("brief_style_contract",{})
        self.assertEqual(ct.get("brief_type"),"internal_watchlist_tracking_brief")
    def test_rules_load(self):
        r=load_rules(); self.assertIn("brief_type",r)
if __name__=="__main__": unittest.main()
