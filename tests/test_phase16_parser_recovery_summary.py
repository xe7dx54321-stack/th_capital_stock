import sqlite3
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
VERIFICATION_DIR = ROOT / "08_scripts" / "verification"
JOBS_DIR = ROOT / "08_scripts" / "jobs"
for path in (LIB_DIR, REPORTING_DIR, VERIFICATION_DIR, JOBS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import build_phase16_parser_recovery_summary as summary


class Phase16ParserRecoverySummaryTests(unittest.TestCase):
    def test_summary_outputs_hkex_cninfo_and_unknown_sections(self):
        fake_payload = {
            "generated_at": "now",
            "summary": {"core_blockers_resolved": 1, "core_blockers_refined": 1, "core_blockers_remaining": 2, "unknown_thesis_improved": 1, "new_pending_created": 0},
            "targets": [
                {
                    "ticker": "00700.HK",
                    "target_type": "hkex_balance_sheet_recovery",
                    "remaining_blockers": [],
                    "field_repair": {"shareholders_equity": {"status": "extracted", "confidence": 0.78}},
                },
                {
                    "ticker": "300308.SZ",
                    "target_type": "cninfo_income_statement_recovery",
                    "fields_repaired": ["revenue"],
                    "fields_refined": ["gross_profit"],
                    "remaining_blockers": ["gross_profit"],
                    "field_repair": {"gross_profit": {"suggested_fix": "extend CNINFO parser"}},
                },
                {
                    "ticker": "002230.SZ",
                    "target_type": "unknown_thesis_recovery",
                    "before_thesis": "unknown",
                    "after_thesis": "ai_infrastructure_demand",
                    "confidence_after": 0.58,
                    "allow_pending": False,
                },
            ],
        }
        with patch.object(summary, "build_payload", return_value=fake_payload):
            payload = summary.build_summary_payload(sqlite3.connect(":memory:"))
        self.assertEqual(payload["summary"]["hkex_targets"], ["00700.HK"])
        self.assertEqual(payload["cninfo_recovery"][0]["fields_repaired"], ["revenue"])
        self.assertEqual(payload["unknown_thesis"][0]["candidate_thesis"], "ai_infrastructure_demand")
        self.assertIn("HKEX Recovery", summary.markdown(payload))


if __name__ == "__main__":
    unittest.main()
