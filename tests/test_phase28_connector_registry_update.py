import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase23_connector_availability_dashboard import build_payload
from smr_source_connector_registry import get_routes_for_information_type, load_source_connector_registry, validate_connector_registry


class Phase28ConnectorRegistryUpdateTests(unittest.TestCase):
    def test_registry_adds_semantic_connectors_without_virtual_implemented(self):
        registry = load_source_connector_registry()
        self.assertFalse(any(issue["severity"] == "error" for issue in validate_connector_registry(registry)))
        for info_type in ("company_ir_records", "cninfo_ir_records", "semantic_ir_extractor", "semantic_evidence_persistence"):
            route = get_routes_for_information_type(info_type, "CN", registry=registry)
            self.assertEqual(route["route_status"], "partial")
            primary = route["preferred_sources"][0]
            self.assertNotEqual(primary["status"], "implemented")
        dashboard = build_payload()
        self.assertFalse(dashboard["safety"]["semantic_ir_mock_marked_implemented"])


if __name__ == "__main__":
    unittest.main()
