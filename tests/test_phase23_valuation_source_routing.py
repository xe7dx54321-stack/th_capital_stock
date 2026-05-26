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

from build_phase23_valuation_source_routing import build_ticker_payload


class Phase23ValuationSourceRoutingTests(unittest.TestCase):
    def test_forward_eps_blocker_routes_official_consensus_as_planned(self):
        with patch(
            "build_phase23_valuation_source_routing.diagnose_valuation_gate_v2",
            return_value={"valuation_gate_v2": {"after_status": "blocked", "remaining_blockers": ["FORWARD_EPS_PROXY_ONLY"]}},
        ):
            payload = build_ticker_payload(sqlite3.connect(":memory:"), "300308.SZ")
        official = next(route for route in payload["source_routes"] if route["information_type"] == "official_consensus")
        self.assertEqual(official["route_status"], "planned_only")
        self.assertTrue(any(source["connector_id"] == "internal_consensus_proxy" for source in official["fallback_sources"]))
        self.assertIn("never label it official consensus", official["next_action"])


if __name__ == "__main__":
    unittest.main()
