import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
for rel in [("08_scripts", "lib"), ("08_scripts", "verification")]:
    path = ROOT.joinpath(*rel)
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import validate_phase19_recovered_fundamentals_promotion_impact as validator


class Phase19RecoveredFundamentalsImpactTests(unittest.TestCase):
    def test_impact_reports_why_not_pending(self):
        with patch.object(
            validator,
            "build_ticker_block_diagnostics",
            return_value={
                "ticker": "00700.HK",
                "status": "candidate_shadow",
                "recovered_fields": ["shareholders_equity"],
                "core_blockers": [],
                "why_not_pending": "bear case residual risk remains",
                "primary_blocking_gate": "BEAR_CASE_GATE",
                "next_fix": ["strengthen bear case response"],
            },
        ), patch.object(
            validator,
            "latest_phase18_validation",
            return_value={"ticker_results": [{"ticker": "00700.HK", "core_blockers_before": ["shareholders_equity"], "core_blockers_after": []}]},
        ), patch.object(validator, "register_snapshot"):
            payload = validator.build_payload(None, ["00700.HK"])

        self.assertEqual(payload["summary"]["core_blockers_after"], 0)
        self.assertEqual(payload["summary"]["new_pending_created"], 0)
        self.assertEqual(payload["ticker_results"][0]["primary_blocking_gate"], "BEAR_CASE_GATE")
        self.assertIn("bear case", payload["ticker_results"][0]["why_not_pending"])


if __name__ == "__main__":
    unittest.main()
