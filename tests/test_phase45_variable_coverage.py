import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from phase45_helpers import make_phase45_conn
from build_phase45_final_variable_coverage_review import build_payload


class Phase45VariableCoverageTests(unittest.TestCase):
    def test_variable_coverage_keeps_sensitive_variables_unconfirmed(self):
        body = build_payload(make_phase45_conn(), "300308.SZ")["final_variable_coverage_review"]
        supplier = body["variables_scenario_only"][0]
        customer = body["variables_proxy_only"][0]
        self.assertEqual(supplier["variable"], "supplier_share")
        self.assertEqual(supplier["status"], "scenario_only")
        self.assertEqual(customer["status"], "proxy_only")
        self.assertIn("official_consensus", body["variables_missing_or_unconfirmed"])
        self.assertEqual(body["confirmed_variables_added"], 0)


if __name__ == "__main__":
    unittest.main()
