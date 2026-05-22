import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_recommendation_candidate import build_recommendation_candidate


class RecommendationCandidateTests(unittest.TestCase):
    def test_candidate_builder_caps_context_only_valuation(self):
        candidate = build_recommendation_candidate(
            recommendation_id="rec-context-only",
            ticker="NVDA",
            valuation_snapshot={"allowed_usage": "context_only"},
            consensus_proxy={"proxy_quality": "strong", "usable_for_promotion": True},
            bear_case={"bear_case_strength": "medium", "deal_breakers": ["break"]},
            risk_snapshot={"status": "pass"},
            market_signal={"signal": "positive"},
            promotion_result={"allowed": True, "to_status": "pending_human_review"},
        )

        self.assertEqual(candidate["action"], "watch")
        self.assertEqual(candidate["status"], "candidate_shadow")

    def test_candidate_builder_outputs_pending_review_only_after_promotion(self):
        candidate = build_recommendation_candidate(
            recommendation_id="rec-eligible",
            ticker="NVDA",
            valuation_snapshot={"allowed_usage": "promotion_eligible"},
            consensus_proxy={"proxy_quality": "strong", "usable_for_promotion": True},
            bear_case={"bear_case_strength": "medium", "deal_breakers": ["Primary evidence breaks thesis"]},
            risk_snapshot={"status": "pass"},
            market_signal={"signal": "positive"},
            promotion_result={"allowed": True, "to_status": "pending_human_review"},
        )

        self.assertEqual(candidate["action"], "buy_candidate")
        self.assertEqual(candidate["status"], "pending_human_review")
        self.assertIn("Primary evidence breaks thesis", candidate["kill_conditions"])

    def test_portfolio_risk_downsizes_candidate(self):
        candidate = build_recommendation_candidate(
            recommendation_id="rec-risk-downsize",
            ticker="NVDA",
            valuation_snapshot={"allowed_usage": "promotion_eligible"},
            consensus_proxy={"proxy_quality": "strong", "usable_for_promotion": True},
            bear_case={"bear_case_strength": "medium", "deal_breakers": ["Risk breaks thesis"]},
            risk_snapshot={"status": "pass"},
            portfolio_risk={
                "status": "warn",
                "recommended_action": "downsize",
                "recommended_position_pct": 0.75,
                "recommended_max_position_pct": 1.0,
            },
            market_signal={"signal": "positive"},
            promotion_result={"allowed": True, "to_status": "pending_human_review"},
        )

        self.assertEqual(candidate["action"], "small_candidate")
        self.assertEqual(candidate["status"], "pending_human_review")
        self.assertEqual(candidate["suggested_position_pct"], 0.75)
        self.assertEqual(candidate["max_position_pct"], 1.0)
        self.assertIn("portfolio_risk_downsizes_candidate", candidate["reasons"])

    def test_portfolio_risk_blocks_candidate(self):
        candidate = build_recommendation_candidate(
            recommendation_id="rec-risk-block",
            ticker="NVDA",
            valuation_snapshot={"allowed_usage": "promotion_eligible"},
            consensus_proxy={"proxy_quality": "strong", "usable_for_promotion": True},
            bear_case={"bear_case_strength": "medium", "deal_breakers": ["Risk breaks thesis"]},
            risk_snapshot={"status": "pass"},
            portfolio_risk={
                "status": "block",
                "recommended_action": "degrade",
                "blocking_factors": [{"code": "THEME_EXPOSURE", "detail": "theme is full"}],
            },
            market_signal={"signal": "positive"},
            promotion_result={"allowed": True, "to_status": "pending_human_review"},
        )

        self.assertEqual(candidate["action"], "observation")
        self.assertEqual(candidate["status"], "observation_only")
        self.assertEqual(candidate["suggested_position_pct"], 0.0)
        self.assertIn("portfolio_risk_blocked", candidate["reasons"])


if __name__ == "__main__":
    unittest.main()
