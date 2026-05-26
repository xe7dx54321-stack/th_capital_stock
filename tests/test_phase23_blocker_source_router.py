import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_blocker_source_router import build_source_routes_for_blocker, map_blocker_to_information_types


class Phase23BlockerSourceRouterTests(unittest.TestCase):
    def test_forward_eps_proxy_only_maps_to_consensus_routes(self):
        information_types = map_blocker_to_information_types("FORWARD_EPS_PROXY_ONLY")
        self.assertIn("official_consensus", information_types)
        self.assertIn("internal_consensus_proxy", information_types)

    def test_unknown_blocker_returns_unknown_route(self):
        self.assertEqual(map_blocker_to_information_types("NO_SUCH_BLOCKER"), ["UNKNOWN_INFORMATION_ROUTE"])
        bundle = build_source_routes_for_blocker("NO_SUCH_BLOCKER", "TEST", "US")
        self.assertFalse(bundle["has_source_route"])

    def test_confirmed_order_routes_to_implemented_and_planned_sources(self):
        bundle = build_source_routes_for_blocker("CONFIRMED_ORDER_EVIDENCE_MISSING", "300308.SZ", "CN")
        routes = bundle["source_routes"]
        self.assertTrue(any(route["information_type"] == "confirmed_order" for route in routes))
        confirmed = next(route for route in routes if route["information_type"] == "confirmed_order")
        self.assertTrue(any(source["connector_id"] == "cninfo_filings" and source["status"] == "implemented" for source in confirmed["preferred_sources"]))
        self.assertTrue(any(source["status"] == "planned" for source in confirmed["preferred_sources"]))


if __name__ == "__main__":
    unittest.main()
