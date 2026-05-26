import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase27_industry_forecast_evidence import render_markdown
from smr_industry_forecast_semantic_extractor import build_industry_forecast_evidence


class Phase27IndustryForecastExtractorTests(unittest.TestCase):
    def test_industry_forecast_has_quote_and_not_company_order(self):
        payload = build_industry_forecast_evidence("ai_optical_interconnect", mode="mock")
        row = payload["industry_forecast_evidence"][0]
        self.assertTrue(row["quoted_span"])
        self.assertEqual(row["allowed_usage"], "end_demand_proxy")
        self.assertIn("not company-specific", row["limitations"])
        self.assertIn("Phase 27 Industry Forecast Evidence", render_markdown(payload))


if __name__ == "__main__":
    unittest.main()
