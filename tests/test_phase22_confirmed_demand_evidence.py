import sqlite3
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
LIB_DIR = ROOT / "08_scripts" / "lib"
for path in (REPORTING_DIR, LIB_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase22_confirmed_demand_evidence import build_ticker_confirmed_demand


class Phase22ConfirmedDemandEvidenceTests(unittest.TestCase):
    def test_customer_capex_is_not_confirmed_order(self):
        with patch(
            "build_phase22_confirmed_demand_evidence.extract_direct_demand_evidence",
            return_value=[
                {
                    "evidence_id": "ev_capex",
                    "evidence_category": "customer_capex",
                    "demand_strength": "strong_indication",
                    "source_quality": "high",
                    "demand_direction": "positive",
                    "usable_for_proxy_signal": True,
                    "usable_for_bear_case_mitigation": True,
                    "independent_source_key": "capex_news_1",
                    "limitations": ["customer-side capex, not company-specific order"],
                }
            ],
        ):
            payload = build_ticker_confirmed_demand(sqlite3.connect(":memory:"), "TEST.SZ")

        summary = payload["confirmed_demand_evidence"]
        self.assertEqual(summary["confirmed_order_count"], 0)
        self.assertEqual(summary["customer_capex_count"], 1)
        self.assertIn("no company-specific signed order", summary["no_confirmed_order_reason"])


if __name__ == "__main__":
    unittest.main()
