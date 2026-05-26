import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
VERIFICATION_DIR = ROOT / "08_scripts" / "verification"
if str(VERIFICATION_DIR) not in sys.path:
    sys.path.insert(0, str(VERIFICATION_DIR))

from validate_phase22_valuation_demand_promotion_revalidation import build_payload


class Phase22PromotionRevalidationTests(unittest.TestCase):
    def test_revalidation_reports_before_after_without_auto_pending(self):
        with patch(
            "validate_phase22_valuation_demand_promotion_revalidation.ticker_result",
            side_effect=[
                {
                    "ticker": "300308.SZ",
                    "before_status": "candidate_shadow",
                    "after_status": "candidate_shadow",
                    "promotion_mode": None,
                    "valuation_after": "reduced_size_supporting",
                    "proxy_after": "strong",
                    "confirmed_order_count": 0,
                    "reduced_size_pending_eligible": True,
                    "why_changed": ["valuation gate upgraded from supporting/context to stronger diagnostic status"],
                    "why_no_pending": ["no automatic pending was created"],
                    "remaining_warnings": [],
                    "new_pending_created": False,
                    "requires_human_review": False,
                    "paper_order_allowed": False,
                }
            ],
        ):
            payload = build_payload(None, ["300308.SZ"], watchlist="ai_core")

        self.assertEqual(payload["summary"]["new_pending_created"], 0)
        self.assertEqual(payload["summary"]["full_size_pending_created"], 0)
        self.assertFalse(payload["safety"]["paper_order_allowed"])


if __name__ == "__main__":
    unittest.main()
