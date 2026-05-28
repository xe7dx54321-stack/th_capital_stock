import phase54_helpers, unittest; from smr_investment_logic_brief_builder import build_investment_logic_brief
class Phase54LogicBriefTests(unittest.TestCase):
    def test_all_sections(self):
        r=build_investment_logic_brief("300308.SZ"); ib=r["investment_logic_brief"]
        for k in ["one_line_conclusion","core_value_judgment","key_business_drivers","evidence_and_data","market_expectation_gap","bull_base_bear","validation_triggers","current_action","quality","boundary"]:
            self.assertIn(k,ib)
    def test_no_system_terms(self):
        r=build_investment_logic_brief("300308.SZ")
        ib=r["investment_logic_brief"]
        user_parts=[ib.get("one_line_conclusion",""), str(ib.get("core_value_judgment",{})), str(ib.get("current_action",{}))]
        s=" ".join(user_parts).lower()
        for t in ["candidate","tracking-support","validator","dashboard","quality gate"]:
            self.assertNotIn(t,s)
    def test_no_trading(self):
        r=build_investment_logic_brief("300308.SZ")
        ib=r["investment_logic_brief"]
        s=str(ib.get("one_line_conclusion",""))+" "+str(ib.get("current_action",{}))
        self.assertNotIn("buy",s.lower()); self.assertNotIn("sell",s.lower())
    def test_boundary_zero(self):
        r=build_investment_logic_brief("300308.SZ"); b=r["investment_logic_brief"]["boundary"]
        for k in ["pending_created","paper_order_created","real_trade_created"]:
            self.assertEqual(b[k],0)
if __name__=="__main__": unittest.main()
