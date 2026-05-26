import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_source_connector_registry import (
    get_routes_for_information_type,
    load_source_connector_registry,
    route_source_is_usable,
    summarize_connector_availability,
    validate_connector_registry,
)


class Phase23SourceConnectorRegistryTests(unittest.TestCase):
    def test_registry_loads_and_validates(self):
        registry = load_source_connector_registry()
        self.assertEqual(registry["version"], 2)
        self.assertFalse(validate_connector_registry(registry))
        for information_type in ("financial_statement", "confirmed_order", "official_consensus", "peer_valuation"):
            self.assertIn(information_type, registry["information_types"])

    def test_official_consensus_is_planned_only(self):
        route = get_routes_for_information_type("official_consensus", "CN")
        self.assertEqual(route["route_status"], "planned_only")
        primary = route["preferred_sources"][0]
        self.assertEqual(primary["status"], "planned")
        self.assertEqual(primary["allowed_usage"], "planned_only")
        self.assertFalse(route_source_is_usable(primary))

    def test_dashboard_summary_keeps_official_consensus_planned(self):
        summary = summarize_connector_availability(load_source_connector_registry())
        official = next(row for row in summary["by_information_type"] if row["information_type"] == "official_consensus")
        self.assertEqual(official["current_usage"], "planned_only")


if __name__ == "__main__":
    unittest.main()
