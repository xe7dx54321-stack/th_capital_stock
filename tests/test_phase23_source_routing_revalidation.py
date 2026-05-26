import sqlite3
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
VERIFICATION_DIR = ROOT / "08_scripts" / "verification"
for path in (LIB_DIR, VERIFICATION_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from validate_phase23_source_routing_revalidation import build_payload


class Phase23SourceRoutingRevalidationTests(unittest.TestCase):
    def test_revalidation_reports_route_coverage_without_pending(self):
        valuation = {
            "valuation_blockers": ["FORWARD_EPS_PROXY_ONLY"],
            "source_routes": [{"route_status": "planned_only"}],
            "next_actions": ["commercial consensus remains planned"],
        }
        demand = {
            "demand_blockers": ["CONFIRMED_ORDER_EVIDENCE_MISSING"],
            "source_routes": [{"route_status": "implemented"}],
            "next_actions": ["search implemented connector first"],
        }
        acquisition = {"repair_tasks": [{"repair_task_type": "CONFIRMED_ORDER_EVIDENCE_MISSING"}], "next_actions": ["search CNINFO first"]}
        with patch("validate_phase23_source_routing_revalidation.build_valuation_routing", return_value=valuation), patch(
            "validate_phase23_source_routing_revalidation.build_demand_routing",
            return_value=demand,
        ), patch("validate_phase23_source_routing_revalidation.build_acquisition_plan", return_value=acquisition):
            payload = build_payload(sqlite3.connect(":memory:"), ["TEST"], watchlist="ai_core")
        self.assertEqual(payload["overall_status"], "pass")
        self.assertEqual(payload["summary"]["blockers_without_source_routes"], 0)
        self.assertEqual(payload["summary"]["new_pending_created"], 0)


if __name__ == "__main__":
    unittest.main()
