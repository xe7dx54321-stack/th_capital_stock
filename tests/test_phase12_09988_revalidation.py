import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFICATION_DIR = ROOT / "08_scripts" / "verification"
if str(VERIFICATION_DIR) not in sys.path:
    sys.path.insert(0, str(VERIFICATION_DIR))

from validate_phase12_evidence_quality_repaired_candidate import _field_quality_delta, validation_blockers


class Phase1209988RevalidationTests(unittest.TestCase):
    def test_field_quality_delta_reports_promoted_fields(self):
        delta = _field_quality_delta(
            {
                "before_field_quality": {"shareholders_equity": {"allowed_usage": "context_only"}},
                "after_field_quality": {
                    "shareholders_equity": {"allowed_usage": "supporting_evidence", "source_evidence_id": "ev_eq"},
                    "capex": {"allowed_usage": "blocked"},
                },
                "improvement_summary": {"fields_with_source_evidence_after": 1},
            }
        )

        self.assertIn("shareholders_equity", delta["fields_promoted_to_supporting"])
        self.assertIn("capex", delta["fields_blocked"])

    def test_validation_keeps_partial_bear_case_blocker(self):
        blockers = validation_blockers(
            {"blocking_factors": []},
            {"allowed_usage": "supporting_evidence"},
            {"sub_blockers": []},
            {"remaining_root_causes": ["FIELD_NOT_FOUND:capex"]},
            {"after": "partially_mitigated"},
        )

        self.assertIn("DATA_QUALITY_RISK", blockers)
        self.assertIn("FIELD_NOT_FOUND", blockers)
        self.assertIn("HIGH_BEAR_CASE_PARTIALLY_MITIGATED", blockers)


if __name__ == "__main__":
    unittest.main()

