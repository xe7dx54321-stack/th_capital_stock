import phase54_helpers, unittest; from smr_bull_base_bear_frame import build_frame
class Phase54BBBTests(unittest.TestCase):
    def test_all_three(self):
        r=build_frame("300308.SZ"); f=r["bull_base_bear_frame"]
        self.assertGreater(len(f["bull_case"]),0)
        self.assertGreater(len(f["base_case"]),0)
        self.assertGreater(len(f["bear_case"]),0)
    def test_swing_factors(self):
        r=build_frame("300308.SZ"); f=r["bull_base_bear_frame"]
        self.assertGreater(len(f["key_swing_factors"]),0)
if __name__=="__main__": unittest.main()
