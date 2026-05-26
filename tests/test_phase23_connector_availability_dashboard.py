import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase23_connector_availability_dashboard import build_payload, render_markdown


class Phase23ConnectorAvailabilityDashboardTests(unittest.TestCase):
    def test_dashboard_outputs_json_and_markdown(self):
        payload = build_payload()
        markdown = render_markdown(payload)
        self.assertIn("implemented_connectors", payload["summary"])
        self.assertIn("# Phase 23 Connector Availability Dashboard", markdown)
        official = next(row for row in payload["by_information_type"] if row["information_type"] == "official_consensus")
        self.assertEqual(official["CN"]["status"], "planned")


if __name__ == "__main__":
    unittest.main()
