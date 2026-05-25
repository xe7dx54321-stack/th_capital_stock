import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_decision import review_audit_detail_from_metadata


class Phase14ReviewAuditTests(unittest.TestCase):
    def test_reduced_size_pending_review_detail_exposes_audit_fields(self):
        detail = review_audit_detail_from_metadata(
            "phase14__09988.HK__valuation_rerating",
            {
                "ticker": "09988.HK",
                "promotion_mode": "reduced_size_pending",
                "position_policy": "reduced_size",
                "primary_thesis_type": "valuation_rerating",
                "optional_warnings": ["capex", "free_cash_flow"],
                "bear_case_gate": {
                    "overall_status": "partially_mitigated",
                    "residual_risk_level": "medium",
                    "action_effect": "reduce_position_size",
                },
                "candidate": {"suggested_position_pct": 0.75},
            },
            status="pending_human_review",
        )

        self.assertEqual(detail["promotion_mode"], "reduced_size_pending")
        self.assertEqual(detail["primary_thesis_type"], "valuation_rerating")
        self.assertEqual(detail["field_gate"]["optional_warnings"], ["capex", "free_cash_flow"])
        self.assertTrue(detail["requires_human_review"])
        self.assertFalse(detail["auto_approval_allowed"])
        self.assertFalse(detail["paper_order_allowed"])
        self.assertIn("reduced_size_only", detail["audit_flags"])


if __name__ == "__main__":
    unittest.main()
