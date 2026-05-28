import phase54_helpers, unittest; from smr_business_driver_tree import build_driver_tree
class Phase54DriverTreeTests(unittest.TestCase):
    def test_has_layers(self):
        r=build_driver_tree("300308.SZ"); t=r["business_driver_tree"]
        for k in ["root_driver","industry_drivers","company_drivers","financial_outputs"]:
            self.assertIn(k,t)
    def test_from_industry_to_company(self):
        r=build_driver_tree("300308.SZ"); t=r["business_driver_tree"]
        self.assertGreater(len(t["industry_drivers"]),0)
        self.assertGreater(len(t["company_drivers"]),0)
if __name__=="__main__": unittest.main()
