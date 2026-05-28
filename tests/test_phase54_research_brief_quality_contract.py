import phase54_helpers, unittest; from smr_research_brief_quality_contract import build_contract, load_rules
class Phase54ContractTests(unittest.TestCase):
    def test_contract_type(self):
        c=build_contract(); ct=c.get("research_brief_quality_contract",{})
        self.assertEqual(ct.get("brief_type"),"internal_equity_research_logic_brief")
    def test_required_questions(self):
        c=build_contract(); ct=c.get("research_brief_quality_contract",{})
        self.assertGreater(len(ct.get("required_business_questions",[])),3)
    def test_rules_load(self):
        r=load_rules(); self.assertIn("brief_type",r)
if __name__=="__main__": unittest.main()
