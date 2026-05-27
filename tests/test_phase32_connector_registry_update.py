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
from smr_source_connector_registry import load_source_connector_registry, validate_connector_registry


class Phase32ConnectorRegistryUpdateTests(unittest.TestCase):
    def test_phase32_connectors_are_partial_not_implemented(self):
        registry = load_source_connector_registry()
        self.assertFalse(any(issue["severity"] == "error" for issue in validate_connector_registry(registry)))
        info = registry.get("information_types") or {}
        for key in [
            "evidence_review_workbench",
            "priority_review_packet",
            "evidence_review_html_dashboard",
            "batch_review_dry_run",
            "download_repair_workbench",
        ]:
            source = info[key]["markets"]["GLOBAL"]["preferred_sources"][0]
            self.assertEqual(source["status"], "partial")
            self.assertNotEqual(source["status"], "implemented")
        dashboard = build_payload()
        self.assertFalse(dashboard["safety"]["phase32_workbench_marked_implemented"])
        self.assertFalse(dashboard["safety"]["phase32_workbench_executes_actions"])


if __name__ == "__main__":
    unittest.main()
