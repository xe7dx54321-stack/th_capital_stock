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
from smr_source_connector_registry import get_routes_for_information_type, load_source_connector_registry


class Phase29ConnectorRegistryUpdateTests(unittest.TestCase):
    def test_phase29_connectors_are_partial_not_implemented(self):
        registry = load_source_connector_registry()
        for info_type in ("real_ir_document_text_extractor", "cninfo_pdf_text_extractor", "semantic_text_cache", "ir_section_splitter"):
            route = get_routes_for_information_type(info_type, "CN", registry=registry)
            self.assertEqual(route["route_status"], "partial")
            self.assertNotEqual(route["preferred_sources"][0]["status"], "implemented")
        dashboard = build_payload()
        self.assertFalse(dashboard["safety"]["real_ir_text_extractor_marked_implemented"])
        self.assertFalse(dashboard["safety"]["ocr_default_enabled"])


if __name__ == "__main__":
    unittest.main()
