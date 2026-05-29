import unittest,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
from smr_cninfo_targeted_disclosure_category_planner import load_category_plan,get_priority_order

class TestCategoryPlan(unittest.TestCase):
    def test_load_plan_has_categories(self):
        plan=load_category_plan()
        cats=plan.get("priority_categories",[])
        self.assertGreater(len(cats),0,"should have at least one category")
    def test_p0_categories_exist(self):
        order=get_priority_order()
        p0=[c for c in order if c.get("priority")=="P0"]
        self.assertGreater(len(p0),0,"should have P0 categories")
    def test_each_category_has_max_sources(self):
        plan=load_category_plan()
        for c in plan.get("priority_categories",[]):
            self.assertIn("max_sources",c)
            self.assertGreater(c["max_sources"],0)
    def test_plan_has_business_variables(self):
        plan=load_category_plan()
        self.assertIn("business_variables",plan)
    def test_priority_order_sorted(self):
        order=get_priority_order()
        priorities={"P0":1,"P1":2,"P2":3}
        prev=0
        for c in order:
            curr=priorities.get(c.get("priority",""),99)
            self.assertGreaterEqual(curr,prev)
            prev=curr

if __name__=="__main__":unittest.main()
