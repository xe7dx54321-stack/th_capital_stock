import unittest

import phase46_helpers  # noqa: F401
from build_phase46_tracking_variables import build_payload


class Phase46TrackingVariablesTests(unittest.TestCase):
    def test_tracking_variables_cover_key_variables(self):
        payload = build_payload("300308.SZ")
        rows = payload["tracking_variables"]
        variables = {row["variable"]: row for row in rows}
        self.assertGreaterEqual(len(rows), 10)
        for variable in (
            "product_mix",
            "order_visibility",
            "shipment",
            "ASP_price_proxy",
            "supplier_share_scenario",
            "official_consensus_status",
            "customer_allocation_proxy",
            "bear_case_residual_risk",
            "valuation_boundary",
            "evidence_quality",
            "thesis_strength",
        ):
            self.assertIn(variable, variables)
            self.assertTrue(variables[variable]["strengthening_signal"])
            self.assertTrue(variables[variable]["weakening_signal"])
        self.assertEqual(variables["supplier_share_scenario"]["current_status"], "scenario_only")
        self.assertEqual(variables["official_consensus_status"]["current_status"], "unconfirmed")
        self.assertEqual(variables["customer_allocation_proxy"]["current_status"], "proxy_only")
        self.assertEqual(payload["safety"]["pending_created"], 0)


if __name__ == "__main__":
    unittest.main()
