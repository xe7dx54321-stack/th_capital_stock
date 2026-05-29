import unittest,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
from smr_deep_evidence_claim_mapper import map_evidence_to_claims

class TestClaimMapper(unittest.TestCase):
    def setUp(self):
        self.rows=[{"evidence_id":"ev1","business_variable":"800G_product_signal","evidence_strength":"management_commentary","quoted_span":"...","limitation":"...","cannot_conclude":["800G revenue share"]},
                    {"evidence_id":"ev2","business_variable":"order_visibility_signal","evidence_strength":"management_commentary","quoted_span":"...","limitation":"...","cannot_conclude":["specific order amount"]},
                    {"evidence_id":"ev3","business_variable":"capacity_expansion_signal","evidence_strength":"financial_report_context","quoted_span":"...","limitation":"...","cannot_conclude":["capacity release schedule"]}]
        self.result=map_evidence_to_claims(self.rows)
    def test_claims_checked(self):
        self.assertGreater(self.result["claims_checked"],0)
    def test_unconfirmed_present(self):
        self.assertGreater(self.result["claims_unconfirmed"],0)
    def test_asp_not_auto_confirmed(self):
        for row in self.result["rows"]:
            if row["claim"]=="asp_trend_unconfirmed":
                self.assertEqual(row["claim_status"],"unconfirmed")
    def test_customer_share_unconfirmed(self):
        for row in self.result["rows"]:
            if "customer_share" in row["claim"]:
                self.assertEqual(row["claim_status"],"unconfirmed")
    def test_800G_supported_from_commentary(self):
        for row in self.result["rows"]:
            if row["claim"]=="800G_signal_supported":
                self.assertIn(row["claim_status"],["supported","partially_supported"])
    def test_evidence_gain_delta_present(self):
        self.assertIn("evidence_gain_delta",self.result)
    def test_claims_with_risk_signal_counted(self):
        self.assertIn("claims_with_risk_signal",self.result)

if __name__=="__main__":unittest.main()
