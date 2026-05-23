import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
VERIFICATION_DIR = ROOT / "08_scripts" / "verification"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
if str(VERIFICATION_DIR) not in sys.path:
    sys.path.insert(0, str(VERIFICATION_DIR))

from validate_phase8_ah_candidate_recovery import build_payload


class Phase8AhCandidateRecoveryTests(unittest.TestCase):
    def test_recovery_payload_outputs_field_level_gap_and_blockers(self):
        phase6_payload = {
            "run_id": "run-09988",
            "summary": {"overall_result": "live_data_available_needs_promotion_work"},
            "tickers": [
                {
                    "ticker": "09988.HK",
                    "status": "candidate_shadow",
                    "action": "watch",
                    "promotion_allowed": False,
                    "live_news_evidence": 2,
                    "live_filing_evidence": 1,
                    "proxy_quality": "invalid",
                    "valuation_usage": "context_only",
                    "blocking_factors": [
                        {
                            "code": "FUNDAMENTALS_MISSING_FIELDS",
                            "affected_fields": ["gross_profit", "capex"],
                            "suggested_fix": "extend HKEX field map",
                        }
                    ],
                }
            ],
        }
        snapshot = {
            "ticker": "09988.HK",
            "freshness_status": "degraded",
            "field_details": {
                "revenue": {"extracted_value": 100.0, "unit": "million HKD", "currency": "HKD", "source_evidence_id": "ev-rev", "confidence": 0.82},
                "net_income": {"extracted_value": 20.0, "unit": "million HKD", "currency": "HKD", "source_evidence_id": "ev-ni", "confidence": 0.8},
                "gross_profit": {"extracted_value": None, "missing_reason": "mapping_missing"},
                "capex": {"extracted_value": None, "missing_reason": "field_not_found"},
            },
            "field_missing_reasons": {"gross_profit": "mapping_missing", "capex": "field_not_found"},
        }

        payload = build_payload(ticker="09988.HK", phase6_payload=phase6_payload, fundamentals_snapshot=snapshot)

        self.assertEqual(payload["current_status"], "candidate_shadow")
        self.assertEqual(payload["field_extraction"]["revenue"]["status"], "extracted")
        self.assertEqual(payload["field_extraction"]["gross_profit"]["missing_reason"], "mapping_missing")
        self.assertTrue(payload["blocking_factors"])
        self.assertTrue(payload["minimum_fix_path"])


if __name__ == "__main__":
    unittest.main()
