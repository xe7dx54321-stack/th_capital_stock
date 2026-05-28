import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase36_targeted_evidence_gap import build_payload, render_markdown
from phase34_helpers import make_phase34_conn


class Phase36TargetedEvidenceGapTests(unittest.TestCase):
    def test_300308_critical_gaps_are_explicit_and_safe(self):
        payload = build_payload(make_phase34_conn(), ticker="300308.SZ")
        body = payload["targeted_evidence_gap"]
        critical = {row["variable"]: row for row in body["critical_missing_variables"]}
        self.assertGreaterEqual(len(critical), 6)
        for variable in (
            "supplier_share",
            "ASP_price_proxy",
            "customer_allocation_proxy",
            "official_consensus",
            "shipment",
            "order_visibility",
            "industry_forecast",
        ):
            self.assertIn(variable, critical)
            self.assertTrue(critical[variable]["why_it_matters"])
        self.assertFalse(critical["supplier_share"]["can_be_confirmed_from_public_sources"])
        self.assertFalse(critical["customer_allocation_proxy"]["confirmed_after_plan"])
        self.assertEqual(payload["safety"]["new_pending_created"], 0)
        self.assertIn("Phase 36 Targeted Evidence Gap", render_markdown(payload))


if __name__ == "__main__":
    unittest.main()
