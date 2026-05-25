import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_hkex_table_parser import detect_balance_sheet_section, extract_shareholders_equity_from_text


class Phase16HkexBalanceSheetParserTests(unittest.TestCase):
    def test_detects_english_traditional_and_simplified_titles(self):
        for title in [
            "Consolidated Statement of Financial Position",
            "綜合財務狀況表",
            "资产负债表",
        ]:
            self.assertTrue(detect_balance_sheet_section(title)["table_detected"])

    def test_owners_equity_preferred_over_total_equity(self):
        text = """
        Consolidated Statement of Financial Position
        RMB million
        Total equity 900
        Equity attributable to owners of the Company 800
        Non-controlling interests 100
        """
        result = extract_shareholders_equity_from_text(text, source_evidence_id="ev_hk", source_chunk_id="chunk_hk")
        self.assertEqual(result["status"], "extracted")
        self.assertEqual(result["value"], 800_000_000.0)
        self.assertFalse(result["fallback_used"])
        self.assertEqual(result["allowed_usage"], "supporting_evidence")

    def test_total_equity_and_net_assets_are_fallbacks(self):
        result = extract_shareholders_equity_from_text(
            "綜合資產負債表\n港幣百萬元\n淨資產 700",
            source_evidence_id="ev_hk",
        )
        self.assertEqual(result["status"], "extracted")
        self.assertTrue(result["fallback_used"])
        self.assertLess(result["confidence"], 0.7)

    def test_non_controlling_interests_not_misidentified(self):
        result = extract_shareholders_equity_from_text(
            "Balance Sheet\nHKD million\nNon-controlling interests 99",
            source_evidence_id="ev_hk",
        )
        self.assertEqual(result["status"], "missing")
        self.assertEqual(result["missing_reason"], "equity_field_not_found")

    def test_ambiguous_fallback_is_blocked(self):
        result = extract_shareholders_equity_from_text(
            "Balance Sheet\nHKD million\nTotal equity 900\nNet assets 880",
            source_evidence_id="ev_hk",
        )
        self.assertEqual(result["status"], "missing")
        self.assertEqual(result["missing_reason"], "ambiguous_equity_field")
        self.assertEqual(result["allowed_usage"], "blocked")


if __name__ == "__main__":
    unittest.main()
