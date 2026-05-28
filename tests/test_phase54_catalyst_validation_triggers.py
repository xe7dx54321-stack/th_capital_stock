import phase54_helpers, unittest; from smr_catalyst_validation_trigger import build_triggers
class Phase54CatalystTests(unittest.TestCase):
    def test_both_directions(self):
        r=build_triggers("300308.SZ"); ct=r["catalyst_validation_triggers"]
        self.assertGreater(len(ct["strengthening_triggers"]),0)
        self.assertGreater(len(ct["weakening_triggers"]),0)
    def test_forbidden_actions(self):
        r=build_triggers("300308.SZ"); ct=r["catalyst_validation_triggers"]
        self.assertIn("create_order",ct["forbidden_actions"])
if __name__=="__main__": unittest.main()
