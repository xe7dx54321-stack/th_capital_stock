import sqlite3
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
VERIFICATION_DIR = ROOT / "08_scripts" / "verification"
for path in (LIB_DIR, VERIFICATION_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from validate_phase24_tender_procurement_revalidation import build_payload


class Phase24TenderRevalidationTests(unittest.TestCase):
    def test_revalidation_reports_before_after_without_pending(self):
        tender = {"evidence_candidates": [{"evidence_id": "ev_tender_1", "evidence_strength": "strong_indication", "usable_for_proxy_signal": True}], "normalized_results": []}
        with patch("validate_phase24_tender_procurement_revalidation.build_cn_tender_procurement_payload", return_value=tender), patch(
            "validate_phase24_tender_procurement_revalidation.build_ticker_block_diagnostics",
            return_value={"status": "candidate_shadow", "primary_blocking_gate": "VALUATION_GATE"},
        ), patch(
            "validate_phase24_tender_procurement_revalidation.build_ticker_proxy_strengthening",
            return_value={"proxy_strengthening": {"after": {"status": "medium"}}},
        ), patch(
            "validate_phase24_tender_procurement_revalidation.build_ticker_bear_case_mitigation",
            return_value={"bear_case_mitigation": {"overall_status": "partially_mitigated"}},
        ):
            payload = build_payload(sqlite3.connect(":memory:"), ["688041.SH"])
        self.assertEqual(payload["summary"]["proxy_gate_improved"], 1)
        self.assertEqual(payload["summary"]["new_pending_created"], 0)
        self.assertFalse(payload["safety"]["promotion_rules_relaxed"])


if __name__ == "__main__":
    unittest.main()
