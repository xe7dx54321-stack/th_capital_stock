import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase42_manual_source_intake_template import build_payload


class Phase42ManualSourceIntakeTests(unittest.TestCase):
    def test_templates_are_format_only_and_evidence_type_specific(self):
        official = build_payload("300308.SZ", "official_consensus")
        supplier = build_payload("300308.SZ", "supplier_share")
        customer = build_payload("300308.SZ", "confirmed_customer_allocation")
        self.assertEqual(official["manual_source_intake_template"]["source_type"], "authorized_consensus_source")
        self.assertEqual(supplier["manual_source_intake_template"]["source_type"], "scenario_assumption")
        self.assertEqual(customer["manual_source_intake_template"]["source_type"], "proxy_evidence_note")
        self.assertFalse(official["safety"]["evidence_written"])
        self.assertEqual(official["manual_source_intake_template"]["quoted_span"], "")


if __name__ == "__main__":
    unittest.main()
