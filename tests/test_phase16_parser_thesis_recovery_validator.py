import sqlite3
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
VERIFICATION_DIR = ROOT / "08_scripts" / "verification"
JOBS_DIR = ROOT / "08_scripts" / "jobs"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
for path in (LIB_DIR, VERIFICATION_DIR, JOBS_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import validate_phase16_parser_thesis_recovery as validator


class Phase16ParserThesisRecoveryValidatorTests(unittest.TestCase):
    def test_validator_outputs_before_after_and_no_pending(self):
        conn = sqlite3.connect(":memory:")

        def fake_recovery(_conn, ticker):
            if ticker == "00700.HK":
                return {
                    "core_blockers_before": ["shareholders_equity"],
                    "core_blockers_after": [],
                    "field_repair": {"shareholders_equity": {"status": "extracted", "source_evidence_id": "ev_hk"}},
                }
            return {
                "core_blockers_before": ["revenue", "gross_profit"],
                "core_blockers_after": ["gross_profit"],
                "field_repair": {
                    "revenue": {"status": "extracted", "source_evidence_id": "ev_cn"},
                    "gross_profit": {"status": "missing", "missing_reason": "derived_field_missing_inputs"},
                },
            }

        with patch.object(validator, "build_recovery_payload", side_effect=fake_recovery), patch.object(
            validator,
            "build_ticker_payload",
            return_value={
                "current_thesis_type": "unknown",
                "inference_confidence": 0.29,
                "after_patch_simulation": {"candidate_thesis_type": "ai_infrastructure_demand", "simulated_confidence": 0.58, "reason": "metadata patch improves thesis inference but evidence gate still required"},
                "unknown_reasons": ["weak_watchlist_metadata"],
                "suggested_metadata_patch": {"theme_tags": ["ai_infrastructure"]},
            },
        ), patch.object(validator, "build_patch_result", return_value={"mode": "dry_run", "changed": False}):
            payload = validator.build_payload(conn, ["00700.HK", "300308.SZ", "002230.SZ"])

        self.assertEqual(payload["overall_status"], "partial_pass")
        self.assertEqual(payload["summary"]["core_blockers_resolved"], 2)
        self.assertEqual(payload["summary"]["unknown_thesis_improved"], 1)
        self.assertEqual(payload["summary"]["new_pending_created"], 0)


if __name__ == "__main__":
    unittest.main()
