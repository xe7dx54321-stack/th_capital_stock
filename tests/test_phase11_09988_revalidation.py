import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
VERIFICATION_DIR = ROOT / "08_scripts" / "verification"
for path in (LIB_DIR, VERIFICATION_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from validate_phase11_peer_historical_repaired_candidate import bear_case_update, validation_blockers, valuation_summary


class Phase1109988RevalidationTests(unittest.TestCase):
    def test_valuation_summary_contains_phase11_before_after_fields(self):
        summary = valuation_summary(
            {
                "allowed_usage": "supporting_evidence",
                "valuation_status": "input_hardened",
                "peer_comparison": {
                    "peer_set_id": "hk_internet_platforms",
                    "peer_set_status": "available",
                    "peer_count_available": 2,
                    "peer_count_required": 2,
                    "peer_comparison_status": "supporting",
                },
                "historical_valuation": {"status": "available", "metrics": {"pb": {"status": "available"}}},
                "forward_eps": {"status": "proxy"},
            }
        )

        self.assertEqual(summary["peer_set_id"], "hk_internet_platforms")
        self.assertEqual(summary["historical_available_metrics"], ["pb"])
        self.assertEqual(summary["forward_eps_status"], "proxy")

    def test_bear_case_update_moves_valuation_claim_to_partial(self):
        update = bear_case_update(
            "09988.HK",
            {"allowed_usage": "supporting_evidence"},
            {
                "allowed_usage": "supporting_evidence",
                "peer_comparison": {"peer_comparison_status": "supporting"},
                "historical_valuation": {"status": "available"},
            },
        )

        self.assertEqual(update["before"], "unresolved")
        self.assertEqual(update["after"], "partially_mitigated")

    def test_validation_blockers_keep_partial_bear_case_from_pending(self):
        blockers = validation_blockers(
            {"blocking_factors": [], "promotion_allowed": False},
            {"valuation_confidence": 0.7, "current_price": 1.0},
            {"sub_blockers": []},
            {"after": "pass", "remaining_root_causes": []},
            {"after": "partially_mitigated"},
        )

        self.assertIn("HIGH_BEAR_CASE_PARTIALLY_MITIGATED", blockers)


if __name__ == "__main__":
    unittest.main()
