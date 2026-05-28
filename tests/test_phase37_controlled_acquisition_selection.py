import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase37_controlled_acquisition_selection import build_payload, render_markdown
from phase37_helpers import make_phase37_conn


class Phase37ControlledAcquisitionSelectionTests(unittest.TestCase):
    def test_selects_small_sample_without_confirmed_sensitive_paths(self):
        payload = build_payload(make_phase37_conn(), ticker="300308.SZ")
        body = payload["controlled_acquisition_selection"]
        selected = body["selected_tasks"]
        variables = {task["variable"] for task in selected}
        self.assertGreaterEqual(len(selected), 3)
        self.assertLessEqual(len(selected), 5)
        self.assertIn("ASP_price_proxy", variables)
        self.assertTrue({"shipment", "order_visibility"} & variables)
        self.assertTrue({"customer_allocation_proxy", "industry_forecast"} & variables)
        self.assertNotIn("supplier_share", variables)
        self.assertFalse(payload["safety"]["official_consensus_impersonated"])
        self.assertIn("Phase 37 Controlled Acquisition Selection", render_markdown(payload))


if __name__ == "__main__":
    unittest.main()
