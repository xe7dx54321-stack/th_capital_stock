import sqlite3
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase23_demand_source_routing import build_ticker_payload


class Phase23DemandSourceRoutingTests(unittest.TestCase):
    def test_demand_blockers_route_confirmed_and_customer_capex_sources(self):
        confirmed = {
            "confirmed_demand_evidence": {
                "confirmed_order_count": 0,
                "tender_or_procurement_count": 0,
                "customer_capex_count": 0,
                "strong_or_medium_indication_count": 0,
            }
        }
        proxy = {
            "proxy_strengthening": {
                "after": {"independent_source_count": 1},
                "remaining_requirements": ["dominant_proxy_signal"],
            }
        }
        with patch("build_phase23_demand_source_routing.build_ticker_confirmed_demand", return_value=confirmed), patch(
            "build_phase23_demand_source_routing.build_ticker_proxy_strengthening",
            return_value=proxy,
        ):
            payload = build_ticker_payload(sqlite3.connect(":memory:"), "002230.SZ")
        self.assertIn("CONFIRMED_ORDER_EVIDENCE_MISSING", payload["demand_blockers"])
        self.assertIn("CUSTOMER_CAPEX_EVIDENCE_MISSING", payload["demand_blockers"])
        self.assertTrue(any(route["information_type"] == "customer_capex" for route in payload["source_routes"]))
        self.assertTrue(any(source["allowed_usage"] == "planned_only" for route in payload["source_routes"] for source in route["preferred_sources"]))


if __name__ == "__main__":
    unittest.main()
