import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase42_supplier_share_scenario_registry import build_payload
from phase42_helpers import make_phase42_conn


class Phase42SupplierShareScenarioRegistryTests(unittest.TestCase):
    def test_supplier_share_scenario_is_not_confirmed(self):
        payload = build_payload(make_phase42_conn(), "300308.SZ")
        body = payload["supplier_share_scenario_registry"]
        scenario = body["scenarios"][0]
        self.assertEqual(body["scenario_count"], 1)
        self.assertEqual(scenario["allowed_usage"], "scenario_analysis_only")
        self.assertFalse(scenario["is_confirmed"])
        self.assertFalse(body["promotion_gate_eligible"])
        self.assertIn("do not treat as fact", scenario["caveats"])


if __name__ == "__main__":
    unittest.main()
