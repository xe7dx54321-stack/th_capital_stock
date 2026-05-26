import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
VERIFICATION_DIR = ROOT / "08_scripts" / "verification"
if str(VERIFICATION_DIR) not in sys.path:
    sys.path.insert(0, str(VERIFICATION_DIR))

from validate_phase21_promotion_revalidation import build_payload


class Phase21PromotionRevalidationTests(unittest.TestCase):
    def test_revalidation_reports_before_after_without_creating_paper_order(self):
        with patch(
            "validate_phase21_promotion_revalidation.ticker_result",
            return_value={
                "ticker": "688041.SH",
                "before_status": "candidate_shadow",
                "after_status": "candidate_shadow",
                "promotion_mode": None,
                "direct_demand_evidence_count": 2,
                "why_changed": ["direct demand evidence added", "proxy sources expanded with independent demand evidence"],
                "why_no_pending": ["valuation gate remains supporting only"],
                "new_pending_created": False,
                "requires_human_review": False,
                "paper_order_allowed": False,
            },
        ):
            payload = build_payload(None, ["688041.SH"], watchlist="ai_core")

        self.assertEqual(payload["summary"]["new_pending_created"], 0)
        self.assertEqual(payload["summary"]["full_size_pending_created"], 0)
        self.assertFalse(payload["safety"]["paper_order_allowed"])
        self.assertFalse(payload["safety"]["promotion_rules_relaxed"])


if __name__ == "__main__":
    unittest.main()
