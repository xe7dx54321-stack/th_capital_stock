import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_supply_chain_variable_evidence import make_variable_evidence, validate_variable_evidence


class Phase26SupplyChainVariableEvidenceTests(unittest.TestCase):
    def test_schema_caps_confidence_and_blocks_planned_scoring(self):
        item = make_variable_evidence(
            ticker="300394.SZ",
            theme="ai_optical_interconnect",
            variable_type="supplier_share",
            evidence_status="planned_only",
            confidence="high",
            allowed_usage="research_evidence",
            missing_reason="planned source only",
        )
        self.assertEqual(item["confidence"], "unknown")
        self.assertEqual(item["allowed_usage"], "planned_only")
        self.assertFalse(item["active_for_scoring"])
        self.assertEqual(validate_variable_evidence(item), [])

    def test_missing_requires_reason(self):
        item = make_variable_evidence(
            ticker="300394.SZ",
            theme="ai_optical_interconnect",
            variable_type="ASP_price_proxy",
            evidence_status="missing",
            confidence="unknown",
            allowed_usage="scenario_analysis_only",
        )
        self.assertTrue(any(issue["path"] == "missing_reason" for issue in validate_variable_evidence(item)))


if __name__ == "__main__":
    unittest.main()
