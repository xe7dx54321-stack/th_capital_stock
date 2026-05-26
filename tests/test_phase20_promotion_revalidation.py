import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
VERIFICATION_DIR = ROOT / "08_scripts" / "verification"
if str(VERIFICATION_DIR) not in sys.path:
    sys.path.insert(0, str(VERIFICATION_DIR))

from validate_phase20_promotion_revalidation import build_payload


class Phase20PromotionRevalidationTests(unittest.TestCase):
    def test_revalidation_reports_before_after_without_paper_order(self):
        with patch(
            "validate_phase20_promotion_revalidation.ticker_result",
            return_value={
                "ticker": "300308.SZ",
                "before_status": "candidate_shadow",
                "after_status": "candidate_shadow",
                "promotion_mode": None,
                "why_changed": ["bear_case_gate improved for at least one claim with linked evidence"],
                "why_no_pending": ["valuation gate remains blocked for 300308.SZ"],
                "new_pending_created": False,
                "requires_human_review": False,
                "paper_order_allowed": False,
            },
        ):
            payload = build_payload(None, ["300308.SZ"], watchlist="ai_core")

        self.assertEqual(payload["summary"]["gate_improvements"], 1)
        self.assertEqual(payload["summary"]["new_pending_created"], 0)
        self.assertFalse(payload["safety"]["paper_order_allowed"])


if __name__ == "__main__":
    unittest.main()
