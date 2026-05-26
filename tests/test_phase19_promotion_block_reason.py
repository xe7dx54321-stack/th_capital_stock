import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_promotion_block_reason import classify_blocking_gates


class Phase19PromotionBlockReasonTests(unittest.TestCase):
    def test_core_empty_does_not_primary_core_gate(self):
        primary, secondary, warnings = classify_blocking_gates(
            row={
                "ticker": "300308.SZ",
                "status": "candidate_shadow",
                "primary_thesis_type": "ai_infrastructure_demand",
                "thesis_inference_confidence": 0.8,
                "core_blockers": [],
                "bear_case_gate": {"overall_status": "unresolved", "residual_risk_level": "high"},
            },
            phase6_row={},
            freshness={"filing_freshness": {"status": "fresh"}},
            evidence_quality={"evidence_quality_gate": {"status": "pass"}},
        )

        self.assertEqual(primary, "BEAR_CASE_GATE")
        self.assertNotEqual(primary, "CORE_EVIDENCE_GATE")
        self.assertEqual(len([primary]), 1)
        self.assertEqual(warnings, [])

    def test_unknown_thesis_beats_other_non_core_gates(self):
        primary, secondary, _warnings = classify_blocking_gates(
            row={
                "ticker": "002230.SZ",
                "status": "candidate_shadow",
                "primary_thesis_type": "unknown",
                "thesis_inference_confidence": 0.29,
                "core_blockers": [],
            },
            phase6_row={"missing_requirements": ["fresh_valuation_price"]},
            freshness={"filing_freshness": {"status": "stale"}},
            evidence_quality={"evidence_quality_gate": {"status": "blocked"}},
        )

        self.assertEqual(primary, "THESIS_CONFIDENCE_GATE")
        self.assertIn("FILING_FRESHNESS_GATE", secondary)
        self.assertIn("EVIDENCE_QUALITY_GATE", secondary)


if __name__ == "__main__":
    unittest.main()
