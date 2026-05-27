import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
for path in (LIB_DIR,):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from smr_source_connector_registry import load_source_connector_registry


class Phase30ConnectorRegistryUpdateTests(unittest.TestCase):
    def test_phase30_connectors_are_partial_not_implemented(self):
        registry = load_source_connector_registry()
        info = registry.get("information_types") or {}
        for key in [
            "semantic_evidence_quality_scorer",
            "semantic_evidence_noise_filter",
            "semantic_evidence_persistence_guard",
            "semantic_evidence_post_persistence_audit",
        ]:
            source = info[key]["markets"]["GLOBAL"]["preferred_sources"][0]
            self.assertEqual(source["status"], "partial")
            self.assertNotEqual(source["status"], "implemented")


if __name__ == "__main__":
    unittest.main()
