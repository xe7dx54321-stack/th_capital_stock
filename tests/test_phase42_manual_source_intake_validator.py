import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "jobs", ROOT / "08_scripts" / "lib"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from validate_phase42_manual_source_intake import build_payload


class Phase42ManualSourceIntakeValidatorTests(unittest.TestCase):
    def test_official_consensus_authorized_sample_is_candidate_not_confirmed(self):
        payload = build_payload("official_consensus")
        result = payload["validation_result"]
        self.assertTrue(result["input_valid"])
        self.assertTrue(result["can_create_evidence_candidate"])
        self.assertFalse(result["can_be_confirmed"])
        self.assertEqual(result["pending_created"], 0)

    def test_official_consensus_internal_proxy_is_rejected(self):
        payload = build_payload("official_consensus_internal_proxy")
        result = payload["validation_result"]
        self.assertFalse(result["input_valid"])
        self.assertIn("official_consensus_requires_authorized_source", result["blocked_reasons"])

    def test_supplier_share_scenario_and_customer_proxy_are_not_confirmed(self):
        supplier = build_payload("supplier_share_scenario")["validation_result"]
        customer = build_payload("customer_allocation_proxy")["validation_result"]
        self.assertTrue(supplier["input_valid"])
        self.assertEqual(supplier["allowed_usage"], "scenario_analysis_only")
        self.assertFalse(supplier["can_be_confirmed"])
        self.assertTrue(customer["input_valid"])
        self.assertEqual(customer["allowed_usage"], "bear_case_context_or_scenario_support")
        self.assertFalse(customer["can_be_confirmed"])


if __name__ == "__main__":
    unittest.main()
