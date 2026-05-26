import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase26_industry_forecast_source_routing import build_industry_forecast_routing


class Phase26IndustryForecastRoutingTests(unittest.TestCase):
    def test_planned_industry_forecast_is_not_active(self):
        payload = build_industry_forecast_routing("ai_optical_interconnect")
        routing = payload["industry_forecast_source_routing"]
        self.assertEqual(routing["active_sources"], [])
        self.assertTrue(routing["planned_sources"])
        self.assertFalse(routing["safety"]["planned_source_used_as_active_evidence"])


if __name__ == "__main__":
    unittest.main()
